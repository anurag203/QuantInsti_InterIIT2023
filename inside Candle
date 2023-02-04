
from blueshift.library.technicals.indicators import fibonacci_support, adx
import numpy as np
import pandas as pd
import talib 
from blueshift.finance import commission, slippage
from blueshift.api import(  symbol,
                            order_target_percent,
                            set_commission,
                            set_slippage,
                            schedule_function,
                            date_rules,
                            time_rules,
                            get_datetime,
                       )

def initialize(context):
    """
        A function to define things to do at the start of the strategy
    """
    # universe selection
    context.securities = [symbol('RELIANCE')]

    # define strategy parameters
    context.params = {'indicator_lookback':6,
                      'indicator_freq':'1m',
                      'buy_signal_threshold':0.5,
                      'sell_signal_threshold':-0.5,
                      'ROC_period_short':30,
                      'ROC_period_long':120,
                      'ADX_period':120,
                      'trade_freq':1,
                      'leverage':2}

    # variable to control trading frequency
    context.bar_count = 0

    # variables to track signals and target portfolio
    context.signals = dict((security,0) for security in context.securities)
    context.target_position = dict((security,0) for security in context.securities)
    context.stop_loss = dict((security,0) for security in context.securities)
    context.target_price = dict((security,0) for security in context.securities)
    
    # set trading cost and slippage to zero
    set_commission(commission.PerShare(cost=0.002, min_trade_cost=0.0))
    set_slippage(slippage.FixedSlippage(0.00))
    
    freq = int(context.params['trade_freq'])
    schedule_function(run_strategy, date_rules.every_day(),
                      time_rules.every_nth_minute(freq))
    
    schedule_function(stop_trading, date_rules.every_day(),
                      time_rules.market_close(minutes=30))

def before_trading_start(context, data):
    context.trade = True
    
def stop_trading(context, data):
    context.trade = False

def run_strategy(context, data):
    """
        A function to define core strategy steps
    """
    if not context.trade:
        return
    
    generate_signals(context, data)
    generate_target_position(context, data)
    rebalance(context, data)

def rebalance(context,data):
    '''
        A function to rebalance - all execution logic goes here
    '''
    for security in context.securities:
        order_target_percent(security, context.target_position[security])

def generate_target_position(context, data):
    """
        A function to define target portfolio
    """
    num_secs = len(context.securities)
    weight = round(1.0/num_secs,2)*context.params['leverage']

    for security in context.securities:
        if context.signals[security] > context.params['buy_signal_threshold']:
            context.target_position[security] = weight
        elif context.signals[security] < context.params['sell_signal_threshold']:
            context.target_position[security] = -weight
        else:
            context.target_position[security] = 0

def generate_signals(context, data):
    """
        A function to define define the signal generation
    """
    try:
        price_data = data.history(context.securities, ['open','high','low','close'],
            context.params['indicator_lookback'], context.params['indicator_freq'])
        price_data_current = data.current(context.securities, ['open','high','low','close'])
    except:
        return

    for security in context.securities:
        px = price_data.xs(security)
        curr_candle=px.iloc[-1]
        prev_candle = px.iloc[-2]
        prev_prev_candle = px.iloc[-3]
        # inside_candel_finder(px)
        if inside_candel_finder(px):
            if curr_candle["close"]>prev_candle["high"]:
                context.signals[security] = 1
                context.stop_loss[security] = prev_prev_candle["low"]
                context.target_price[security] = (abs(prev_candle['close']-prev_candle['open'])*2) + prev_candle['high']
                print(" long jaa raha hai at ",get_datetime()," stop loss hai = ",context.stop_loss[security]," target hai = ", context.target_price[security])
            elif curr_candle["close"]<prev_candle["low"]:
                context.signals[security] = -1
                context.stop_loss[security] = prev_prev_candle["high"]
                context.target_price[security] = prev_candle['low']- (abs(prev_candle['close']-prev_candle['open'])*2)  
                print(" short jaa raha hai at ",get_datetime()," stop loss hai = ",context.stop_loss[security]," target hai = " ,context.target_price[security])
        elif context.signals[security]>0:
            if context.stop_loss[security] >= curr_candle['close'] or context.target_price[security] <= curr_candle['close']:
                context.signals[security] = 0
                print(" stop loss ya get profit ho gaya long mai",get_datetime())
        elif context.signals[security]<0:
            if context.stop_loss[security] <= curr_candle['close'] or context.target_price[security] >= curr_candle['close']:
                context.signals[security] = 0
                print(" stop loss ya get profit ho gaya short mai",get_datetime())



def inside_candel_finder(px):
    df = px.copy()
    # print(df)
    high =  df["high"]
    low = df["low"]
    open_ = df["open"]
    close = df["close"]

    mother_body = abs(close[-3]-open_[-3])
    child_body = abs(close[-2]-open_[-2])

    if (high[-3]>high[-2] and low[-2]>low[-3] and mother_body/1.5>=child_body):
        return True
    else :
        return False

