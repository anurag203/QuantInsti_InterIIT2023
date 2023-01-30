from blueshift.library.technicals.indicators import fibonacci_support, adx
from blueshift.finance import commission, slippage
from blueshift.api import symbol, order_target_percent, set_commission, set_slippage, schedule_function, date_rules, time_rules, get_datetime
import numpy as np
import pandas as pd
from math import sqrt

def initialize(context):
    # universe selection
    context.securities = [symbol('NIFTY-I'),symbol('BANKNIFTY-I')]

    # define strategy parameters
    context.params = {'indicator_lookback':100,
                      'indicator_freq':'1d',
                      'buy_signal_threshold':0.5,
                      'sell_signal_threshold':-0.5,
                      'ROC_period_short':30,
                      'ROC_period_long':120,
                      'ADX_period':120,
                      'trade_freq':30,
                      'leverage':2}

    # variables to calculate support and resistance line and target portfolio
    context.support_line = dict((security,0) for security in context.securities)
    context.resistance_line = dict((security,0) for security in context.securities)
    context.target_position = dict((security,0) for security in context.securities)

    # set trading cost and slippage to zero
    set_commission(commission.PerShare(cost=0.002, min_trade_cost=0.0))
    set_slippage(slippage.FixedSlippage(0.00))
    
    freq = int(context.params['trade_freq'])
    # schedule_function(run_strategy, date_rules.every_day(), time_rules.every_nth_minute(freq))
    schedule_function(run_strategy, date_rules.every_day(), time_rules.market_close(minutes=59))
    schedule_function(stop_trading, date_rules.every_day(), time_rules.market_close(minutes=30))

def before_trading_start(context, data):
    context.trade = True
    
def stop_trading(context, data):
    context.trade = False

def run_strategy(context, data):
    if not context.trade:
        return
    
    generate_support_resistance(context,data)
    generate_target_position(context, data)
    rebalance(context, data)

def rebalance(context,data):
    for security in context.securities:
        order_target_percent(security, context.target_position[security])

def generate_target_position(context, data):
    num_secs = len(context.securities)
    weight = round(1.0/num_secs,2)*context.params['leverage']

    for security in context.securities:
        print("support line for ", security,"on date",get_datetime() ,"is : ")
        print(context.support_line[security])
    #     if context.signals[security] > context.params['buy_signal_threshold']:
    #         context.target_position[security] = weight
    #     elif context.signals[security] < context.params['sell_signal_threshold']:
    #         context.target_position[security] = -weight
    #     else:
    #         context.target_position[security] = 0

def generate_support_resistance(context, data):
    try:
        price_data = data.history(context.securities, ['open','high','low','close'], context.params['indicator_lookback'], context.params['indicator_freq'])
    except:
        return

    for security in context.securities:
        px = price_data.xs(security)
        context.support_line[security], context.resistance_line[security] = s_r_func(px, context.params)

# Pythagoras function to calculate distance between two points
def pythg(pt1, pt2):
    a_sq = (pt2[0] - pt1[0]) ** 2
    b_sq = (pt2[1] - pt1[1]) ** 2
    return sqrt(a_sq + b_sq)

# Function to calculate local minima and maxima points
def loc_min_max(points):
    loc_minima = []
    loc_maxima = []
    prev_pts = [(0, points[0]), (1, points[1])]
    for i in range(1, len(points) - 1):
        append_to = ''
        if points[i-1] > points[i] < points[i+1]:
            append_to = 'min'
        elif points[i-1] < points[i] > points[i+1]:
            append_to = 'max'
        if append_to:
            if loc_minima or loc_maxima:
                prev_distance = pythg(prev_pts[0], prev_pts[1]) * 0.5
                curr_distance = pythg(prev_pts[1], (i, points[i]))
                if curr_distance >= prev_distance:
                    prev_pts[0] = prev_pts[1]
                    prev_pts[1] = (i, points[i])
                    if append_to == 'min':
                        loc_minima.append((i, points[i]))
                    else:
                        loc_maxima.append((i, points[i]))
            else:
                prev_pts[0] = prev_pts[1]
                prev_pts[1] = (i, points[i])
                if append_to == 'min':
                    loc_minima.append((i, points[i]))
                else:
                    loc_maxima.append((i, points[i]))                  
    return loc_minima, loc_maxima

def line_mse(pt1, pt2, data):
    dist = 0
    dist_sq = 0
    sum_dist_sq = 0
    mean_sq_err = 0
    length = len(data)

    for pt3 in range(0, length):
            p1 = data[pt1]
            p2 = data[pt2]
            p3 = data[pt3]           
            
            # To calculate perpendicular distance of a point from line passing through pt1 and pt2
            dist = np.abs(np.linalg.norm(np.cross(p2-p1, p1-p3)))/np.linalg.norm(p2-p1)            
            # Squared error of a point from line passing through pt1 and pt2
            dist_sq = dist**2
            # Sum of squared errors of all points from line passing through pt1 and pt2
            sum_dist_sq = sum_dist_sq + dist_sq
            
    # Mean squared error formula applied
    mean_sq_err = sum_dist_sq / length
    return (mean_sq_err)

def s_r_lines(data):
    lines = []
    for pt1 in range(0, len(data) - 1):
        for pt2 in range(0, len(data)):
            if pt1 != pt2:
                mse_val = line_mse(pt1, pt2, data)
                lines.append((data[pt1], data[pt2], mse_val))
    return lines

def line_least_mse(data):
    best_line = []
    # Temporarily assign value of first line in dataset as 'least_mse'
    least_mse = data[0][2]
    
    # Compare MSE values of all lines present in the dataset
    for r in range (0, len(data)):
            if data[r][2] < least_mse:
                
                # Assign the current value to 'least_mse' if 
                # the current value is less than existing value
                least_mse = data[r][2]
                
                # Store data of the line with least mse value
                best_line = data[r]
                
    return best_line

def s_r_func(px, params):
    points = px.close.values
    loc_minima, loc_maxima = loc_min_max(points)
    minima_pts = np.array(loc_minima)
    maxima_pts = np.array(loc_maxima)
    support_lines = s_r_lines(minima_pts)
    resistance_lines = s_r_lines(maxima_pts)
    support = line_least_mse(support_lines)
    resistance = line_least_mse(resistance_lines)
    return support, resistance