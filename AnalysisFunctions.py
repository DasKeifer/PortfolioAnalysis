import os
import pandas as pd 
import datetime
import SimFunctions as sf
import Utils as utils
import math
import time
    
def read(path, fileName):
    return utils.convertToDateTimeDate(pd.read_csv(os.path.join(path, fileName) + ".csv", index_col=0, header=0).squeeze("columns"))

def determineContributionDates(data, startDate, frequency=14):
    found = data[startDate:]
    nextBiweeklyDate = datetime.datetime.strptime(startDate, "%Y-%m-%d") + datetime.timedelta(days=frequency)
    for date,_ in found.items():
        dateTime = datetime.datetime.strptime(date, "%Y-%m-%d")
        if (dateTime - nextBiweeklyDate).days >= 0:
            found.at[date] = True
            nextBiweeklyDate = nextBiweeklyDate + datetime.timedelta(days=14)
        else:
            found.at[date] = False
    return found

def percentChanges(prices):
    tmp = (1 + prices.pct_change(1))
    tmp[0] = 1
    return tmp

def drawdown(prices):
    rets = sf.returns(prices)
    return (rets.div(rets.cummax()) - 1) * 100

def cagr(prices):
    delta = (prices.index[-1] - prices.index[0]).days / 365.25
    return ((prices[-1] / prices[0]) ** (1 / delta) - 1) * 100


