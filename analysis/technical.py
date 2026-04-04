"""
Technical Analysis Engine
Calculates all key indicators and generates signals.
Uses the `ta` library (compatible with latest Python/pandas).
"""
import pandas as pd
import numpy as np
import os
import sys

from ta.momentum import RSIIndicator, StochRSIIndicator
from ta.trend import MACD, EMAIndicator, ADXIndicator
from ta.volatility import BollingerBands, AverageTrueRange
from ta.volume import VolumeWeightedAveragePrice

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import TA_CONFIG


class TechnicalAnalyzer:
    """Runs full technical analysis on stock data."""

    def __init__(self):
        self.config = TA_CONFIG

    def analyze(self, df, symbol=""):
        """Run complete technical analysis on a DataFrame."""
        if df is None or len(df) < 50:
            return None

        result = {
            "symbol": symbol,
            "indicators": self._calculate_indicators(df),
            "signals": {},
            "pattern": self._detect_patterns(df),
            "support_resistance": self._find_support_resistance(df),
            "trend": self._determine_trend(df),
        }
        result["signals"] = self._generate_signals(result["indicators"], df)
        result["overall_signal"] = self._aggregate_signals(result["signals"])
        result["summary"] = self._create_summary(result)
        return result

    def _calculate_indicators(self, df):
        """Calculate all technical indicators."""
        close = df["Close"]
        high = df["High"]
        low = df["Low"]
        volume = df["Volume"]

        indicators = {}

        # RSI
        try:
            rsi_ind = RSIIndicator(close=close, window=self.config["rsi_period"])
            rsi_val = rsi_ind.rsi().iloc[-1]
            indicators["rsi"] = round(rsi_val, 2) if not pd.isna(rsi_val) else None
        except Exception:
            indicators["rsi"] = None

        # MACD
        try:
            macd_ind = MACD(close=close,
                           window_fast=self.config["macd_fast"],
                           window_slow=self.config["macd_slow"],
                           window_sign=self.config["macd_signal"])
            macd_val = macd_ind.macd().iloc[-1]
            macd_sig = macd_ind.macd_signal().iloc[-1]
            macd_hist = macd_ind.macd_diff().iloc[-1]
            indicators["macd"] = round(macd_val, 2) if not pd.isna(macd_val) else None
            indicators["macd_signal"] = round(macd_sig, 2) if not pd.isna(macd_sig) else None
            indicators["macd_histogram"] = round(macd_hist, 2) if not pd.isna(macd_hist) else None
        except Exception:
            indicators["macd"] = indicators["macd_signal"] = indicators["macd_histogram"] = None

        # Bollinger Bands
        try:
            bb = BollingerBands(close=close, window=self.config["bb_period"], window_dev=self.config["bb_std"])
            indicators["bb_upper"] = round(bb.bollinger_hband().iloc[-1], 2)
            indicators["bb_middle"] = round(bb.bollinger_mavg().iloc[-1], 2)
            indicators["bb_lower"] = round(bb.bollinger_lband().iloc[-1], 2)
            pct_b = bb.bollinger_pband().iloc[-1]
            indicators["bb_pct_b"] = round(pct_b, 2) if not pd.isna(pct_b) else 0.5
        except Exception:
            pass

        # EMAs
        for period_name, config_key in [("short", "ema_short"), ("medium", "ema_medium"),
                                         ("long", "ema_long"), ("trend", "ema_trend")]:
            try:
                ema = EMAIndicator(close=close, window=self.config[config_key])
                val = ema.ema_indicator().iloc[-1]
                indicators[f"ema_{period_name}"] = round(val, 2) if not pd.isna(val) else None
            except Exception:
                indicators[f"ema_{period_name}"] = None

        # Supertrend (manual calculation since ta lib doesn't have it)
        try:
            period = self.config["supertrend_period"]
            multiplier = self.config["supertrend_multiplier"]
            atr_ind = AverageTrueRange(high=high, low=low, close=close, window=period)
            atr_vals = atr_ind.average_true_range()

            hl2 = (high + low) / 2
            upper_band = hl2 + (multiplier * atr_vals)
            lower_band = hl2 - (multiplier * atr_vals)

            supertrend = pd.Series(index=df.index, dtype=float)
            direction = pd.Series(index=df.index, dtype=int)

            supertrend.iloc[0] = upper_band.iloc[0]
            direction.iloc[0] = -1

            for i in range(1, len(df)):
                if close.iloc[i] > upper_band.iloc[i - 1]:
                    direction.iloc[i] = 1
                elif close.iloc[i] < lower_band.iloc[i - 1]:
                    direction.iloc[i] = -1
                else:
                    direction.iloc[i] = direction.iloc[i - 1]

                if direction.iloc[i] == 1:
                    supertrend.iloc[i] = lower_band.iloc[i]
                else:
                    supertrend.iloc[i] = upper_band.iloc[i]

            indicators["supertrend"] = round(supertrend.iloc[-1], 2)
            indicators["supertrend_direction"] = int(direction.iloc[-1])
        except Exception:
            indicators["supertrend"] = None
            indicators["supertrend_direction"] = None

        # VWAP
        try:
            typical_price = (high + low + close) / 3
            vwap = (typical_price * volume).cumsum() / volume.cumsum()
            indicators["vwap"] = round(vwap.iloc[-1], 2) if not vwap.empty else None
        except Exception:
            indicators["vwap"] = None

        # ADX
        try:
            adx_ind = ADXIndicator(high=high, low=low, close=close, window=14)
            adx_val = adx_ind.adx().iloc[-1]
            indicators["adx"] = round(adx_val, 2) if not pd.isna(adx_val) else None
        except Exception:
            indicators["adx"] = None

        # Volume analysis
        try:
            avg_vol_20 = volume.rolling(20).mean().iloc[-1]
            indicators["volume_current"] = int(volume.iloc[-1])
            indicators["volume_avg_20"] = int(avg_vol_20) if not pd.isna(avg_vol_20) else 0
            indicators["volume_ratio"] = round(volume.iloc[-1] / avg_vol_20, 2) if avg_vol_20 > 0 else 1.0
        except Exception:
            indicators["volume_ratio"] = 1.0

        # ATR
        try:
            atr_ind = AverageTrueRange(high=high, low=low, close=close, window=14)
            atr_val = atr_ind.average_true_range().iloc[-1]
            indicators["atr"] = round(atr_val, 2) if not pd.isna(atr_val) else None
            indicators["atr_pct"] = round((atr_val / close.iloc[-1]) * 100, 2) if atr_val and close.iloc[-1] else None
        except Exception:
            indicators["atr"] = None

        # Current price
        indicators["price"] = round(close.iloc[-1], 2)
        indicators["prev_close"] = round(close.iloc[-2], 2) if len(close) >= 2 else None
        indicators["change_pct"] = round(((close.iloc[-1] - close.iloc[-2]) / close.iloc[-2]) * 100, 2) if len(close) >= 2 else 0

        return indicators

    def _generate_signals(self, indicators, df):
        """Generate buy/sell/hold signals from indicators."""
        signals = {}

        # RSI Signal
        rsi = indicators.get("rsi")
        if rsi is not None:
            if rsi < self.config["rsi_oversold"]:
                signals["rsi"] = {"signal": "BUY", "strength": min((self.config["rsi_oversold"] - rsi) / 10, 1.0),
                                  "reason": f"RSI oversold at {rsi}"}
            elif rsi > self.config["rsi_overbought"]:
                signals["rsi"] = {"signal": "SELL", "strength": min((rsi - self.config["rsi_overbought"]) / 10, 1.0),
                                  "reason": f"RSI overbought at {rsi}"}
            else:
                signals["rsi"] = {"signal": "HOLD", "strength": 0, "reason": f"RSI neutral at {rsi}"}

        # MACD Signal
        macd = indicators.get("macd")
        macd_sig = indicators.get("macd_signal")
        hist = indicators.get("macd_histogram")
        if macd is not None and macd_sig is not None:
            if macd > macd_sig and hist and hist > 0:
                signals["macd"] = {"signal": "BUY", "strength": min(abs(hist) / 5, 1.0),
                                   "reason": "MACD bullish crossover"}
            elif macd < macd_sig and hist and hist < 0:
                signals["macd"] = {"signal": "SELL", "strength": min(abs(hist) / 5, 1.0),
                                   "reason": "MACD bearish crossover"}
            else:
                signals["macd"] = {"signal": "HOLD", "strength": 0, "reason": "MACD neutral"}

        # Bollinger Band Signal
        bb_pct = indicators.get("bb_pct_b")
        if bb_pct is not None:
            if bb_pct < 0.05:
                signals["bollinger"] = {"signal": "BUY", "strength": 0.8,
                                        "reason": "Price near lower Bollinger Band"}
            elif bb_pct > 0.95:
                signals["bollinger"] = {"signal": "SELL", "strength": 0.8,
                                        "reason": "Price near upper Bollinger Band"}
            else:
                signals["bollinger"] = {"signal": "HOLD", "strength": 0, "reason": "Price within Bollinger Bands"}

        # EMA Crossover Signal
        ema_s = indicators.get("ema_short")
        ema_m = indicators.get("ema_medium")
        ema_l = indicators.get("ema_long")
        price = indicators.get("price")
        if ema_s and ema_m and ema_l and price:
            if ema_s > ema_m > ema_l and price > ema_s:
                signals["ema"] = {"signal": "BUY", "strength": 0.9,
                                  "reason": "Strong uptrend: EMA 9 > 21 > 50, price above all"}
            elif ema_s < ema_m < ema_l and price < ema_s:
                signals["ema"] = {"signal": "SELL", "strength": 0.9,
                                  "reason": "Strong downtrend: EMA 9 < 21 < 50, price below all"}
            elif ema_s > ema_m:
                signals["ema"] = {"signal": "BUY", "strength": 0.5,
                                  "reason": "Short-term bullish: EMA 9 > 21"}
            else:
                signals["ema"] = {"signal": "HOLD", "strength": 0, "reason": "EMAs mixed"}

        # Supertrend Signal
        st_dir = indicators.get("supertrend_direction")
        if st_dir is not None:
            if st_dir == 1:
                signals["supertrend"] = {"signal": "BUY", "strength": 0.7, "reason": "Supertrend bullish"}
            else:
                signals["supertrend"] = {"signal": "SELL", "strength": 0.7, "reason": "Supertrend bearish"}

        # Volume Confirmation
        vol_ratio = indicators.get("volume_ratio", 1.0)
        if vol_ratio > 1.5:
            signals["volume"] = {"signal": "CONFIRM", "strength": min(vol_ratio / 3, 1.0),
                                 "reason": f"Volume {vol_ratio:.1f}x above average"}
        elif vol_ratio < 0.5:
            signals["volume"] = {"signal": "WEAK", "strength": 0.3,
                                 "reason": f"Low volume ({vol_ratio:.1f}x avg)"}
        else:
            signals["volume"] = {"signal": "NEUTRAL", "strength": 0, "reason": "Normal volume"}

        return signals

    def _aggregate_signals(self, signals):
        """Combine all signals into one overall recommendation."""
        buy_score = 0
        sell_score = 0
        total_weight = 0

        weights = {"rsi": 1.0, "macd": 1.2, "bollinger": 0.8, "ema": 1.5, "supertrend": 1.3, "volume": 0.5}

        for name, sig in signals.items():
            w = weights.get(name, 1.0)
            if sig["signal"] == "BUY":
                buy_score += sig["strength"] * w
            elif sig["signal"] == "SELL":
                sell_score += sig["strength"] * w
            total_weight += w

        if total_weight == 0:
            return {"signal": "HOLD", "confidence": 0, "reason": "Insufficient data"}

        net = (buy_score - sell_score) / total_weight
        if net > 0.3:
            signal = "STRONG BUY" if net > 0.6 else "BUY"
        elif net < -0.3:
            signal = "STRONG SELL" if net < -0.6 else "SELL"
        else:
            signal = "HOLD"

        confidence = min(abs(net) * 100, 100)
        reasons = [sig["reason"] for sig in signals.values() if sig["signal"] in ("BUY", "SELL", "CONFIRM") and sig["strength"] > 0.3]

        return {
            "signal": signal,
            "confidence": round(confidence, 1),
            "buy_score": round(buy_score, 2),
            "sell_score": round(sell_score, 2),
            "reasons": reasons[:3],
        }

    def _detect_patterns(self, df):
        """Detect candlestick patterns."""
        patterns_found = []
        if len(df) < 3:
            return patterns_found

        o, h, l, c = df["Open"].iloc[-1], df["High"].iloc[-1], df["Low"].iloc[-1], df["Close"].iloc[-1]
        po, ph, pl, pc = df["Open"].iloc[-2], df["High"].iloc[-2], df["Low"].iloc[-2], df["Close"].iloc[-2]
        body = abs(c - o)
        prev_body = abs(pc - po)
        upper_wick = h - max(o, c)
        lower_wick = min(o, c) - l
        total_range = h - l

        if total_range > 0 and body / total_range < 0.1:
            patterns_found.append({"name": "Doji", "type": "neutral", "desc": "Indecision"})
        if total_range > 0 and lower_wick > 2 * body and upper_wick < body * 0.5 and c > o:
            patterns_found.append({"name": "Hammer", "type": "bullish", "desc": "Potential bottom reversal"})
        if total_range > 0 and upper_wick > 2 * body and lower_wick < body * 0.5 and c < o:
            patterns_found.append({"name": "Shooting Star", "type": "bearish", "desc": "Potential top reversal"})
        if pc > po and c > o and c > ph and o < pl and body > prev_body:
            patterns_found.append({"name": "Bullish Engulfing", "type": "bullish", "desc": "Strong buying"})
        if pc < po and c < o and c < pl and o > ph and body > prev_body:
            patterns_found.append({"name": "Bearish Engulfing", "type": "bearish", "desc": "Strong selling"})
        if o > ph:
            patterns_found.append({"name": "Gap Up", "type": "bullish", "desc": "Opened above yesterday's high"})
        if o < pl:
            patterns_found.append({"name": "Gap Down", "type": "bearish", "desc": "Opened below yesterday's low"})

        return patterns_found

    def _find_support_resistance(self, df, window=20):
        if len(df) < window:
            return {"support": [], "resistance": []}

        close = df["Close"].values
        high = df["High"].values
        low = df["Low"].values
        current_price = close[-1]

        supports = []
        resistances = []
        for i in range(window, len(df) - 1):
            if low[i] == min(low[i-window:i+1]):
                supports.append(round(float(low[i]), 2))
            if high[i] == max(high[i-window:i+1]):
                resistances.append(round(float(high[i]), 2))

        supports = sorted(set([s for s in supports if s < current_price]), reverse=True)[:3]
        resistances = sorted(set([r for r in resistances if r > current_price]))[:3]
        return {"support": supports, "resistance": resistances}

    def _determine_trend(self, df):
        if len(df) < 50:
            return {"short": "unknown", "medium": "unknown", "long": "unknown"}

        close = df["Close"]
        price = close.iloc[-1]

        def get_trend(window):
            try:
                ema = EMAIndicator(close=close, window=window).ema_indicator().iloc[-1]
                return "bullish" if price > ema else "bearish"
            except Exception:
                return "unknown"

        return {"short": get_trend(9), "medium": get_trend(21), "long": get_trend(50)}

    def _create_summary(self, result):
        ind = result["indicators"]
        sig = result["overall_signal"]
        trend = result["trend"]

        lines = []
        lines.append(f"Price: ₹{ind['price']} ({ind.get('change_pct', 0):+.2f}%)")
        lines.append(f"Signal: {sig['signal']} (Confidence: {sig['confidence']}%)")
        lines.append(f"Trend: Short={trend['short']}, Medium={trend['medium']}, Long={trend['long']}")
        if ind.get("rsi"): lines.append(f"RSI: {ind['rsi']}")
        if ind.get("supertrend_direction") is not None:
            lines.append(f"Supertrend: {'Bullish' if ind['supertrend_direction'] == 1 else 'Bearish'}")
        if ind.get("volume_ratio"): lines.append(f"Volume: {ind['volume_ratio']:.1f}x average")
        if sig["reasons"]: lines.append("Key reasons: " + "; ".join(sig["reasons"]))

        sr = result["support_resistance"]
        if sr["support"]: lines.append(f"Support: {', '.join(str(s) for s in sr['support'][:2])}")
        if sr["resistance"]: lines.append(f"Resistance: {', '.join(str(r) for r in sr['resistance'][:2])}")

        return "\n".join(lines)
