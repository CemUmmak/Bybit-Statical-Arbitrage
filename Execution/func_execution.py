import json
from config_api_execution import *
from statsmodels.tsa.stattools import coint
import statsmodels.api as sm
import pandas as pd
import datetime
import math
import time
import telebot


#Puts all close prices in a list
def extract_close_prices(prices):
    close_prices = []
    for i in prices:
        if math.isnan(i["close"]):
            return []
        close_prices.append(i["close"])
    return close_prices

# Get trade details and lastest prices
def get_trade_details(orderbook, direction="Buy", capital=100):

    # Set calculation and output variables
    midPrice = 0
    quantity = 0
    stoploss = 0
    bidItemList = []
    askItemList = []

    if orderbook:
        # Set price rounding
        priceRounding = roundingTicker1 if orderbook["result"][0]["symbol"] == ticker1 else roundingTicker2
        quantityRounding = quantityRoundingTicker1 if orderbook["result"][0]["symbol"] == ticker1 else quantityRoundingTicker2
        for i in orderbook["result"]:
            if i["side"] == "Buy":
                bidItemList.append(float(i["price"]))
            else:
                askItemList.append(float(i["price"]))

        # Calculate price, size , stoploss and avarage liquidity
        if len(askItemList) > 0 and len(bidItemList) > 0:
            #sort list
            askItemList.sort()
            bidItemList.sort()
            bidItemList.reverse()

            # Get nearet ask, nearest bif and orderbook spread
            nearest_ask = askItemList[0]
            nearest_bid = bidItemList[0]

            #calculate hard stop loss
            if direction == "Buy":
                midPrice = nearest_bid
                stoploss = round(midPrice * (1 - stopLossFail),priceRounding)
            elif direction == "Sell":
                midPrice = nearest_ask
                stoploss = round(midPrice * (1 + stopLossFail),priceRounding)

            # Canculate Quantity
            quantity = round(capital/ midPrice,quantityRounding)

    return midPrice,stoploss,quantity

# Get position information
def get_position_info(ticker):
    size = 0
    side = ""
    position = session_auth.my_position(symbol=ticker)
    if "ret_msg" in position.keys():
        if position["ret_msg"] == "OK":
            if len(position["result"]) == 2:
                if position["result"][0]["size"] > 0 :
                    size = position["result"][0]["size"]
                    side = position["result"][0]["side"]
                else :
                    size = position["result"][1]["size"]
                    side = position["result"][1]["side"]
    return side,size

# Place market close order
def place_market_close_order(ticker,side,size):

    # Close position
    session_auth.place_active_order(
        symbol=ticker,
        side=side,
        order_type="Market",
        qty=size,
        time_in_force="GoodTillCancel",
        reduce_only=True,
        close_on_trigger=False)
    return

def close_all_position(kill_switch=1):

    # Cancel oll active orders
    session_auth.cancel_all_active_orders(symbol=signalPositiveTicker)
    session_auth.cancel_all_active_orders(symbol=signalNegativeTicker)

    # Get position information
    side1, size1 = get_position_info(signalPositiveTicker)
    side2, size2 = get_position_info(signalNegativeTicker)
    if size1 > 0:
        place_market_close_order(signalPositiveTicker,("Buy" if side1 == "Sell" else "Sell"), size1)
    if size2 > 0:
        place_market_close_order(signalNegativeTicker,("Buy" if side2 == "Sell" else "Sell"), size2)

    kill_switch = 0
    return  kill_switch


def set_leverage(ticker):

    # Setting the leverage
    try:
        session_auth.cross_isolated_margin_switch(
            symbol=ticker,
            is_isolated=True,
            buy_leverage=5,
            sell_leverage=5,
        )
    except Exception as ex:
        print("Kaldıraç Ayarlanmadı. ")
    return

def place_order(ticker, price, side, quantity, stopLoss):

   if limitOrderBasis:
       order = session_auth.place_active_order(
           symbol=ticker,
           side=side,
           order_type="Limit",
           qty=quantity,
           price=price,
           time_in_force="GoodTillCancel",
           reduce_only=False,
           close_on_trigger=False,
           stop_loss = stopLoss)
   else:
       order = session_auth.place_active_order(
           symbol=ticker,
           side=side,
           order_type="Market",
           qty=quantity,
           time_in_force="GoodTillCancel",
           reduce_only=False,
           close_on_trigger=False,
           stop_loss = stopLoss)
   return order