def percentageBased(stockData, portfolio, doRebalances=True, investMethod="target",\
                    startingBalance=100000, periodicDeposit=0, depositInterval=14,\
                    startDate=datetime.date(2005, 1, 28), endDate=datetime.date(2023, 2, 3)):
    
    if len(portfolio) <= 1:
        doRebalances = False
        
    value = {'total':pd.Series(dtype="float64"), 'totalReturns':pd.Series(dtype="float64"), \
             'params':(portfolio, startingBalance, startDate, endDate, periodicDeposit, depositInterval)}
    
    value['total'].at[startDate] = startingBalance
    nextInvestDate = startDate + datetime.timedelta(days=depositInterval)
        
    rebalanceColumns = []
    balances = {}  
    for _,stock in enumerate(portfolio):
        if "startPercent" in stock.keys():
            stock["targetPercent"] = stock["startPercent"]
        balances[stock["ticker"]] = startingBalance * stock["targetPercent"]
        rebalanceColumns.append(stock["ticker"])
    
    rebalanceColumns.append("date")
    for _,stock in enumerate(portfolio):
        rebalanceColumns.append("post " + stock["ticker"])
        
    value['rebalances'] = pd.DataFrame(columns=rebalanceColumns)
    
    previousDate = startDate
    for date,_ in stockData["spy"][startDate:endDate].items():
        # Update the value and determine total value
        totalValue = 0      
        for _,stock in enumerate(portfolio):
            balances[stock["ticker"]] = balances[stock["ticker"]] * stockData[stock["ticker"]][date]
            totalValue += balances[stock["ticker"]]
        value["total"].at[date] = totalValue
        value["totalReturns"].at[date] = value["total"][date] / value["total"][previousDate] - 1
        
        # See if we need to rebalance
        rebalance = False
        rebalanceRow = []
        if doRebalances:
            for _,stock in enumerate(portfolio):
                rebalanceRow.append(balances[stock["ticker"]] / totalValue)
                if (rebalanceRow[-1] > (stock["targetPercent"] + stock["maxIncrease"]) or
                    rebalanceRow[-1] < (stock["targetPercent"] - stock["maxDecrease"])):
                        rebalance = True
        
        # Check for periodic investments
        if periodicDeposit > 0 and (date - nextInvestDate).days >= 0:
            nextInvestDate = nextInvestDate + datetime.timedelta(days=depositInterval)
            if investMethod == "target":
                for _,stock in enumerate(portfolio):
                    balances[stock["ticker"]] += periodicDeposit * stock["targetPercent"]
            elif investMethod == "current":
                for _,stock in enumerate(portfolio):
                    balances[stock["ticker"]] += periodicDeposit * balances[stock["ticker"]] / totalValue
            else:
                print("Failed rebalance!")
                
            value["total"].at[date] += periodicDeposit 
            
        # Rebalance if needed
        if rebalance:
            preRebalance = totalValue
            postRebalance = 0
            # for 3 if one is near, either neither of the other are or one is near the other end
            '''delta = {}
            unchanged = []
            if "increment" in stock.keys():
                netDelta = 0
                for i,stock in enumerate(portfolio):
                    if rebalanceRow[i] > (stock["targetPercent"] + stock["maxIncrease"] - stock["rebalanceTolerance"]):
                        print("over", stock["ticker"], rebalanceRow[i])
                        if stock["targetPercent"] < stock["maxTarget"]:
                            delta[stock["ticker"]] = stock["increment"]
                            if delta[stock["ticker"]] + stock["targetPercent"] > stock["maxTarget"]:
                                delta[stock["ticker"]] = stock["maxTarget"] - stock["targetPercent"]
                            netDelta -= delta[stock["ticker"]]
                        else:
                            delta[stock["ticker"]] = 0
                        
                    elif rebalanceRow[i] < (stock["targetPercent"] - stock["maxDecrease"] + stock["rebalanceTolerance"]):
                        print("under", stock["ticker"], rebalanceRow[i])
                        if stock["targetPercent"] > stock["minTarget"]:
                            delta[stock["ticker"]] = -stock["increment"]
                            if delta[stock["ticker"]] + stock["targetPercent"] < stock["minTarget"]:
                                delta[stock["ticker"]] = stock["minTarget"] - stock["targetPercent"]
                            netDelta -= delta[stock["ticker"]]
                        else:
                            delta[stock["ticker"]] = 0
                    else:
                        print("unchanged", stock["ticker"], rebalanceRow[i])
                        unchanged.append(stock)
                
                #nonCloseDelta = {}
                print(netDelta)
                if netDelta == 0:
                    for i,stock in enumerate(unchanged):
                        delta[stock["ticker"]] = 0
                else:
                    balancing = True
                    tmpDelta = {}
                    while balancing:
                        tmpDelta = {}
                        balancing = False
                        for i,stock in enumerate(unchanged):
                            tmpDelta[stock["ticker"]] = netDelta / len(unchanged)
                            tmpTarget = stock["targetPercent"] + tmpDelta[stock["ticker"]]
                            if tmpTarget < stock["minTarget"]:
                                delta[stock["ticker"]] = stock["minTarget"] - stock["targetPercent"]
                                netDelta -= delta[stock["ticker"]]
                                del unchanged[i]
                                balancing = True
                                print(stock["ticker"],"mined",delta[stock["ticker"]])
                            elif tmpTarget > stock["maxTarget"]:
                                delta[stock["ticker"]] = stock["maxTarget"] - stock["targetPercent"]
                                netDelta -= delta[stock["ticker"]]
                                del unchanged[i]
                                balancing = True
                                print(stock["ticker"],"maxed",delta[stock["ticker"]])
                    for ticker, delt in tmpDelta.items():
                        print(ticker, "inbetween", delt)
                        netDelta -= delt
                        delta[ticker] = delt
                print(netDelta)
                          
                if netDelta > 1e-12:
                    print("------------------ Need more work! -------------------")
                          
                for _,stock in enumerate(portfolio):
                    fromTarget = stock["targetPercent"]
                    stock["targetPercent"] += delta[stock["ticker"]]
                    print("adjusted", stock["ticker"], fromTarget, "to", stock["targetPercent"])
                  '''
            if "maxRebalance" in next(iter(portfolio)):
                #print("--- rebalance ---")
                unbalanced = []
                unbalancedCurrTotal = 0
                unaccountedPercentage = 1
                for i,stock in enumerate(portfolio):
                    if "forceMinRebalance" in stock:
                        if rebalanceRow[i] < stock["forceMinRebalance"]:
                            #print('fm', stock["ticker"],  rebalanceRow[i], stock["forceMinRebalance"])
                            balances[stock["ticker"]] = totalValue * stock["forceMinRebalance"]
                            unaccountedPercentage -= stock["forceMinRebalance"]
                        else:
                            #print('fm', stock["ticker"],  rebalanceRow[i],  rebalanceRow[i])
                            unaccountedPercentage -= rebalanceRow[i]
                    elif "forceRebalance" in stock:
                        #print('f', stock["ticker"],  rebalanceRow[i], stock["forceRebalance"])
                        balances[stock["ticker"]] = totalValue * stock["forceRebalance"]
                        unaccountedPercentage -= stock["forceRebalance"]
                    elif rebalanceRow[i] > (stock["targetPercent"] + stock["maxIncrease"]):
                        #print('max', stock["ticker"],  rebalanceRow[i], stock["maxRebalance"])
                        balances[stock["ticker"]] = totalValue * stock["maxRebalance"]
                        unaccountedPercentage -= stock["maxRebalance"]
                    elif rebalanceRow[i] < (stock["targetPercent"] - stock["maxDecrease"]):
                        #print('min', stock["ticker"],  rebalanceRow[i], stock["minRebalance"])
                        balances[stock["ticker"]] = totalValue * stock["minRebalance"]
                        unaccountedPercentage -= stock["minRebalance"]
                    else:
                        #print('u', stock["ticker"],  rebalanceRow[i])
                        unbalanced.append(stock)
                        unbalancedCurrTotal += balances[stock["ticker"]]
                        postRebalance -= balances[stock["ticker"]]
                        
                    postRebalance +=balances[stock["ticker"]]
                    
                leftPercentage = unaccountedPercentage
                #print("left",   unaccountedPercentage)          
                for stock in unbalanced:
                    targetPercentage = balances[stock["ticker"]] / unbalancedCurrTotal * leftPercentage
                    #print('u', stock["ticker"],  targetPercentage)
                    balances[stock["ticker"]] = totalValue * targetPercentage
                    unaccountedPercentage -= targetPercentage
                    postRebalance +=balances[stock["ticker"]]
                
                if unaccountedPercentage > 1e-12:
                    print(" ")
                    print(" ")
                    print("----------ERROR-----------", unaccountedPercentage)
                    print(" ")
                    print(" ")
                    
            else:
                for i,stock in enumerate(portfolio):
                    balances[stock["ticker"]] = totalValue * stock["targetPercent"]
                    postRebalance += balances[stock["ticker"]]
            rebalanceRow.append(date)
            for i,stock in enumerate(portfolio):
                rebalanceRow.append(balances[stock["ticker"]] / totalValue)
            value["rebalances"].loc[len(value["rebalances"])] = rebalanceRow
            
        
            if (preRebalance - postRebalance) > 0.01:
                print("-------------- REBALANCE ERROR -----------", preRebalance, postRebalance)
        previousDate = date
    value["endingBalances"] = balances
    value["endingPercentages"] = {}
    for i,stock in enumerate(portfolio):
        value["endingPercentages"][stock["ticker"]] = balances[stock["ticker"]] / value['total'][-1]
        
    return postAnalysis(value)

