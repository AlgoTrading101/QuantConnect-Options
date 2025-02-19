# region imports
from AlgorithmImports import *
from datetime import timedelta

# endregion


class StrikeFilterAlgorithm(QCAlgorithm):
    def Initialize(self):
        self.SetStartDate(2020, 1, 1)
        self.SetEndDate(2020, 1, 31)
        self.SetCash(100000)

        # Add the underlying equity
        self.equity = self.AddEquity("SPY", Resolution.Minute).Symbol

        # Add options and set a filter
        option = self.AddOption("SPY", Resolution.Minute)
        option.SetFilter(self.StrikeFilter)
        self.optionSymbol = option.Symbol

    def StrikeFilter(self, universe):
        # Filter options with strikes in a broad range (later refined in OnData)
        return (
            universe.IncludeWeeklys()
            .Strikes(-10, +10)
            .Expiration(timedelta(0), timedelta(30))
        )

    def OnData(self, data):
        if self.optionSymbol in data.OptionChains:
            chain = data.OptionChains[self.optionSymbol]
            underlyingPrice = self.Securities[self.equity].Price
            for contract in chain:
                # Only select options with strike within 5% of the underlying price
                if abs(contract.Strike - underlyingPrice) / underlyingPrice < 0.05:
                    self.Debug("Selected option by strike: " + str(contract.Symbol))
                    # For demo purposes, exit after the first match
                    break
