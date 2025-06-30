import json
import warnings
import pandas as pd
from func_strategy import *

warnings.simplefilter(action="ignore",category=FutureWarning)


if __name__ == "__main__":

    # # Step 1 - Get list of symbols
    # print("Getting Symbols...")
    # symResponse = get_tradeable_symbols()
    #
    # # Step 2 - Construct and save price history
    # print("Constructing and savig price data to JSON...")
    # if len(symResponse) > 0:
    #     store_price_history(symResponse)

    # # # Step 3 - Find cointegrated pairs
    # print("Calculating co-integrated...")
    # with open("../Data/1_price_list.json") as jfile:
    #     priceData = json.load(jfile)
    #     if len(priceData) > 0:
    #         cointPairs = get_cointegrated_pairs(priceData)

    # Step 4 - Plot trends and save for backtesting
    print("Plotting trends...")
    sym1 = "BTCUSDT"
    sym2 = "ETHUSDT"
    with open("../Data/1_price_list.json") as js:
        priceData = json.load(js)
        if len(priceData) > 0:
            plot_trends(sym1,sym2,priceData)