def sellStock(ticker, amount, date, totalStocks, purchases, priceData, gains, fifo):
    toSell = amount / priceData[ticker][date]
    totalStocks[ticker] -= toSell
    while toSell > 0:
        if fifo:
            purchase = purchases[ticker].pop(0)
        else:
            purchase = purchases[ticker].pop()
            
        # Determine how much to sell
        leftover = 0
        sold = purchase[1]
        if purchase[1] > toSell:
            leftover = purchase[1] - toSell
            sold = toSell
        toSell -= sold
            
        # Determine gains
        if not (date.year in gains.index):
            gains.loc[date.year] = [0,0]
            
        sellGains = sold * (priceData[ticker][date] - priceData[ticker][purchase[0]])
        if (date - purchase[0]).days > 365.25:
            gains.at[date.year, "long term"] = gains.at[date.year, "long term"] + sellGains
        else:
            gains.at[date.year, "short term"] = gains.at[date.year, "short term"] + sellGains
            #print(ticker, "short gains", sellGains, "from", purchase[0], "on", date)
       # print(ticker, "selling with gains", sellGains, "from", purchase[0], "on", date)
        # add any leftover back in
        if leftover > 0:       
            if fifo:
                purchases[ticker].insert(0, [purchase[0], leftover])
            else:
                purchases[ticker].append([purchase[0], leftover])
    #print("----------")
    #print("sell", ticker, amount, amount / priceData[ticker][date])
    #print(">", purchases)
    
