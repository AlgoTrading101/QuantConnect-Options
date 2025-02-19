# region imports
from QuantConnect import *
from datetime import timedelta
from QuantConnect.Data import Slice
from QuantConnect.Algorithm import QCAlgorithm

# endregion


class AutomaticImpliedVolatilityIndicatorAlgorithm(QCAlgorithm):

    def initialize(self) -> None:
        self.set_start_date(2024, 1, 1)
        self.set_end_date(2024, 2, 1)
        # Subscribe to the underlying equity.
        self._underlying = self.add_equity(
            "SPY", data_normalization_mode=DataNormalizationMode.RAW
        ).symbol

        # Schedule an event before market open to select options and attach IV indicators.
        self.schedule.on(
            self.date_rules.every_day(self._underlying),
            self.time_rules.at(9, 0),
            self._update_contracts_and_indicators,
        )

        self._options = None

    def _update_contracts_and_indicators(self) -> None:
        if self._underlying is None:
            return

        # Get the option chain as a DataFrame.
        chain = self.option_chain(self._underlying, flatten=True).data_frame
        if chain.empty:
            return

        # Filter for options with >1 month until expiry and at-the-money (ATM).
        chain = chain[chain.expiry > self.time + timedelta(days=30)]
        expiry = chain.expiry.min()
        chain = chain[chain.expiry == expiry]
        chain.loc[:, "abs_strike_delta"] = abs(
            chain["strike"] - chain["underlyinglastprice"]
        )
        abs_strike_delta = chain["abs_strike_delta"].min()
        chain = chain[chain["abs_strike_delta"] == abs_strike_delta]

        # Group contracts into call/put pairs.
        contracts_pair_sizes = chain.groupby(["expiry", "strike"]).count()["right"]
        paired_contracts = contracts_pair_sizes[contracts_pair_sizes == 2].index
        if len(paired_contracts) == 0:
            return

        expiries = [x[0] for x in paired_contracts]
        strikes = [x[1] for x in paired_contracts]
        symbols = [
            idx[-1]
            for idx in chain[
                chain["expiry"].isin(expiries) & chain["strike"].isin(strikes)
            ]
            .reset_index()
            .groupby(["expiry", "strike", "right", "symbol"])
            .first()
            .index
        ]
        pairs = [(symbols[i], symbols[i + 1]) for i in range(0, len(symbols), 2)]
        if len(pairs) == 0:
            return

        # Use the first call/put pair found.
        call, put = pairs[0]
        contractCall = self.add_option_contract(call)
        contractPut = self.add_option_contract(put)

        # Attach automatic IV indicators.
        contractCall.iv = self.iv(call, put)
        contractPut.iv = self.iv(put, call)
        self._options = (call, put)

    def on_data(self, slice: Slice) -> None:
        if self._options:
            call, put = self._options
            if call in self.securities and put in self.securities:
                optionCall = self.securities[call]
                optionPut = self.securities[put]

                # Only log when both IV indicators are ready.
                if optionCall.iv.is_ready and optionPut.iv.is_ready:
                    iv_call = optionCall.iv.current.value
                    iv_put = optionPut.iv.current.value

                    # Compute IV Rank from the indicator's rolling window.
                    def iv_rank(indicator):
                        if not indicator.window or indicator.window.count == 0:
                            return 0
                        values = [dp.value for dp in indicator.window]
                        mn = min(values)
                        mx = max(values)
                        return (
                            0
                            if mx == mn
                            else (indicator.current.value - mn) / (mx - mn)
                        )

                    rank_call = iv_rank(optionCall.iv)
                    rank_put = iv_rank(optionPut.iv)

                    self.Debug(f"Call IV: {iv_call:.2f}, Call IV Rank: {rank_call:.2f}")
                    self.Debug(f"Put IV:  {iv_put:.2f}, Put IV Rank:  {rank_put:.2f}")
