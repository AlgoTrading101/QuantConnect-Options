# region imports
from AlgorithmImports import *
from datetime import timedelta

# endregion


class HedgeSoldOptionAlgorithm(QCAlgorithm):
    def Initialize(self):
        self.SetStartDate(2020, 1, 1)
        self.SetEndDate(2020, 1, 31)
        self.SetCash(100000)

        # Add the underlying equity
        self.equity = self.AddEquity("SPY", Resolution.Minute).Symbol

        # Add options and set a filter
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
                # Sell an out-of-the-money call option
                if (
                    contract.Right == OptionRight.Call
                    and contract.Strike > self.Securities[self.equity].Price
                ):
                    if not self.Portfolio[contract.Symbol].Invested:
                        self.Sell(contract.Symbol, 1)
                        self.Debug("Sold option: " + str(contract.Symbol))

                        # Hedge the sold option by buying the underlying based on its delta
                        if contract.Greeks is not None:
                            # Standard option multiplier is 100 shares
                            hedgeQuantity = int(round(contract.Greeks.Delta * 100))
                            if hedgeQuantity != 0:
                                self.MarketOrder(self.equity, hedgeQuantity)
                                self.Debug(
                                    "Hedged option with {} shares of underlying.".format(
                                        hedgeQuantity
                                    )
                                )
                        break