def buyStock(ticker, amount, date, totalStocks, purchases, priceData):
    quantity = amount / priceData[ticker][date]
    purchases[ticker].append([date, quantity])
    totalStocks[ticker] += quantity
    #print(ticker, "buying now on ", date)
    #print("----------")
    #print("buy", ticker, amount, quantity)
    #print(">", purchases)

def percentageBased2(stockData, portfolio, doRebalances=True,\
                    startingBalance=100000, periodicDeposit=0, depositInterval=14,\
                    taxable=False, ltTax = .2875, stTax = .4075, fifo=True,\
                    startDate=datetime.date(2005, 1, 28), endDate=datetime.date(2023, 2, 3)):
    print(portfolio, doRebalances, startingBalance, periodicDeposit, depositInterval,\
                    taxable, ltTax, stTax, fifo, startDate, endDate)
    
    if len(portfolio) <= 1:
        doRebalances = False
    
    purchases = {}  
    totalStocks = {}        
    nextInvestDate = startDate + datetime.timedelta(days=depositInterval)
    previousDate = startDate
    
    value = {'total':pd.Series(dtype="float64"), 'totalReturns':pd.Series(dtype="float64"), \
             'params':(portfolio, startingBalance, startDate, endDate, periodicDeposit, depositInterval)}
    
    value['total'].at[startDate] = startingBalance
    value['yearlyGains'] = pd.DataFrame(columns=["short term", "long term"])
     
    rebalanceColumns = []
    for _,stock in enumerate(portfolio):
        if "startPercent" in stock.keys():
            stock["targetPercent"] = stock["startPercent"]
        purchases[stock["ticker"]] = []
        totalStocks[stock["ticker"]] = 0
        buyStock(stock["ticker"], startingBalance * stock["targetPercent"], startDate, totalStocks, purchases, stockData)
        rebalanceColumns.append(stock["ticker"])
    rebalanceColumns.append("date")
    
    for _,stock in enumerate(portfolio):
        rebalanceColumns.append(stock["ticker"])
    value['rebalances'] = pd.DataFrame(columns=rebalanceColumns)
    
    for date,_ in stockData["spy"][startDate:endDate].items():
        
        # Update the value and determine total value
        totalValue = 0
        for _,stock in enumerate(portfolio):
            totalValue += totalStocks[stock["ticker"]] * stockData[stock["ticker"]][date]
        value["total"].at[date] = totalValue
        value["totalReturns"].at[date] = value["total"][date] / value["total"][previousDate] - 1
        
        periodicInvest = periodicDeposit > 0 and (date - nextInvestDate).days >= 0
        rebalance = False
        rebalanceRow = []
        
        # See if we need to rebalance
        if doRebalances:
            for _,stock in enumerate(portfolio):
                rebalanceRow.append(totalStocks[stock["ticker"]] * stockData[stock["ticker"]][date] / totalValue)
                if (rebalanceRow[-1] > (stock["targetPercent"] + stock["maxIncrease"]) or
                    rebalanceRow[-1] < (stock["targetPercent"] - stock["maxDecrease"])):
                        rebalance = True
                        
        if rebalance:
            #print("------ rebalance -----", date)
            if periodicInvest:
                nextInvestDate = nextInvestDate + datetime.timedelta(days=depositInterval)
                totalValue += periodicDeposit
                
            if "maxRebalance" in next(iter(portfolio)):
                unbalanced = []
                unbalancedCurrTotal = 0
                unaccountedPercentage = 1
                for i,stock in enumerate(portfolio):
                    targetValue = 0
                    if "forceMinRebalance" in stock:
                        if rebalanceRow[i] < stock["forceMinRebalance"]:
                            #print('fm', stock["ticker"],  rebalanceRow[i], stock["forceMinRebalance"])
                            targetValue = totalValue * stock["forceMinRebalance"]
                            unaccountedPercentage -= stock["forceMinRebalance"]
                        else:
                            #print('fm', stock["ticker"],  rebalanceRow[i],  rebalanceRow[i])
                            unaccountedPercentage -= rebalanceRow[i]
                    elif "forceRebalance" in stock:
                        #print('f', stock["ticker"],  rebalanceRow[i], stock["forceRebalance"])
                        targetValue = totalValue * stock["forceRebalance"]
                        unaccountedPercentage -= stock["forceRebalance"]
                    elif rebalanceRow[i] > (stock["targetPercent"] + stock["maxIncrease"]):
                        #print('max', stock["ticker"],  rebalanceRow[i], stock["maxRebalance"])
                        targetValue = totalValue * stock["maxRebalance"]
                        unaccountedPercentage -= stock["maxRebalance"]
                    elif rebalanceRow[i] < (stock["targetPercent"] - stock["maxDecrease"]):
                        #print('min', stock["ticker"],  rebalanceRow[i], stock["minRebalance"])
                        targetValue = totalValue * stock["minRebalance"]
                        unaccountedPercentage -= stock["minRebalance"]
                    else:
                        #print('u', stock["ticker"], rebalanceRow[i])
                        unbalanced.append(stock)
                        unbalancedCurrTotal += totalStocks[stock["ticker"]] * stockData[stock["ticker"]][date]
                        
                    if targetValue > 0:
                        currentValue = totalStocks[stock["ticker"]] * stockData[stock["ticker"]][date]
                        diff = currentValue - targetValue
                        #print(stock["ticker"], currentValue, targetValue, diff)
                        if diff > 0:
                            sellStock(stock["ticker"], diff, date, totalStocks, purchases, stockData, value['yearlyGains'], fifo)
                        elif diff < 0:
                            buyStock(stock["ticker"], abs(diff), date, totalStocks, purchases, stockData)
                
                leftPercentage = unaccountedPercentage
                #print("left",   unaccountedPercentage)          
                for stock in unbalanced:
                    currentValue = totalStocks[stock["ticker"]] * stockData[stock["ticker"]][date]
                    targetPercentage = currentValue / unbalancedCurrTotal * leftPercentage
                    targetValue = totalValue * targetPercentage
                    diff = currentValue - targetValue
                    #print('u', stock["ticker"],  targetPercentage)
                    #print(stock["ticker"], currentValue, targetValue, diff)
                    if diff > 0:
                        sellStock(stock["ticker"], diff, date, totalStocks, purchases, stockData, value['yearlyGains'], fifo)
                    elif diff < 0:
                        buyStock(stock["ticker"], abs(diff), date, totalStocks, purchases, stockData)
                    unaccountedPercentage -= targetPercentage
                
                if unaccountedPercentage > 1e-12:
                    print(" ")
                    print(" ")
                    print("----------ERROR-----------", unaccountedPercentage)
                    print(" ")
                    print(" ")
                    
            else:         
                for _,stock in enumerate(portfolio):
                    currentValue = totalStocks[stock["ticker"]] * stockData[stock["ticker"]][date]
                    targetValue = totalValue * stock["targetPercent"]
                    diff = currentValue - targetValue 
                    #print(stock["ticker"], currentValue, targetValue, diff)
                    if diff > 0:
                        sellStock(stock["ticker"], diff, date, totalStocks, purchases, stockData, value['yearlyGains'], fifo)
                    elif diff < 0:
                        buyStock(stock["ticker"], abs(diff), date, totalStocks, purchases, stockData)
                    
            rebalanceRow.append(date)
            for i,stock in enumerate(portfolio):
                rebalanceRow.append(totalStocks[stock["ticker"]] * stockData[stock["ticker"]][date] / totalValue)
            value["rebalances"].loc[len(value["rebalances"])] = rebalanceRow
            #print(rebalanceRow)
                
        elif periodicInvest:
            nextInvestDate = nextInvestDate + datetime.timedelta(days=depositInterval)
            for _,stock in enumerate(portfolio):
                buyStock(stock["ticker"], periodicDeposit * stock["targetPercent"], date, totalStocks, purchases, stockData)
                
        if taxable:
            # Time for taxes! Oh boy!
            if date.month == 4 and previousDate.month == 3:
                if (date.year - 1 in value['yearlyGains'].index):
                    
                    yearlyGains = value['yearlyGains'].loc[date.year - 1]
                    totalGains = yearlyGains[0] + yearlyGains[1]
                    #print("------ Taxes -----", date)
                    if totalGains < 0:
                        toBuy = abs(totalGains)
                        if toBuy > 3000:
                            if not (date.year in value['yearlyGains'].index):
                                value['yearlyGains'].loc[date.year] = [0, 3000 - toBuy]
                            else:
                                value['yearlyGains'].at[date.year, "long term"] = value['yearlyGains'].at[date.year, "long term"] + 3000 - toBuy
                            toBuy = 3000
                        #print("buying", toBuy * stTax, "rolling",value['yearlyGains'].at[date.year, "long term"])
                        for _,stock in enumerate(portfolio):
                            buyStock(stock["ticker"], toBuy * stTax * stock["targetPercent"], date, totalStocks, purchases, stockData)
                    else:
                        taxes = yearlyGains[0] * stTax + yearlyGains[1] * ltTax
                        if yearlyGains[0] < 0:
                            taxes = totalGains * ltTax
                        elif yearlyGains[1] < 0:
                            taxes = totalGains * stTax
                        #print("selling", taxes, yearlyGains)
                        for _,stock in enumerate(portfolio):
                            sellStock(stock["ticker"], taxes * stock["targetPercent"], date, totalStocks, purchases, stockData, value['yearlyGains'], fifo)
            
        previousDate = date
        
    totalValue = 0
    for _,stock in enumerate(portfolio):
        for _,purch in enumerate(purchases[stock["ticker"]]):
            totalValue += stockData[stock["ticker"]][purch[0]] * purch[1]
    value["equity"] = totalValue
    
    return postAnalysis(value)
        
    
