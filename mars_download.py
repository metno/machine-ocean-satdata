#!/usr/bin/env python
from ecmwfapi import *
from datetime import date, timedelta

# get params zust, 2d, 2t, msl, 10u, 10v, chnk

#date (outer loop)
#   time
#      step
#         number (EPS only)
#            level
#               parameter (inner loop)

# full range to cover available in-situ observation time series
# datetime.datetime(2004, 11, 26, 0, 0, 0, tzinfo=<UTC>)
# datetime.datetime(2021, 7, 31, 23, 59, 59, tzinfo=<UTC>)

# range zust parameter
# datetime.datetime(2010, 9, 10, 0, 0, 0, tzinfo=<UTC>)
# datetime.datetime(2021, 7, 31, 23, 11, 59, tzinfo=<UTC>)

# range including hourly timesteps
# datetime.datetime(2011, 11, 16, 0, 0, 0, tzinfo=<UTC>)
# datetime.datetime(2021, 7, 31, 23, 11, 59, tzinfo=<UTC>)

# chnk/msl/10u/10v/2t/2d/zust
# 148.128/151.128/165.128/166.128/167.128/168.128/3.228

# TODO
# 1) 10u/10v først, så resten
# 2) 2016, så resten
# 3) 10u/10v slutten av 2011 (3-timers oppløsning)

server = ECMWFService("mars")

def daterange(start_date, end_date):
    for n in range(int((end_date - start_date).days)):
        yield start_date + timedelta(n)

start_date = date(2011, 1, 1)
end_date = date(2012, 1, 1)

print("Retrieving for period {} to {}".format(start_date.strftime("%Y%m%d"), end_date.strftime("%Y%m%d")))

for date in daterange(start_date, end_date):
    date_str = date.strftime("%Y%m%d")
    filename = "ifs_fc_{}.nc".format(date_str)

    print("Retrieving {}".format(date_str))

    server.execute(
        {
            "class": "od",
            "date": date_str,
            "expver": "1",
            "levtype": "sfc",
            "param": "165.128/166.128",
            "step": "0/3/6/9",
            "stream": "oper",
            "time": "00/12",
            "type": "fc",
            "grid": "0.1/0.1",
            "format": "netcdf"
        },
        filename)
    
    print("Written {} to file {}".format(date_str, filename))
