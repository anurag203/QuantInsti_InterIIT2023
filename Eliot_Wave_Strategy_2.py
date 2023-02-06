from blueshift.library.technicals.indicators import fibonacci_support, adx
from blueshift.finance import commission, slippage
from blueshift.api import symbol, order_target_percent, set_commission, set_slippage, schedule_function, date_rules, time_rules, get_datetime
import numpy as np
import pandas as pd
from math import sqrt
import talib as ta

def initialize(context):
    # universe selection
    # context.securities = [symbol('NIFTY-I'),symbol('BANKNIFTY-I')]
    # context.securities = [symbol('MARUTI'),symbol('TVSMOTOR'),symbol('EICHERMOT'),symbol('ESCORTS'),symbol('ASHOKLEY'),symbol('TATAMOTORS'),symbol('MOTHERSON')]
    context.securities = [symbol('BAJFINANCE'),symbol('HDFCBANK'),symbol('ICICIBANK'),symbol('KOTAKBANK'),symbol('SBIN'),symbol('BAJAJFINSV'),symbol('AXISBANK')]
    # context.securities = [symbol('TCS'),symbol('INFY'),symbol('WIPRO'),symbol('TECHM'),symbol('HCLTECH'),symbol('COFORGE'),symbol('MPHASIS')]
    # context.securities = [symbol('JSL'),symbol('JSWSTEEL'),symbol('TATASTEEL'),symbol('TECHM'),symbol('ADANIENT'),symbol('HINDALCO'),symbol('WELCORP')]
    # context.securities = [symbol('ADANIPOWER')]

    # define strategy parameters
    context.params = {'indicator_lookback':100,
                      'indicator_freq':'1d',
                      'buy_signal':1,
                      'sell_signal':-1,
                      'ROC_period_short':30,
                      'ROC_period_long':120,
                      'ADX_period':120,
                      'trade_freq':1,
                      'leverage':2}

    # variables to calculate support and resistance line and target portfolio
    context.stop_loss = dict((security,0) for security in context.securities)
    context.previous_peak = dict((security,0) for security in context.securities)
    context.signal = dict((security,0) for security in context.securities)
    context.target_position = dict((security,0) for security in context.securities)

    # set trading cost and slippage to zero
    set_commission(commission.PerShare(cost=0.002, min_trade_cost=0.0))
    set_slippage(slippage.FixedSlippage(0.00))
    
    freq = int(context.params['trade_freq'])
    # schedule_function(run_strategy, date_rules.every_day(), time_rules.every_nth_minute(freq))
    schedule_function(run_strategy, date_rules.every_day(), time_rules.market_open(minutes=45))
    schedule_function(stop_trading, date_rules.every_day(), time_rules.market_close(minutes=30))

def before_trading_start(context, data):
    context.trade = True
    
def stop_trading(context, data):
    context.trade = False

def run_strategy(context, data):
    if not context.trade:
        return
    
    generate_max_min(context,data)
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
        else:
            context.target_position[security] = 0


def generate_signal(context,security,points):
    curr = points[len(points)-1] #current price 
    m_avg = ta.SMA(points, 40)
    m_avg=m_avg[-1]
    if(curr>=m_avg):
        context.signal[security] = context.params['buy_signal']
    elif(curr<= m_avg):
        context.signal[security] = context.params['sell_signal']
    elif(curr>=context.previous_peak[security]):
        context.signal[security] = context.params['buy_signal']
    elif(curr<=context.stop_loss[security]):
        context.signal[security] = context.params['sell_signal']



def generate_max_min(context, data):
    try:
        price_data = data.history(context.securities, ['open','high','low','close'], context.params['indicator_lookback'], context.params['indicator_freq'])
    except:
        return

    for security in context.securities:
        px = price_data.xs(security)
        context.previous_peak[security], context.stop_loss[security] = loc_max_min(px)
        generate_signal(context,security,px.close.values)


# Function to calculate last minima and maxima price
def loc_max_min(px):
    points=px.close.values
    i=len(points)-2
    for j in range(1,len(points)-1):
        i=len(points)-1-j
        if points[i-1] > points[i] < points[i+1]:
            mi=points[i]
            break

    for j in range(1,len(points)-1):
        i=len(points)-1-j
        if points[i-1] < points[i] > points[i+1]:
            ma=points[i]
            break                 
    return ma,mi