def percentageBasedReserves(stockData, portfolio, \
                            reserveTarget=.15, reserveTolerance = 0.03,\
                            reserveDrawDownTrigger=.15, reserveUpTrigger=0, reserveDailyGrowth=0.00008, \
                            reserveSteps=3, reservePercentage=0,\
                            startingBalance=100000, periodicDeposit=0, depositInterval=14,\
                            startDate=datetime.date(2005, 1, 28), endDate=datetime.date(2023, 2, 3)):
    
    value = {'total':pd.Series(dtype="float64"), 'totalReturns':pd.Series(dtype="float64"), 'drawdown':pd.Series(dtype="float64"),\
             'params':(portfolio, reserveTarget, reserveTolerance, reserveDrawDownTrigger, reserveDailyGrowth, reserveSteps, reservePercentage, startingBalance, startDate, endDate, periodicDeposit, depositInterval)}
    
    value['total'].at[startDate] = startingBalance
    nextInvestDate = startDate + datetime.timedelta(days=depositInterval)
     
    rebalanceColumns = []
    balances = {}  
    cumBal = {}  
    cum_max = {}
    for _,stock in enumerate(portfolio):
        balances[stock["ticker"]] = startingBalance * stock["targetPercent"]
        cumBal[stock["ticker"]] = startingBalance * stock["targetPercent"]
        cum_max[stock["ticker"]] = stock["targetPercent"]
        rebalanceColumns.append(stock["ticker"])
        
    balances["reserve"] = startingBalance * reserveTarget
    reserveInfo = []
    reserveDDTarget = reserveDrawDownTrigger
    reserveStepsLeft = reserveSteps
        
    rebalanceColumns.append("date")
    value['rebalances'] = pd.DataFrame(columns=rebalanceColumns)
    value['reserves'] = pd.DataFrame(columns=rebalanceColumns)
    
    previousDate = startDate
    for date,_ in stockData["spy"][startDate:endDate].items():
        
        # Update the value and determine total value
        balances["reserve"] = balances["reserve"] * (1 + reserveDailyGrowth)
        totalValue = balances["reserve"]
        
        for _,stock in enumerate(portfolio):
            balances[stock["ticker"]] = balances[stock["ticker"]] * stockData[stock["ticker"]][date]
            cumBal[stock["ticker"]] = cumBal[stock["ticker"]] * stockData[stock["ticker"]][date]
            totalValue += balances[stock["ticker"]]
            
            if cum_max[stock["ticker"]] < cumBal[stock["ticker"]]:
                cum_max[stock["ticker"]] = cumBal[stock["ticker"]]     
                
            drawdown = 1 - cumBal[stock["ticker"]] / cum_max[stock["ticker"]]
            #print(balances, cum_max[stock["ticker"]], cumBal[stock["ticker"]], drawdown, reserveDDTarget)
            if drawdown > reserveDDTarget:
                #trigger reserve investment
                if reserveSteps > 0:
                    if reserveStepsLeft > 0:
                        #print ("inevst!------", date)
                        percentDivest = (reserveSteps - reserveStepsLeft + 1)/reserveSteps
                        delta = percentDivest * balances["reserve"]
                        balances[stock["ticker"]] += delta
                        balances["reserve"] -= delta
                        
                        reserveInfo.append([cum_max[stock["ticker"]], delta])
                       # reserveInfo.append([cumBal[stock["ticker"]] * (1 + reserveDrawDownTrigger), delta])
                        reserveDDTarget += reserveDrawDownTrigger
                        reserveStepsLeft -= 1
                else: # todo percentage
                    #print ("inevst!------", date)
                    delta = reservePercentage * balances["reserve"]
                    balances[stock["ticker"]] += delta
                    balances["reserve"] -= delta
                    
                    reserveInfo.append([cumBal[stock["ticker"]] * (1 + reserveDrawDownTrigger), delta])
                    reserveDDTarget += reserveDrawDownTrigger
            else:
                for invest in list(reserveInfo):
                    if cumBal[stock["ticker"]] > invest[0]:
                        #print(invest, cumBal[stock["ticker"]])
                        #print ("divest!------", date)
                        delta = invest[1] * (1 + reserveDrawDownTrigger)
                        balances[stock["ticker"]] -= delta
                        balances["reserve"] += delta
                        
                        reserveInfo.remove(invest)
                        reserveDDTarget -= reserveDrawDownTrigger
                        reserveStepsLeft += 1
                
        value["total"].at[date] = totalValue
        value["totalReturns"].at[date] = value["total"][date] / value["total"][previousDate] - 1
        
        # See if we need to rebalance
        rebalance = False
        if len(reserveInfo) <= 0:
            if balances["reserve"] / totalValue < reserveTarget - reserveTolerance:
                rebalance = True
        
        # Check for periodic investments
        if (date - nextInvestDate).days >= 0:
            nextInvestDate = nextInvestDate + datetime.timedelta(days=depositInterval)
            for _,stock in enumerate(portfolio):
                balances[stock["ticker"]] += periodicDeposit * stock["targetPercent"]
            balances["reserve"] += periodicDeposit * reserveTarget
            
            value["total"].at[date] += periodicDeposit 
            
        # Rebalance if needed
        if rebalance:
            #print ("rebalance!------", date)
            for _,stock in enumerate(portfolio):
                balances[stock["ticker"]] = totalValue * stock["targetPercent"]
            balances["reserve"] = totalValue * reserveTarget
            
            value["rebalances"].loc[len(value["rebalances"])] = date
                
        # See if we dip into reserves
                
        previousDate = date
        
    return postAnalysis(value)    
    

