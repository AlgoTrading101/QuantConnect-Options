# region imports
from AlgorithmImports import *
from datetime import timedelta
# endregion

class DynamicLimitOrderAlgorithm(QCAlgorithm):
    def Initialize(self):
        self.SetStartDate(2020, 1, 1)
        self.SetEndDate(2020, 1, 15)
        self.SetCash(100000)
        
        # Add the underlying equity
        self.equity = self.AddEquity("SPY", Resolution.Minute).Symbol
        
        # Variables to track the limit order and threshold
        self.limitOrderTicket = None
        self.orderQuantity = 100
        self.priceThreshold = 0.10  # Update if price changes by more than $0.10

    def OnData(self, data):
        security = self.Securities[self.equity]
        askPrice = security.AskPrice
        if askPrice == 0:
            return

        if self.limitOrderTicket is None:
            # Place the initial limit order at the current ask price
            self.limitOrderTicket = self.LimitOrder(self.equity, self.orderQuantity, askPrice)
            self.Debug("Placed limit order at ask price: {:.2f}".format(askPrice))
        else:
            # Access the original limit price from the order ticket's OrderRequests
            ticketPrice = self.limitOrderTicket.OrderRequests[0].LimitPrice
            # If the ask price has moved by more than the threshold, update the order
            if abs(ticketPrice - askPrice) > self.priceThreshold:
                self.Transactions.CancelOrder(self.limitOrderTicket.OrderId)
                self.limitOrderTicket = self.LimitOrder(self.equity, self.orderQuantity, askPrice)
                self.Debug("Updated limit order to new ask price: {:.2f}".format(askPrice))