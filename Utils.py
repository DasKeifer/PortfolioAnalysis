import pandas as pd 
import datetime

def convertToDateOnlyIndex(series):
    dateOnly = pd.Series(dtype="float64")
    for index, date in enumerate(series.index):
        dateOnly[date[:10]] = series[date]
    return dateOnly

def convertToDateTimeDate(series):
    dateOnly = pd.Series(dtype="float64")
    for _, date in enumerate(series.index):
        dt = datetime.datetime.strptime(date[:10], "%Y-%m-%d").date()
        dateOnly[dt] = series[date]
    return dateOnly
    