def postAnalysis(results):
    results["cagr"] = cagr(results["total"])
    results["drawdown"] = drawdown(results["total"])
    results["drawdownMax"] = results["drawdown"].min()
    results["dailyReturnsPctAvg"] = results["totalReturns"].mean()
    results["dailyStddev"] = results["totalReturns"].std()
    results["sharpe"] = (results["dailyReturnsPctAvg"] - 0.000087) / results["dailyStddev"] * math.sqrt(252)
    
    return results                              
                                 
def slidingWindowAnalysis(fn, stockData,\
                    timeWindow=datetime.timedelta(3652.5), timeStep=datetime.timedelta(11),\
                    startDate=datetime.date(2005, 1, 28), endDate=datetime.date(2023, 2, 3),\
                    args=[]):
    results = pd.Series(dtype="float64")
    
    print("starting windowed analysis...", startDate, endDate, args)
    start = time.perf_counter()
    
    nextStart = startDate
    lastWindowedStart = endDate - timeWindow
    for date,_ in stockData["spy"][startDate:lastWindowedStart].items():
        if (nextStart - date).days <= 0:
            nextStart = date + timeStep
            results[date] = fn(stockData, *args, startDate=date, endDate=date + timeWindow)

    stop = time.perf_counter()
    print("Completed windowed analysis:", (stop - start))
    return results

