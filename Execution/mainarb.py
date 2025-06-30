from func_execution import *

#Initialise variables

statusDict = {"message" : "Starting"}
orderLong = {}
orderShort = {}
signalSignPositive = False
killSwitch = 0
signalSide = ""
firstStart = True
zScore = 0
pnl = 0
spread = 0
# Save status
save_status(statusDict)

# Set leverage in cafe forgotten to do so on the platform
print("Setting leverage")
set_leverage(ticker1)
set_leverage(ticker2)

# Commence bot
print("Seeking trades")

while True:
    # Pause -protect API
    time.sleep(5)
    message = ""
    # Check for signal and place new trades
    try:
        if killSwitch == 0:
            pTickerOpen = open_position_confirmation(signalPositiveTicker)
            nTickerOpen = open_position_confirmation(signalNegativeTicker)
            checksAll = [pTickerOpen, nTickerOpen]
            isManageNewTrades = not any(checksAll)
            # Save Status
            statusDict["message"] = "Intial checks made..."
            statusDict["checks"] = checksAll
            save_status(statusDict)
            if isManageNewTrades:
                statusDict["message"] = "Managing new trades..."
                save_status(statusDict)
                killSwitch,signalSide = manage_new_trades(killSwitch,firstStart)
            else:
                killSwitch = 1

        # Managig open kill switch if positions chance or should reach 2
        # Check for signal to be false
        if killSwitch == 1:
            # Get and save the lastest z-score
            timeChance15 = minute_is_chance(0,[0,15,30,45])
            timeChance1  = minute_is_chance(1)
            if timeChance1:
                pnl = get_unrelized_pnl()
                print("PNL", pnl)
            if timeChance15:
                zScore, signalSinPositive,spread = get_latest_zscrore()
                print("Z-Score = ", zScore," PNL : ",pnl)
            if ((zScore != 0 and (signalSide == "positive" and zScore < 0) or (signalSide == "negative" and zScore > 0))):
                killSwitch = 2
                message = f"Orders closed by Z-Score.\n\nPNL : {pnl} Without commission."
            elif (pnl != 0 and pnl > profitTargetDolar):
                killSwitch = 2
                message = f"Orders closed by profit target : {profitTargetDolar}.\n\nPNL : {pnl} Without commission."
            else:
                time.sleep(10)

        # Close all active orders and positions
        if killSwitch == 2:
            print("Closing all positions.")
            statusDict["message"] = "Closing existing trades..."
            save_status(statusDict)
            killSwitch = close_all_position(killSwitch)
            time.sleep(5)
            killSwitch = 0

        if message != "":
            send_telegram(message, "5554:AAH2NZ_yASpKw",
                          "-10005", True)
        firstStart = False
    except Exception as exc:
        print(exc)
        send_telegram(f"İstasitiksel Arbitraj'da hata! \n\n --- Hata Kodu ---\n\n{exc}", "557317535_yASpKw",
                      "-1005505", True)
        time.sleep(10)