# Initialise execution
def initialise_order_execution(ticker, direction, capital):
    orderbook = sessionPublic.orderbook(symbol=ticker)
    midPrice, stoploss, quantity = get_trade_details(orderbook,direction,capital)
    order = place_order(ticker,midPrice,direction,quantity,stoploss)
    if quantity > 0:
        if "result" in order.keys():
            if "order_id" in order["result"]:
                return order["result"]["order_id"]
    return 0

# Get Start Times

def get_timestapms():
    now = datetime.datetime.now()
    timeStartDate = now - datetime.timedelta(minutes=(klineLimit*timeFrame))
    timeStartSec = int(timeStartDate.timestamp())

    return timeStartSec

#Get historical prices (klines)
def get_price_klines(ticker):

    # Get prices
    timeStartSec = get_timestapms()
    prices = sessionPublic.query_kline(
        symbol=ticker,
        interval = timeFrame,
        limit = klineLimit,
        from_time=timeStartSec)
    # Manage API calls
    time.sleep(0.1)
    if len(prices["result"]) != klineLimit:
        return[]
    return prices["result"]

# Get lastest kline
def get_lastest_klines():
    series1 = []
    series2 = []
    prices1 = get_price_klines(ticker1)
    prices2 = get_price_klines(ticker2)

    if len(prices1) > 0:
        series1 = extract_close_prices(prices1)
    if len(prices2) > 0:
        series2 = extract_close_prices(prices2)
    return series1,series2

# Get trade liquidiry for ticker
def get_ticker_trade_liqudity(ticker):
    trades = sessionPublic.public_trading_records(
        symbol=ticker,
        limit=50
    )
    # Get the avarage liquidity
    quantityList = []
    if "result" in trades.keys():
        for i in trades["result"]:
            quantityList.append(i["qty"])

    if len(quantityList) > 0:
        return (sum(quantityList) / len(quantityList)), float(trades["result"][0]["price"])
    return 0,0

def calculate_metrics(series1,series2):
    cointFlag = 0
    cointResault = coint(series1,series2)
    cointT = cointResault[0]
    pValue = cointResault[1]
    criticalValue = cointResault[2][1]
    model = sm.OLS(series1,series2).fit()
    hedgeRatio = model.params[0]
    spread = calculate_spread(series1,series2,hedgeRatio)
    zScoreList = calculate_zscore(spread)
    if pValue < 0.5 and cointT < criticalValue:
        cointFlag = 1
    spread = spread.values[(len(spread)-1)]
    return cointFlag, zScoreList.tolist(), ("Positive" if spread > 0 else "Negative")

def calculate_spread(series1,series2,hedge_ratio):
    spread = pd.Series(series1) - (pd.Series(series2) * hedge_ratio)
    return spread

def calculate_zscore(spread):
    df = pd.DataFrame(spread)
    mean = df.rolling(center=False, window= zScoreWindow).mean()
    std  = df.rolling(center=False, window= zScoreWindow).std()
    x    = df.rolling(center=False, window=1).mean()
    df["ZScore"] = (x - mean ) / std
    return df["ZScore"].astype(float).values

def get_latest_zscrore():

    # Get last asset orderbook prices and add dummy price for latest
    # Get last price history
    series1, series2 = get_lastest_klines()
    series1 = series1[:-1]
    series2 = series2[:-1]
    # Get z-scrore and confirm if hot
    if len(series1) > 0 and len(series2) > 0:
        _, zScoreList, spread = calculate_metrics(series1,series2)
        zScore = zScoreList[-1]
        if zScore > 0:
            signalSinPositive = True
        else:
            signalSinPositive = False
        return round(zScore,2),signalSinPositive,spread


def open_position_confirmation(ticker):
    try:
        position = sessionPrivate.my_position(symbol=ticker)
        if position["ret_msg"] == "OK":
            for i in position["result"]:
                if i["size"] > 0:
                    return True
    except Exception as ex:
        print(f"Error : {ex}. Open position confirmation.")
        return True
    return False

def active_position_confirmation(ticker):
    try:
        active = sessionPrivate.get_active_order(symbol=ticker, order_status="Created,New,PartiallyFilled,Active")
        if active["ret_msg"] == "OK":
            if active["result"]["data"] != None:
                return True
    except Exception as ex:
        print(f"Error : {ex}. Active position confirmation.")
        return True
    return False

# Get open position price and quantity
def get_open_positions(ticker, direction="Buy"):

    position = sessionPrivate.my_position(symbol=ticker)

    # Select index to avoid looping throught response
    index = 0 if direction == "Buy" else 1

    if "ret_msg" in position.keys():
        if position["ret_msg"] == "OK":
            if "symbol" in position["result"][index].keys():
                orderPrice = position["result"][index]["entry_price"]
                orderQuant = position["result"][index]["size"]
                return orderPrice,orderQuant
    return 0,0