def postAnalysisSlidingWindow(results, startDate=datetime.date(1992, 1, 2), endDate=datetime.date(2023, 2, 1)):
    summaries = pd.DataFrame(columns=["total", "cagr", "drawdownMax", "dailyStddev", "sharpe"])
    datedTotals = pd.Series(dtype="float64")
    for date, result in results.items():
        if date >= startDate and date <= endDate:
            summaries.loc[len(summaries)] = [result["total"][-1], result["cagr"], result["drawdownMax"], result["dailyStddev"], result["sharpe"]]
            datedTotals[result["total"].index[0]] = result["total"][-1]
    condensed = {"totals":datedTotals}
    
    for name, vals in summaries.items():
        condensed[name + "_avg"] = vals.mean()
        condensed[name + "_med"] = vals.median()
        condensed[name + "_stddev"] = vals.std()
        condensed[name + "_max"] = vals.max()
        condensed[name + "_min"] = vals.min()
        
    condensed["total_max_data"] = results[summaries.query('total == ' + str(condensed["total_max"])).index[0]]["total"]
    condensed["total_min_data"] = results[summaries.query('total == ' + str(condensed["total_min"])).index[0]]["total"]
    condensed["params"] = results[0]["params"]
    condensed["name"] = results.iloc[0]["name"]
    
    return condensed

