from blueshift.library.technicals.indicators import bollinger_band, doji

from blueshift.finance import commission, slippage
from blueshift.api import(  symbol, order_target_percent, set_commission, set_slippage, schedule_function, date_rules, time_rules, get_datetime)
import talib as ta

def initialize(context):
    # universe selection
    # context.securities = [symbol('NIFTY-I'),symbol('BANKNIFTY-I')]
    context.securities = [symbol('NIFTY-I')]

    # define strategy parameters
    context.params = {'indicator_lookback':375, 
                      'indicator_freq':'1m', 
                      'buy_signal_threshold':1, 
                      'sell_signal_threshold':-1, 
                      'ROC_period_short':30, 
                      'ROC_period_long':120, 
                      'BBands_period':300, 
                      'trade_freq': 1, 
                      'leverage':2,
                      }

    # variables to track signals and target portfolio
    context.signals = dict((security,0) for security in context.securities)
    context.target_position = dict((security,100000000) for security in context.securities)
    context.stop_loss = dict((security,0) for security in context.securities)
    context.target_price = dict((security,0) for security in context.securities)
    context.stop_loss_short = dict((security,0) for security in context.securities)
    context.target_price_short = dict((security,0) for security in context.securities)

    # set trading cost and slippage to zero
    set_commission(commission.PerShare(cost=0.0, min_trade_cost=0.0))
    set_slippage(slippage.FixedSlippage(0.00))
    
    freq = int(context.params['trade_freq'])
    # schedule_function(run_strategy, date_rules.every_day(), time_rules.market_close(minutes=59))
    schedule_function(run_strategy, date_rules.every_day(), time_rules.every_nth_minute(freq))
    schedule_function(stop_trading, date_rules.every_day(), time_rules.market_close(minutes=30))
    
def before_trading_start(context, data):
    context.trade = True
    
def stop_trading(context, data):
    context.trade = False

def run_strategy(context, data):
    if not context.trade:
        return
    generate_signals(context, data)
    generate_target_position(context, data)
    rebalance(context, data)

def rebalance(context,data):
    for security in context.securities:
        order_target_percent(security, context.target_position[security])

def generate_target_position(context, data):
    num_secs = len(context.securities)
    weight = round(1.0/num_secs,2)*context.params['leverage']

    for security in context.securities:
        if context.signals[security] == context.params['buy_signal_threshold']:
            context.target_position[security] = weight
        elif context.signals[security] == context.params['sell_signal_threshold']:
            context.target_position[security] =  -weight
        else:
            context.target_position[security] =  0
        


def generate_signals(context, data):
    try:
        price_data = data.history(context.securities, ['open','high','low','close'], context.params['indicator_lookback'], context.params['indicator_freq'])
        price_data.drop(price_data.index[-1], inplace=True)
        price_data_current = data.current(context.securities, ['open','high','low','close'])
    except:
        return 

    for security in context.securities:
        px = price_data.xs(security)
        curr_price=price_data_current.xs(security)
        context.signals[security] = signal_function(context,px,curr_price,security)

def signal_function(context,px,curr_price,security):
    ind1 = doji(px)
    if(ind1):
        # print("doji ban gayi !!, on", get_datetime())
        # upper, mid, lower = bollinger_band(px.close.values, context.params['BBands_period'])
        uppe, mi, lowe = ta.BBANDS(px.close.values, timeperiod=context.params['BBands_period'],nbdevup=1.5,nbdevdn=1.5)
        upper=uppe[-1]
        mid=mi[-1]
        lower=lowe[-1]
        # print(upper,mid,lower)
        last_px = px.iloc[-1]
        h = last_px['high']
        l = last_px['low']
        # print("doji high",h,"low",l)
        # print("current price:-",curr_price)
        if (h < lower):
            if (curr_price['close']  > h):
                # print("!!!!!!!!!!!!!!!!!!!!!! NOW WE CAN BUY !!!!!!!!!!!!!!!!!!!!!!")
                context.stop_loss[security]=l
                context.target_price[security]=(3*(h-l))+h
                return 1
        if(l>upper):
            if(curr_price['close']<l):
                # print("!!!!!!!!!!!!!!!!!!!!!! NOW WE CAN SELL !!!!!!!!!!!!!!!!!!!!!!")
                context.stop_loss_short[security]=h
                context.target_price_short[security]=l-(3*(h-l))
                return -1
        if(context.target_position[security] >0):
            if(curr_price['close'] <=context.stop_loss[security] or curr_price['close'] >= context.target_price[security]):
                return 0
        if(context.target_position[security] <0):
            if(curr_price['close'] >= context.stop_loss_short[security] or curr_price['close'] <= context.target_price_short[security]):
                return 0
    return context.signals[security]
