from blueshift.library.technicals.indicators import fibonacci_support, adx
from blueshift.finance import commission, slippage
from blueshift.api import symbol, order_target_percent, set_commission, set_slippage, schedule_function, date_rules, time_rules, get_datetime
import numpy as np
import pandas as pd
import talib as ta
from math import sqrt

def initialize(context):
    # universe selection
    # context.securities = [symbol('BAJFINANCE'),symbol('HDFCBANK'),symbol('ICICIBANK'),symbol('KOTAKBANK'),symbol('SBIN'),symbol('BAJAJFINSV'),symbol('AXISBANK')]
    # context.securities = [symbol('ADANIPOWER')]
    # context.securities = [symbol('JSL'),symbol('JSWSTEEL'),symbol('TATASTEEL'),symbol('TECHM'),symbol('ADANIENT'),symbol('HINDALCO'),symbol('WELCORP')]
    # context.securities = [symbol('TCS'),symbol('INFY'),symbol('WIPRO'),symbol('TECHM'),symbol('HCLTECH'),symbol('COFORGE'),symbol('MPHASIS')]
    context.securities = [symbol('MARUTI'),symbol('TVSMOTOR'),symbol('EICHERMOT'),symbol('ESCORTS'),symbol('ASHOKLEY'),symbol('TATAMOTORS'),symbol('MOTHERSON')]
    # define strategy parameters
    context.params = {'indicator_lookback':300,
                      'indicator_freq':'1d',
                      'buy_signal':1,
                      'sell_signal':-1,
                      'short_sell_signal':-1,
                      'short_buy_signal':1,
                      'ROC_period_short':30,
                      'ROC_period_long':120,
                      'ADX_period':120,
                      'trade_freq':1,
                      'leverage':2}

    # variables to calculate support and resistance line and target portfolio
    context.stop_loss = dict((security,0) for security in context.securities)
    context.exits = dict((security,0) for security in context.securities)
    context.signal = dict((security,0) for security in context.securities)
    context.target_position = dict((security,0) for security in context.securities)

    # set trading cost and slippage to zero
    set_commission(commission.PerShare(cost=0.002, min_trade_cost=0.0))
    set_slippage(slippage.FixedSlippage(0.00))
    
    freq = int(context.params['trade_freq'])
    schedule_function(run_strategy, date_rules.every_day(), time_rules.every_nth_minute(freq))
    # schedule_function(run_strategy, date_rules.every_day(), time_rules.market_close(minutes=59))
    schedule_function(stop_trading, date_rules.every_day(), time_rules.market_close(minutes=30))

def before_trading_start(context, data):
    context.trade = True
    
def stop_trading(context, data):
    context.trade = False

def run_strategy(context, data):
    if not context.trade:
        return
    
    generate_signal(context,data)
    generate_target_position(context, data)
    rebalance(context, data)

def rebalance(context,data):
    for security in context.securities:
        order_target_percent(security, context.target_position[security])

def generate_target_position(context, data):
    num_secs = len(context.securities)
    weight = round(1.0/num_secs,2)*context.params['leverage']

    for security in context.securities:
        if context.signal[security] == context.params['buy_signal']:
            context.target_position[security] = weight
        elif context.signal[security] == context.params['sell_signal']:
            context.target_position[security] = 0
        elif context.signal[security] == context.params['short_sell_signal']:
            context.target_position[security] = -weight
        elif context.signal[security] == context.params['short_buy_signal']:
            context.target_position[security] = 0


def is_bullish_engulfing_harami(candles):
    
        present_candle = candles.iloc[-1]
        en_candle = candles.iloc[-2]
        prev_candle = candles.iloc[-3]

        close = en_candle['close']
        openf = en_candle['open']
        high = en_candle['high']
        low = en_candle['low']

        prev_close = prev_candle['close']
        prev_open = prev_candle['open']
        prev_high = prev_candle['high']
        prev_low = prev_candle['low']

        # return (prev_close < prev_open and
        #         0.3 > abs(prev_close - prev_open) / (prev_high - prev_low) >= 0.1 and
        #         close > openf and
        #         abs(close - openf) / (high - low) >= 0.7 and
        #         prev_high < close and
        #         prev_low > openf)

        if (close >= prev_open and prev_open > prev_close and close > openf and prev_close >= openf and close - openf > prev_open - prev_close) or  (prev_open > prev_close and
                prev_close <= openf < close <= prev_open and
                close - openf < prev_open - prev_close):
            if present_candle['close']>=en_candle['high']:
                return True
            # return True
        return False



def is_bearish_engulfing_harami(candles):
    
        present_candle = candles.iloc[-1]
        en_candle = candles.iloc[-2]
        prev_candle = candles.iloc[-3]

        close = en_candle['close']
        openf = en_candle['open']
        high = en_candle['high']
        low = en_candle['low']

        prev_close = prev_candle['close']
        prev_open = prev_candle['open']
        prev_high = prev_candle['high']
        prev_low = prev_candle['low']

        # return (prev_close < prev_open and
        #         0.3 > abs(prev_close - prev_open) / (prev_high - prev_low) >= 0.1 and
        #         close > openf and
        #         abs(close - openf) / (high - low) >= 0.7 and
        #         prev_high < close and
        #         prev_low > openf)

        if (openf >= prev_close > prev_open and openf > close and prev_open >= close and openf - close > prev_close - prev_open) or (prev_close > prev_open and
                prev_open <= close < openf <= prev_close and openf - close < prev_close - prev_open):
            if present_candle['close']<=en_candle['low']:
                return True
            # return True
        return False

def sma(px, lookback):
    sig = ta.SMA(px.close.values, timeperiod=lookback)
    return sig[-1]

def generate_signal(context, data):
    try:
        price_data = data.history(context.securities, ['open','high','low','close'], context.params['indicator_lookback'], context.params['indicator_freq'])
    except:
        return

    for security in context.securities:
        px = price_data.xs(security)
        previous_candle = px.iloc[-2]
        present_candle=px.iloc[-1]
        last_to_last=px.iloc[-3]
        # check if the candle is bulish engulfing and 
        # is_bullish_engulfing_harami(px)

        if sma(px,200)>=present_candle['low'] :
            if is_bullish_engulfing_harami(px):
                context.signal[security] = context.params['buy_signal']
                context.stop_loss[security] = min(previous_candle['low'],last_to_last['low'])
                context.exits[security] = previous_candle['high']+3*(previous_candle['high']-previous_candle['low'])
            elif context.stop_loss[security]>=present_candle['close'] or context.exits[security]<=present_candle['close']:
                context.signal[security] = context.params['sell_signal']
        else:
            if is_bearish_engulfing_harami(px):
                context.signal[security] = context.params['short_sell_signal']
                context.stop_loss[security] = min(previous_candle['high'],last_to_last['high'])
                context.exits[security] = previous_candle['low']-3*(previous_candle['high']-previous_candle['low'])
            elif context.stop_loss[security]<=present_candle['close'] or context.exits[security]>=present_candle['close']:
                context.signal[security] = context.params['short_buy_signal']
        # else:
        #     context.signal[security] =0
