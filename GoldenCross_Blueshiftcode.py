from blueshift.api import date_rules, time_rules, symbol
from blueshift.api import schedule_function, set_long_only, order_target_percent
from blueshift.library.library import alpha_function, get_history, enter_long
from blueshift.library.library import finish_prune_tracking, init_prune_tracking


def initialize(context):
    set_long_only()
    context.universe = [symbol('RELIANCE')]
    context.deathcross = {}
    context.golden_cross = {}
    context.shortterm_ma = {}
    context.longtermma = {}
    schedule_function(scheduled_func_87631, date_rules.every_day(),
        time_rules.market_open(hours=0, minutes=5))


def rule_func_87643(context, data):
    for asset in context.universe:
        if context.deathcross[asset]:
            enter_long(context, asset, order_target_percent, -0.25, None,
                'SCHEDULE')


def rule_func_87635(context, data):
    for asset in context.universe:
        if context.golden_cross[asset]:
            enter_long(context, asset, order_target_percent, 0.25, None,
                'SCHEDULE')
