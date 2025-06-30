""""
    API Documentation
    https://bybit-exchange.github.io/docs/futuresV2/inverse/#t-introduction
"""

# API Imports
from pybit import HTTP
from pybit import inverse_perpetual
from time import sleep


# Config
mode = "Test"
timeFrame = 15
klineLimit = 200
zScoreWindow = 21

# Real API
apiKeyMainnet = ""
apiSecretMainnet = ""

# Testnet API
apiKeyTest = "GEPdgTBY2vcM6Uni64"
apiSecretTest = "CGF0BqYDhjf6guutXJegQPVBFfyAYUInLqqB"

# Select API
apiKey =  apiKeyMainnet if mode == "Real" else apiKeyTest
apiSecret =  apiSecretMainnet if mode == "Real" else apiSecretTest

# Select URL
apiUrl =  "https://api.bybit.com" if mode == "Real" else "https://api-testnet.bybit.com"

# Session Activation
session = HTTP(apiUrl)

# Web Socket Connectiond
ws = inverse_perpetual.WebSocket(test=True, ping_interval = 30 , ping_timeout = 10, domain = "bybit")


def handleMesaage(msg):
    print(msg)

# ws.kline_stream(handleMesaage,"BTCUSD","D")
# while True:
#     sleep(5)
