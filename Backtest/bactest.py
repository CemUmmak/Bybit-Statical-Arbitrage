import time

import pandas as pd

df = pd.read_csv("../Data/3_backtest_file.csv")
df.drop("Unnamed: 0",axis=1, inplace = True)
df.dropna(inplace=True)

print(df.head)

buytQty = 0
sellQty = 0
positive = False
negative = False
result = []

for i in df.values:
    if abs(i[3]) > 1:
        if i[3] > 0 and not positive and not negative:
            buytQty = 100 / i[0]
            sellQty = 100 / i[1]
            positive = True
        if i[3] < 0 and not positive and not negative:
            buytQty = 100 / i[0]
            sellQty = 100 / i[1]
            negative = True
        if positive:
            if i[3] < 0:
                resultBuy = buytQty * i[0]
                resultSell = sellQty *  i[1]
                result.append([resultBuy,resultSell,(resultBuy - resultSell)])
                positive = False
        if negative:
            if i[3] > 0:
                resultBuy = buytQty * i[0]
                resultSell = sellQty *  i[1]
                result.append([resultBuy,resultSell,(resultBuy - resultSell)])
                negative = False


for i in result:
    print(i)