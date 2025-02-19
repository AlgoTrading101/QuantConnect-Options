# region imports
from AlgorithmImports import *
from datetime import timedelta

# endregion


class ExpiryFilterAlgorithm(QCAlgorithm):
    def Initialize(self):
        self.SetStartDate(2020, 1, 1)
        self.SetEndDate(2020, 1, 31)
        self.SetCash(100000)

        # Add the underlying equity
        self.equity = self.AddEquity("SPY", Resolution.Minute).Symbol

        # Add options and set an expiry filter
        option = self.AddOption("SPY", Resolution.Minute)
        option.SetFilter(
            lambda universe: universe.IncludeWeeklys()
            .Strikes(-5, 5)
            .Expiration(timedelta(0), timedelta(30))
        )
        self.optionSymbol = option.Symbol

    def OnData(self, data):
        if self.optionSymbol in data.OptionChains:
            chain = data.OptionChains[self.optionSymbol]
            for contract in chain:
                daysToExpiry = (contract.Expiry - self.Time).days
                if 0 < daysToExpiry <= 30:
                    self.Debug(
                        "Selected option by expiry ("
                        + str(daysToExpiry)
                        + " days): "
                        + str(contract.Symbol)
                    )
                    break