def postAnalysisSlidingWindow2(results, startDate=datetime.date(1992, 1, 2), endDate=datetime.date(2023, 2, 1)):
    summaries = pd.DataFrame(columns=["total", "cagr", "drawdownMax", "dailyStddev", "sharpe", "equity"])
    datedTotals = pd.Series(dtype="float64")
    for date, result in results.items():
        if date >= startDate and date <= endDate:
            summaries.loc[len(summaries)] = [result["total"][-1], result["cagr"], result["drawdownMax"], result["dailyStddev"], result["sharpe"], result["equity"]]
            datedTotals[result["total"].index[0]] = result["total"][-1]
    condensed = {"totals":datedTotals}
    
    for name, vals in summaries.items():
        condensed[name + "_avg"] = vals.mean()
        condensed[name + "_med"] = vals.median()
        condensed[name + "_stddev"] = vals.std()
        condensed[name + "_max"] = vals.max()
        condensed[name + "_min"] = vals.min()
        
    condensed["total_max_data"] = results[summaries.query('total == ' + str(condensed["total_max"])).index[0]]["total"]
    condensed["total_min_data"] = results[summaries.query('total == ' + str(condensed["total_min"])).index[0]]["total"]
    condensed["params"] = results[0]["params"]
    condensed["name"] = results.iloc[0]["name"]
    
    return condensed