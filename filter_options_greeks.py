# region imports
from AlgorithmImports import *
from datetime import timedelta

# endregion


class GreeksFilterAlgorithm(QCAlgorithm):
    def Initialize(self):
        self.SetStartDate(2020, 1, 1)
        self.SetEndDate(2020, 1, 31)
        self.SetCash(100000)

        # Add the underlying equity
        self.equity = self.AddEquity("SPY", Resolution.Minute).Symbol

        # Add options and set a broad filter
        option = self.AddOption("SPY", Resolution.Minute)
        option.SetFilter(
            lambda universe: universe.IncludeWeeklys()
            .Strikes(-10, 10)
            .Expiration(timedelta(0), timedelta(60))
        )
        self.optionSymbol = option.Symbol

    def OnData(self, data):
        if self.optionSymbol in data.OptionChains:
            chain = data.OptionChains[self.optionSymbol]
            for contract in chain:
                # Check if Greeks data is available
                if contract.Greeks is not None:
                    delta = abs(contract.Greeks.Delta)
                    if 0.2 <= delta <= 0.5:
                        self.Debug(
                            "Selected option by Greeks (Delta: {:.2f}): {}".format(
                                delta, contract.Symbol
                            )
                        )
                        break
