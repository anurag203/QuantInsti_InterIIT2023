from blueshift.api import schedule_function, date_rules, time_rules
from blueshift.api import get_datetime, symbol, order
import pandas as pd

def initialize(context):
    context.universe=[symbol('AAPL')] # list of shares we will be trading
    # shedule funtion for keep running program in specified time interval
    schedule_function(myfunc, date_rule=date_rules.every_day(), time_rule=time_rules.every_nth_minute(minutes=30))

def myfunc(context, data):
    # stock price of last 50 days
    prev_data = data.history(context.universe[0], 'close', 50, '1d')
    df = pd.DataFrame(prev_data) # converted to panda dataframe

    # finding last maxima (it is maxima if it is maximum in window of 5 days)
    df['rolling_max'] = df['close'].rolling(window=5).max()
    previous_peak = df[df['close'] == df['rolling_max']].iloc[-2]['close']

    # finding last minima (it is maxima if it is minimum in window of 5 days)
    df['rolling_min'] = df['close'].rolling(window=5).min()
    previous_low = df[df['close'] == df['rolling_min']].iloc[-2]['close']

    # current price 
    px = data.current(context.universe[0],'close')
    # print([previous_peak,previous_low,px])

    #calculating count of share of AAPL we have
    portfolio = context.portfolio
    positions = portfolio.positions
    tot_share = 0 # assuming 0 at first

    # str(asset).split("(")[1].split(")")[0] # for getting share name and id
    
    for asset in positions:
        position = positions[asset]
        tot_share = position.quantity

    if(px > previous_peak):
        x = portfolio.cash / px # count we can buy with our cash
        x= int(x)
        if(x > 0):
            order(context.universe[0], x) # buying shares
    if(px < previous_low and tot_share > 0):
        order(context.universe[0],-tot_share) # selling shares

    # print(f'scheduled function called at {get_datetime()}')