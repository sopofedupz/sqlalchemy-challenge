#############################################
# Import modules
#############################################

from flask import Flask, jsonify
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import datetime as dt
import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func, inspect
import seaborn as sns
from collections import OrderedDict


#################################################
# Database Setup
#################################################
engine = create_engine("sqlite:///Resources/hawaii.sqlite", connect_args={'check_same_thread': False})

# reflect an existing database into a new model
Base = automap_base()
# reflect the tables
Base.prepare(engine, reflect=True)

# Save reference to the table
Measurement = Base.classes.measurement
Station = Base.classes.station

# Create our session (link) from Python to the DB
session = Session(engine)
conn = engine.connect()

# query the latest date in the database
latest_date = session.query(Measurement.date).order_by(Measurement.date.desc()).first()

# getting the the 1-yr prior date to retrieve the previous 1 year data
latestDate = list(np.ravel(latest_date))
LatestDate = dt.datetime.strptime(latestDate[0],'%Y-%m-%d').date()
year_ago = LatestDate - dt.timedelta(days=365)

# filter the 1-year data and calculate the AVERAGE PRECIPITATION by Date
ave_prcp = func.avg(Measurement.prcp)
results = session.query(Measurement.date, ave_prcp, Measurement.station, Measurement.tobs).\
    filter(Measurement.date.between(year_ago, LatestDate)).\
    group_by(Measurement.date).\
    order_by(Measurement.date.desc()).all()

# query list of stations and count of observations at each station
station_list = session.query(Measurement.station, Station.name, func.count(Measurement.station)).\
    join(Measurement, Measurement.station == Station.station).group_by(Measurement.station).\
    order_by(func.count(Measurement.station).desc()).all()

# setting the average, minimum, and maximum temperature
ave_temp = func.avg(Measurement.tobs)
min_temp = func.min(Measurement.tobs)
max_temp = func.max(Measurement.tobs)

#################################################
# Flask Setup
#################################################

app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False

#################################################
# Flask Routes
#################################################

# Homepage with available routes
################################

@app.route("/")
def home():
        return (
        f"<strong><h1>Welcome to Hawaii!</h1></strong>"
        f"<h2>Here you will get the precipitation and observed temperature data between 2010-01-01 and 2017-08-23 at different stations in Hawaii!</h1>"
        f"<h4>If you would like to get the average precipitation by date (between 2016-08-23 and 2017-08-23), go to: <u>/api/v1.0/precipitation</u></h4>"
        f"<h4>Here is a list of stations in Hawaii: <u>/api/v1.0/stations</u></h4>"
        f"<h4>To get a list of Temperature Observations by station (between 2016-08-23 and 2017-08-23), go to: <u>/api/v1.0/tobs</u></h4>"
        f"<h4>If you would like to get the average, minimum, and maximum temperature recorded at stations from any given date, go to (replace startdate with the date of interest - <i>format YYYY-MM-DD</i>): <u>/api/v1.0/startdate</u></h4>"
        f"<h4>If you would like to get the average, minimum, and maximum temperature recorded at stations from any given date range, go to (replace startdate and enddate with the date of interest - <i>format YYYY-MM-DD</i>): <u>/api/v1.0/startdate/enddate</u></h4>"
    )

# Precipitation page
####################

@app.route("/api/v1.0/precipitation")
def prcp():
    # Unpack the date and prcp from results and save into separate lists
    date = [result[0] for result in results]
    prcp = [round(result[1],2) for result in results]
    
    # put results in dict
    prcp_dict = dict(zip(date, prcp))

    return jsonify(prcp_dict)

# Stations
###########

@app.route("/api/v1.0/stations")
def stations():
    # Unpack the station from results and save into separate lists
    station = [result[0] for result in station_list]
    station_name = [result[1] for result in station_list]
    
    # put results in dict
    station_dict = dict(zip(station, station_name))

    return jsonify(station_dict)

# Temperature Observation
##########################

@app.route("/api/v1.0/tobs")
def tobs():
    # Unpack the date, station, and temperature observations from results and save into separate lists
    date = [result[0] for result in results]
    station = [result[2] for result in results]
    tobs = [result[3] for result in results]
    
    # prepare a list of station, date, and temperature observation
    tobs_station_list = []
    for result in results:
        case = {'Station': result[2], 'Date of Observation': result[0], 'Temperature Observation':result[3] }
        tobs_station_list.append(case)

    return jsonify(tobs_station_list)

# Temperature observation given a start (with or without end date)
###################################################################

@app.route("/api/v1.0/<start>")
def start_temp(start):
    # query the average, minimum, and maximum temperature on and after a given date
    tobs_start = session.query(Measurement.date, ave_temp, min_temp, max_temp).\
        filter(Measurement.date >= start).\
        group_by(Measurement.date).all()

    # creating an empty list to store the information
    temp_list = []

    # creating a dictionary to store the information
    for result in tobs_start:
        temp_dict = {
            'Date': result[0],
            'Average Temperature': round(result[1],0), 
            'Minimum Temperature': result[2], 
            'Maximum Temperature':result[3]
            }
        temp_list.append(temp_dict)
        
    return jsonify(temp_list)

# Temperature observation given a start and end date
#####################################################

@app.route("/api/v1.0/<start>/<end>")
def startend(start,end):

    # query the average, minimum, and maximum temperature on and after a given date
    tobs_startend = session.query(Measurement.date, ave_temp, min_temp, max_temp).\
        filter(Measurement.date.between(start, end)).\
        group_by(Measurement.date).all()

    # creating an empty list to store the information
    temp_startend_list = []

    # creating a dictionary to store the information
    for result in tobs_startend:
        temp_startend_dict = {
            'Date': result[0],
            'Average Temperature': round(result[1],0), 
            'Minimum Temperature': result[2], 
            'Maximum Temperature':result[3]
            }
        temp_startend_list.append(temp_startend_dict)
       
    return jsonify(temp_startend_list)

if __name__ == "__main__":
    app.run(debug=True)
