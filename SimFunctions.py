import os
import pandas as pd 
from pandas_datareader import data as pdr
import yfinance as yfin
yfin.pdr_override()
import math
import datetime

def pullAndSaveData(ticker, filePath, start, end):
    data = pdr.get_data_yahoo(ticker, start, end)["Adj Close"]
    print(data)
    saveData(data, ticker, filePath)
    
def saveData(data, ticker, filePath):
    if not os.path.exists(filePath):
        os.makedirs(filePath)
    data.to_csv(os.path.join(filePath, ticker + ".csv"))

def convertToDateOnlyIndex(series):
    dateOnly = pd.Series(dtype="float64")
    for index, date in enumerate(series.index):
        dateOnly[date[:10]] = series[date]
    return dateOnly

def diffIndexes(lhs, rhs):
    diffs = []
    for _, index in enumerate(lhs.index):
        if not index in rhs.index:
            print(index)
            diffs.append(index)
    for _, index in enumerate(rhs.index):
        if not index in lhs.index:
            print(index)
            diffs.append(index)
    return diffs

def removeNonMatches(lhs, rhs):
    shortened = rhs
    for _, index in enumerate(rhs.index):
        if not index in lhs.index:
            shortened = shortened.drop(index)
    return shortened

def returns(prices):
    """
    Calulates the growth of 1 dollar invested in a stock with given prices
    """
    tmp = (1 + prices.pct_change(1)).cumprod()
    tmp[0] = 1
    return tmp

def sim_leverage(proxy, leverage=1, expense_ratio = 0.0, initial_value=1.0):
    pct_change = proxy.pct_change(1)
    pct_change = (pct_change - expense_ratio / 252) * leverage
    sim = (1 + pct_change).cumprod() * initial_value
    sim[0] = initial_value
    return sim

def readLeveraged(dataPath, normalName, leveragedName):
    normalData = convertToDateOnlyIndex(pd.read_csv(os.path.join(dataPath, normalName), index_col=0, header=0).squeeze("columns"))
    leveragedData = convertToDateOnlyIndex(pd.read_csv(os.path.join(dataPath, leveragedName), index_col=0, header=0).squeeze("columns"))
    return normalData, leveragedData

def simulateLeverageHistorical(normalData, leveragedData, leverage, expenseRatio, graphOverlap = True):
    leveragedReturns = returns(leveragedData)
    simLeveragedReturns = sim_leverage(normalData, leverage=leverage, expense_ratio=expenseRatio)
    
    print ("Splicing together at", leveragedReturns.index[0])
    
    simLeveragedEarlier = simLeveragedReturns[:leveragedReturns.index[0]]
    matchMultiplier = simLeveragedEarlier.iloc[-1] / leveragedReturns.iloc[0]
    leveragedSpliced = simLeveragedEarlier.iloc[:-1].append(leveragedReturns * matchMultiplier)
    
    if graphOverlap:
        leveragedAligned = removeNonMatches(simLeveragedReturns, leveragedReturns);
        simLeveragedAligned = removeNonMatches(leveragedReturns, simLeveragedReturns);
        
        leveragedAligned[::20].rename("leveraged").plot(legend=True, figsize=(16,6))
        (simLeveragedAligned[::20] / matchMultiplier).rename("leverage sim").plot(legend=True)
    
    return leveragedSpliced

def bond_sim(rate, maturityYears):
    prices = rate.copy()
    for i in range(1, rate.size - 1):
        previousRate = rate[i-1]
        if math.isnan(rate[i]):
            rate[i] = rate[i-1]
        currentRate = rate[i]
            
        rate1 = 1 + currentRate / 100
        dailyAverage = (previousRate + currentRate) / (252 * 2 * 100)
        rateMaturity = 1 / (rate1 ** maturityYears)
        inverseRateMaturity = rate1 ** (maturityYears * -1)
        inverseOverRate =  (1 - inverseRateMaturity) / currentRate
        prices.values[i] = (prices.values[i-1] * (previousRate * inverseOverRate + rateMaturity - 1 + dailyAverage + 1))
    return prices

def alignSeries(alignTo, align):
    start = alignTo.index[0]
    end = alignTo.index[-1]
    print(start, end)
    aligned = []
    for series in align:
        aligned.append(series[start:end])
        print(aligned[-1].index[0], aligned[-1].index[-1])
    return aligned

def dateToMonth(date):
    return datetime.date(date.year, date.month, 1)

def linearInterpolate(datesData, monthlyData):
    est = pd.Series(dtype="float64")

    daysTilnextMonth, daysInMonth = 1,1
    nextMonthIdx = 1
    month, nextMonth = dateToMonth(datesData.index[0]), dateToMonth(datesData.index[1])
    for i, date in enumerate(datesData.index):
        # get number of days until next month
        if daysTilnextMonth <= 0:
            month = nextMonth
            tmpI = i
            while tmpI < len(datesData.index) and datesData.index[tmpI].month == month.month:
                if tmpI + 1 >=  len(datesData.index):
                    break;
                tmpI += 1
            nextMonth = dateToMonth(datesData.index[tmpI])
            daysTilnextMonth = tmpI - i
            daysInMonth = daysTilnextMonth

        if (daysInMonth > 0):
            diff = monthlyData[nextMonth] - monthlyData[month]
            est[date] = monthlyData[month] + diff * (daysInMonth - daysTilnextMonth)/daysInMonth

        daysTilnextMonth -= 1
    return est