def get_active_positions(ticker, direction="Buy"):

    active = sessionPrivate.get_active_order(symbol=ticker, order_status="Created,New,PartiallyFilled,Active")
    if "ret_msg" in active.keys():
        if active["ret_msg"] == "OK":
            if active["result"]["data"] != None:
                orderPrice = active["result"]["data"][0]["price"]
                orderQuant = active["result"]["data"][0]["qty"]
                return orderPrice, orderQuant
    return 0, 0

# Query existing order
def query_existing_order(ticker, orderID):

    order = sessionPrivate.query_active_order(symbol=ticker, order_id = orderID)

    if "ret_msg" in order.keys():
        if order["ret_msg"] == "OK":
            orderPrice = order["result"]["price"]
            orderQuant = order["result"]["qty"]
            orderStatus = order["result"]["order_status"]
            return orderPrice,orderQuant,orderStatus
    return 0,0,0

def check_order(ticker, orderID, reamingCapital, direction = "Buy"):

    # Get trade details
    orderPrice,orderQuant,orderStatus = query_existing_order(ticker,orderID)

    # Get open positions
    positionPrice, positionQuant = get_open_positions(ticker,direction)

    # Determine action - trade complate - stop placing orders
    if positionQuant >= (reamingCapital*0.7) and positionQuant > 0:
        return "Trade Complate"

    # Determine action - position filled - Buy More
    if orderStatus == "Filled":
        return "Position Filled"

    # Determine action - order active - do nothing
    activeItems = ["Created", "New"]
    if orderStatus in activeItems:
        return "Order Active"

    # Determine action - partial filled order - do nothing
    if orderStatus == "PartiallyFilled":
        return "Partial Fill"

    # Determine action - order filled - try place order again
    cancelItems = ["Cancelled", "Rejected", "PendingCancel"]
    if orderStatus in cancelItems:
        return "Try Again"

def save_status(dict):
    with open("../Data/4_status.json","w") as st:
        json.dump(dict,st,indent=4)

