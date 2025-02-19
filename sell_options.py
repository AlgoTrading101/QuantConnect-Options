# region imports
from AlgorithmImports import *
from datetime import timedelta
# endregion

class SellOptionAlgorithm(QCAlgorithm):
    def Initialize(self):
        self.SetStartDate(2020, 1, 1)
        self.SetEndDate(2020, 1, 31)
        self.SetCash(100000)
        
        # Add the underlying equity
        self.equity = self.AddEquity("SPY", Resolution.Minute).Symbol
        
        # Add options for the underlying and set a basic filter
        option = self.AddOption("SPY", Resolution.Minute)
        option.SetFilter(lambda universe: universe.IncludeWeeklys()
                         .Strikes(-2, 2)
                         .Expiration(timedelta(0), timedelta(30)))
        self.optionSymbol = option.Symbol

    def OnData(self, data):
        if self.optionSymbol in data.OptionChains:
            chain = data.OptionChains[self.optionSymbol]
            # Sell the first out-of-the-money call option we find
            for contract in chain:
                if contract.Right == OptionRight.Call and contract.Strike > self.Securities[self.equity].Price:
                    if not self.Portfolio[contract.Symbol].Invested:
                        self.Sell(contract.Symbol, 1)
                        self.Debug("Sold option: " + str(contract.Symbol))
                        break