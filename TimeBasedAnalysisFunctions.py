import datetime
import matplotlib.pyplot as plt

import MultiprocessingHelper as mh


def percentageBasedSlidingWindowMultiprocessWrapper(data, args):
    import AnalysisFunctions as af
        
    narrowedArgs = [args[1], True, "current", args[4], args[5]]
    res = af.slidingWindowAnalysis(af.percentageBased, data, args=narrowedArgs,\
                                    timeWindow=args[2], timeStep=args[3], startDate=args[6], endDate=args[7])
    res.iloc[0]["name"] = args[0]
    return res

def percentageBased2SlidingWindowMultiprocessWrapper(data, args):
    import AnalysisFunctions as af
        
    narrowedArgs = [args[1], True, args[4], args[5], 14, True, .2875, .4075, True]
    res = af.slidingWindowAnalysis(af.percentageBased2, data, args=narrowedArgs,\
                                    timeWindow=args[2], timeStep=args[3], startDate=args[6], endDate=args[7])
    res.iloc[0]["name"] = args[0]
    return res

def makePortfioliosAndRun(stockData, startingBalance, periodicDeposit, timeWindow, timeStep, results,\
                          startDate=datetime.date(2005, 1, 28), endDate=datetime.date(2023, 2, 3), portfolios=["best"]):
    args = []
    if portfolios == "all" or "spy" in portfolios:
        spy100p = [{'ticker':'spy', 'targetPercent':1,'maxIncrease':.05,'maxDecrease':0.05}]
        args.append(["spy", spy100p, timeWindow, timeStep, startingBalance, periodicDeposit, startDate, endDate])

    if portfolios == "all" or "spyief" in portfolios:
        spyiefp = [{'ticker':'spy', 'targetPercent':.6,'maxIncrease':.05,'maxDecrease':0.05},
                    {'ticker':'ief', 'targetPercent':.4,'maxIncrease':.05,'maxDecrease':0.05}]
        args.append([spyiefp, timeWindow, timeStep, startingBalance, periodicDeposit, startDate, endDate])
        
        spyiefp = [{'ticker':'spy', 'targetPercent':.5,'maxIncrease':.05,'maxDecrease':0.05},
                    {'ticker':'ief', 'targetPercent':.5,'maxIncrease':.05,'maxDecrease':0.05}]
        args.append([spyiefp, timeWindow, timeStep, startingBalance, periodicDeposit, startDate, endDate])
        
        spyiefp = [{'ticker':'spy', 'targetPercent':.4,'maxIncrease':.05,'maxDecrease':0.05},
                    {'ticker':'ief', 'targetPercent':.6,'maxIncrease':.05,'maxDecrease':0.05}]
        args.append([spyiefp, timeWindow, timeStep, startingBalance, periodicDeposit, startDate, endDate])
        
    if portfolios == "all" or "spytlt" in portfolios:
        spytltp = [{'ticker':'spy', 'targetPercent':.6,'maxIncrease':.05,'maxDecrease':0.05},
                    {'ticker':'tlt', 'targetPercent':.4,'maxIncrease':.05,'maxDecrease':0.05}]
        args.append([spytltp, timeWindow, timeStep, startingBalance, periodicDeposit, startDate, endDate])
        
        spytltp = [{'ticker':'spy', 'targetPercent':.5,'maxIncrease':.05,'maxDecrease':0.05},
                    {'ticker':'tlt', 'targetPercent':.5,'maxIncrease':.05,'maxDecrease':0.05}]
        args.append([spytltp, timeWindow, timeStep, startingBalance, periodicDeposit, startDate, endDate])
        
        spytltp = [{'ticker':'spy', 'targetPercent':.4,'maxIncrease':.05,'maxDecrease':0.05},
                    {'ticker':'tlt', 'targetPercent':.6,'maxIncrease':.05,'maxDecrease':0.05}]
        args.append([spytltp, timeWindow, timeStep, startingBalance, periodicDeposit, startDate, endDate])

    mh.runFunctionMultiprocess(percentageBasedSlidingWindowMultiprocessWrapper, len(args), stockData, args, results)
    
def makePortfioliosAndRun2(stockData, startingBalance, periodicDeposit, timeWindow, timeStep, results,\
                          startDate=datetime.date(2005, 1, 28), endDate=datetime.date(2023, 2, 3), portfolios=["best"]):
    args = []
    if portfolios == "all" or "spy" in portfolios:
        spy100p = [{'ticker':'spy', 'targetPercent':1,'maxIncrease':.05,'maxDecrease':0.05}]
        args.append(["spy", spy100p, timeWindow, timeStep, startingBalance, periodicDeposit, startDate, endDate])

    mh.runFunctionMultiprocess(percentageBased2SlidingWindowMultiprocessWrapper, len(args), stockData, args, results)
    
def showResultsSummary(results, filterStrings=[""], divsor=1, ylim=[0,10]):
    print("{:20}, {:10}, {:10}, {:10}, {:10}, {:10}, {:10}, {:10}".format("  id", "  avg", "  med", "  max", "  min", "ttl std", "std avg", "shp avg"))
    for result in results:
        if filterStrings == None or result["name"] in filterStrings:
            print("{:20}, {:10.4f}, {:10.4f}, {:10.4f}, {:10.4f}, {:10.4f}, {:10.4f}, {:10.4f}".format(
                result["name"], result["total_avg"]/divsor, result["total_med"]/divsor, result["total_max"]/divsor, result["total_min"]/divsor, result["total_stddev"]/divsor, result["dailyStddev_avg"], result["sharpe_avg"]))
            ax = (result["totals"]/divsor).rename(result["name"]).plot(legend=True, figsize=(16,8)) 
            ax.set_ylim(ylim)
                
def showResultsSummary2(results, filterStrings=[""], divsor=1, ylim=[0,10]):
    print("{:20}, {:10}, {:10}, {:10}, {:10}, {:10}, {:10}, {:10}".format("  id", "  avg", "  med", "  max", "  min", "ttl std", "std avg", "shp avg"))
    for result in results:
        if filterStrings == None or result["name"] in filterStrings:
            print("{:12}, {:10.4f}, {:10.4f}, {:10.4f}, {:10.4f}, {:10.4f}, {:10.4f}, {:10.4f}".format(
                result["name"], result["total_avg"]/divsor, result["total_med"]/divsor, result["total_max"]/divsor, result["total_min"]/divsor, result["total_stddev"]/divsor, result["dailyStddev_avg"], result["sharpe_avg"]))
            ax = (result["totals"]/divsor).rename(result["name"]).plot(legend=True, figsize=(16,8)) 
            ax.set_ylim(ylim)