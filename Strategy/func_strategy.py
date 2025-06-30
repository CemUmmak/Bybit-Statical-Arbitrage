from config_api_strategy import session,timeFrame,klineLimit,zScoreWindow
from statsmodels.tsa.stattools import coint
import matplotlib.pyplot as plt
import statsmodels.api as sm
import pandas as pd
import numpy as np
import datetime
import math
import time
import json

def get_tradeable_symbols():
    symList = []
    symbols = session.query_symbol()
    if "ret_msg" in symbols.keys():
        if symbols["ret_msg"] == "OK":
            symbols = symbols["result"]
    for i in symbols:                               # maker fee 0 dan küçülk olmalı
        if i["quote_currency"] == "USDT" and float(i["maker_fee"]) < 1 and i["status"] == "Trading":
            symList.append(i)
    return symList

def store_price_history(symbols):
    """
    Store price history for all available pairs.
    """
    counts = 0
    priceHistoryDict = {}

    for i in symbols:
        symbolName = i["name"]
        priceHistory = get_price_klines(symbolName)
        if len(priceHistory) > 0:
            priceHistoryDict[symbolName] = priceHistory
            counts += 1
            print(f"{counts} item stored")
        else:
            print("Item not stored")
    if len(priceHistoryDict) > 0:
        with open("../Data/1_price_list.json", "w") as fp:
            json.dump(priceHistoryDict,fp,indent=4)
        print("Prices saved successfully.")
    return



def get_price_klines(symbol):
    timeStartDate = 0
    if timeFrame == 60:
        timeStartDate = datetime.datetime.now() - datetime.timedelta(hours=klineLimit)
    if timeFrame == "D":
        timeStartDate = datetime.datetime.now() - datetime.timedelta(days=klineLimit)
    if timeFrame == 15:
        timeStartDate = datetime.datetime.now() - datetime.timedelta(minutes=(klineLimit*timeFrame))
    timeStartSeconts = int(timeStartDate.timestamp())

    prices = session.query_mark_price_kline(symbol=symbol,interval=timeFrame,limit=klineLimit,from_time=timeStartSeconts)
    time.sleep(0.1)
    if len(prices["result"]) != klineLimit:
        return []
    return prices["result"]

def get_cointegrated_pairs(prices):

    # loop through and check for co-integration
    cointPairList = []
    includedList = []
    for sym1 in prices.keys():  # Keys is coins

        # Check each coin against the first
        for sym2 in prices.keys():
            if sym1 != sym2:

                # get unique combination id and ensure one
                sortedCharacters = sorted([sym1,sym2])
                unique = "".join(sortedCharacters)
                if unique in includedList:
                    break

                # Get close prices
                series1 = extract_close_prices(prices[sym1])
                series2 = extract_close_prices(prices[sym2])


                # Check for cointegration and add cointegrated pair
                cointFlag,pValue,tValue,cValue,hedgeRatio,zeroCrossings = calculate_cointegration(series1,series2)
                if cointFlag == 1:
                    includedList.append(unique)
                    cointPairList.append({
                        "sym1" : sym1,
                        "sym2" : sym2,
                        "pValue" : pValue,
                        "tValue" : tValue,
                        "cValue" : cValue,
                        "hedgeRatio" : hedgeRatio,
                        "zeroCrossings" : zeroCrossings
                    })
    dfCoint = pd.DataFrame(cointPairList)
    dfCoint = dfCoint.sort_values("zeroCrossings",ascending=False)
    dfCoint.to_csv("../Data/2_cointegrated_pairs.csv")
    return dfCoint

def extract_close_prices(prices):

    # Put close prices into a list
    closePrice = []
    for i in prices:
        if math.isnan(i["close"]):
            return []
        closePrice.append(i["close"])
    return closePrice

def calculate_spread(series1,series2,hedge_ratio):
    spread = pd.Series(series1) - (pd.Series(series2) * hedge_ratio)
    return spread

def calculate_cointegration(series1,series2):
    cointFlag = 0
    cointResault = coint(series1,series2)
    cointT = cointResault[0]
    pValue = cointResault[1]
    criticalValue = cointResault[2][1]
    model = sm.OLS(series1,series2).fit()
    hedgeRatio = model.params[0]
    spread = calculate_spread(series1,series2,hedgeRatio)
    zeroCrossings = len(np.where(np.diff(np.sign(spread)))[0])
    if pValue < 0.5 and cointT < criticalValue:
        cointFlag = 1
    return (cointFlag, round(pValue,2), round(cointT,2), round(criticalValue,2), round(hedgeRatio,2),zeroCrossings)

def plot_trends(sym1,sym2,priceData):

    # Extract Prices
    price1 = extract_close_prices(priceData[sym1])
    price2 = extract_close_prices(priceData[sym2])

    # Get spread and zscore
    cointFlag, pValue, tValue, cValue, hedgeRatio, zeroCrossings = calculate_cointegration(price1, price2)
    spread = calculate_spread(price1,price2,hedgeRatio)
    zScore = calculate_zscore(spread)

    # Calculate percentage chances
    df = pd.DataFrame(columns=[sym1,sym2])
    df[sym1] = price1
    df[sym2] = price2
    df[f"{sym1}_pct"] = df[sym1] / price1[0]
    df[f"{sym2}_pct"] = df[sym2] / price2[0]
    series1 = df[f"{sym1}_pct"].astype(float).values
    series2 = df[f"{sym2}_pct"].astype(float).values

    # Save results for bactesting
    df2 = pd.DataFrame()
    df2[sym1] = price1
    df2[sym2] = price2
    df2["spread"] = spread
    df2["zscore"] = zScore
    # df2.sort_values("spread", inplace=True)
    df2.to_csv("../Data/3_backtest_file.csv")
    print("File for backtesting saved.")

    # Plot Charts
    plt.subplot(3,1,1)
    plt.plot(series1,color="blue")
    plt.subplot(3,1,1)
    plt.plot(series2,color="orange")
    plt.subplot(3,1,2)
    plt.plot(spread,color="blue")
    plt.subplot(3,1,3)
    plt.plot(zScore,color="blue")
    plt.suptitle(f"Price and Spread - {sym1} - {sym2} ")
    plt.show()


def calculate_zscore(spread):
    df   = pd.DataFrame(spread)
    mean = df.rolling(center=False, window= zScoreWindow).mean()
    std  = df.rolling(center=False, window= zScoreWindow).std()
    x    = df.rolling(center=False, window=1).mean()
    df["ZScore"] = (x - mean ) / std
    return df["ZScore"].astype(float).values