""""
    API Documentation
    https://bybit-exchange.github.io/docs/futuresV2/inverse/#t-introduction
"""
# API Imports
from pybit import HTTP
from pybit import usdt_perpetual

mode = "test"
ticker1 = "BTCUSDT"
ticker2 = "ETHUSDT"
signalPositiveTicker = ticker2
signalNegativeTicker = ticker1
roundingTicker1 = 2
roundingTicker2 = 2
quantityRoundingTicker1 = 3
quantityRoundingTicker2 = 2

profitTargetDolar = 2
closePositionByZScore = False
limitOrderBasis = False # Will ensure positions (except for close) will be placed on limit basis

tradeableCapitalUSDT = 100
stopLossFail = 0.15
signalTriggerThresh = 0.01 # Z-Scrore threshold which determines trade

timeFrame = 15
klineLimit = 200
zScoreWindow = 21

# Real API
apiKeyMainnet = "5juBoJfx8l4ncPUcjS"
apiSecretMainnet = "OB5E6l6Ygg9mz7CCCW46ZmAOcJbsFpPpFAH8"

# Testnet API
apiKeyTest = "GEPdgTBY2vcM6Uni64"
apiSecretTest = "CGF0BqYDhjf6guutXJegQPVBFfyAYUInLqqB"

# Select API
apiKey =  apiKeyMainnet if mode == "Real" else apiKeyTest
apiSecret =  apiSecretMainnet if mode == "Real" else apiSecretTest

# Select URL
apiUrl =  "https://api.bybit.com" if mode == "Real" else "https://api-testnet.bybit.com"
wsPublicURL = "wss://stream-testnet.bybit.com/realtime" if mode == "test" else "wss://stream.bybit.com/realtime"

# Session Activation
sessionPublic = HTTP(apiUrl)
sessionPrivate = HTTP(apiUrl,api_key=apiKey,api_secret=apiSecret)
session_auth = usdt_perpetual.HTTP(endpoint=apiUrl,api_secret=apiSecret,api_key=apiKey)