def manage_new_trades(killSwitch,FirstStart):

    # Set output variables
    orderLongID = ""
    orderShortID = ""
    signalSide = ""
    hot = False
    zScore = 0

    # Get and save the lastest z-score
    timeChance15 = minute_is_chance(2,[0, 15, 30, 45])

    if timeChance15 or FirstStart:
        zScore,signalSinPositive , spread = get_latest_zscrore()
        print("Z-Score = ",zScore)
    # Switch to hot if meet signal threshold
        if abs(zScore) > signalTriggerThresh:
            # Active hot trigger
            hot = True
            print("-- Trade Status HOT --\n-- Placing and Monitoring Existing Trades -- ")
            send_telegram(f"ByBit Arbitrage Bot\n\nNew position opened.\n\nSpread : {spread}\n\nZ-Score : {zScore}","5573175354:AAH32qOFLU-S-Vkd_n82yLPcI2NZ_yASpKw", "-1001706505505", True)
        else:
            print("Z-Score is not high enough")
            time.sleep(5)

    # Place and manage trades
    if hot and killSwitch == 0:

        # Get trades hisyory for liqudity
        avrLiqudityPositive, lastPricePositive = get_ticker_trade_liqudity(signalPositiveTicker)
        avrLiqudityNegative, lastPriceNegative = get_ticker_trade_liqudity(signalNegativeTicker)

        # Determine long ticker vs short ticker
        if signalSinPositive:
            longTicker = signalPositiveTicker
            shortTicker = signalNegativeTicker
            avgLiqudityLong = avrLiqudityPositive
            avgLiqudityShort = avrLiqudityNegative
            lastPriceLong = lastPricePositive
            lastPriceShort = lastPriceNegative
        else :
            longTicker = signalNegativeTicker
            shortTicker = signalPositiveTicker
            avgLiqudityLong = avrLiqudityNegative
            avgLiqudityShort = avrLiqudityPositive
            lastPriceLong = lastPriceNegative
            lastPriceShort = lastPricePositive

        # Fill targest
        capitalLong = tradeableCapitalUSDT * 0.5
        capitalShort = tradeableCapitalUSDT * 0.5
        initialFillTargetLongUsdt = avgLiqudityLong * lastPriceLong
        initialFillTargetShortUsdt = avgLiqudityShort * lastPriceShort
        initialCapitalInjection = min(initialFillTargetLongUsdt,initialFillTargetShortUsdt)

        # Ensure inital capital does not exceed limits set in configuration
        if limitOrderBasis:
            if initialCapitalInjection > capitalLong:
                initalCapitalUsdt = capitalLong
            else:
                initalCapitalUsdt = initialCapitalInjection
        else:
            initalCapitalUsdt = capitalLong

        # Set remaining capital
        remainingCapitalLong = capitalLong
        remainingCapitalShort = capitalShort

        # Trade until filled or signal is false

        orderStatusLong = ""
        orderStatusShort = ""
        countsLong = 0
        countsShort = 0

        while killSwitch == 0:

            # Place order - long
            if countsLong == 0:
                orderLongID = initialise_order_execution(longTicker,"Buy",initalCapitalUsdt)
                countsLong = 1 if orderLongID else 0
                remainingCapitalLong = remainingCapitalLong-initalCapitalUsdt

            # Place order - short
            if countsShort == 0:
                orderShortID = initialise_order_execution(shortTicker,"Sell",initalCapitalUsdt)
                countsShort = 1 if orderShortID else 0
                remainingCapitalShort = remainingCapitalShort-initalCapitalUsdt

            # Update signal side
            signalSide = "positive" if zScore > 0 else "negative"

            # Handle kill switch for market orders
            if not limitOrderBasis and countsLong and countsShort:
                killSwitch = 1

            # Allow for time to register the limit orders
            time.sleep(3)

            # Check limit orders and ensure Zscore is still with in range
            zScoreNew, signalSinPositiveNew,spread = get_latest_zscrore()
            if killSwitch == 0:
                if abs(zScoreNew) > (signalTriggerThresh * 0.9) and signalSinPositiveNew == signalSinPositive:

                    # Check long order status
                    if countsLong == 1:
                        orderStatusLong = check_order(longTicker,orderLongID,remainingCapitalLong,"Buy")

                    # Check short order status
                    if countsShort == 1:
                        orderStatusShort = check_order(shortTicker,orderShortID,remainingCapitalShort,"Sell")

                    # if orders still active, do nothing
                    if orderStatusLong == "Order Active" or orderStatusShort == "Order Active":
                        continue

                    # if orders partial fill, do nothing
                    if orderStatusLong == "Partial Fill" or orderStatusShort == "Partial Fill":
                        continue

                    # if orders trade complate, stop opening trade
                    if orderStatusLong == "Trade Complate" and orderStatusShort == "Trade Complate":
                        killSwitch = 1

                    # if position filled - place another trade
                    if orderStatusLong == "Position Filled" and orderStatusShort == "Position Filled":
                        countsLong = 0
                        countsShort = 0

                    # if order cancelled for long try again
                    if orderStatusLong == "Try Again":
                        countsLong = 0

                    # if order cancelled for short try again
                    if orderStatusShort == "Try Again":
                        countsShort = 0
                else:
                    # Cancel all active orders
                    sessionPrivate.cancel_all_active_orders(symbol=signalPositiveTicker)
                    sessionPrivate.cancel_all_active_orders(symbol=signalNegativeTicker)
                    killSwitch = 1
    return killSwitch,signalSide

def send_telegram(message,tapi,tchat,telegram):
    if telegram:
        telebot.TeleBot(tapi).send_message(tchat,message)

def get_unrelized_pnl():
    info1 = session_auth.my_position(symbol=ticker1)
    info2 = session_auth.my_position(symbol=ticker2)
    info3 = info1["result"] + info2["result"]
    pnl = 0
    for i in info3:
        if i["size"] > 0:
            pnl += i["unrealised_pnl"]
    return pnl

def minute_is_chance(staticVariableCount=0,minuteList=list(range(0,60,1))):
    """
    returns true if minutes change
    """
    timeNow = datetime.datetime.now().strftime("%M")
    staticTime = 0
    try:
        with open(f"../Data/{staticVariableCount}staticTimeMinute.json", "r") as st:
            dt = json.load(st)
            staticTime = dt["time"]
            st.close()
    except:
        with open(f"../Data/{staticVariableCount}staticTimeMinute.json","w") as st:
            json.dump({"time" : timeNow},st,indent=4)
    if staticTime != timeNow:
        if int(timeNow) in minuteList:
            with open(f"../Data/{staticVariableCount}staticTimeMinute.json","w") as st:
                json.dump({"time" : timeNow},st,indent=4)
                return True
        return False
    return False

