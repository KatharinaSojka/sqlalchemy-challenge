# Import the dependencies.
import numpy as np
import pandas as pd
import datetime as dt
import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func
from flask import Flask, jsonify
from collections import OrderedDict

#################################################
# Database Setup
#################################################
engine = create_engine("sqlite:///Resources/hawaii.sqlite")

# reflect an existing database into a new model

Base = automap_base()
# reflect the tables

Base.prepare(engine, reflect=True)

# Save references to each table
measurement = Base.classes.measurement
station = Base.classes.station


# Create our session (link) from Python to the DB

session = Session(engine)

#################################################
# Flask Setup
#################################################

app = Flask(__name__)

def valid_date(datestr):
    """Helper function, checking if a date string is valid."""
    try:
        dt.datetime.strptime(datestr, "%Y-%m-%d")
        return True
    except ValueError:
        return False


#################################################
# Flask Routes
#################################################

@app.route("/")
def homepage():
    """List all the available api routes"""
    return (
        f"Available Routes:<br/>"
        f"/api/v1.0/precipitation<br/>"
        f"/api/v1.0/stations<br/>"
        f"/api/v1.0/tobs<br/>"
        "/api/v1.0/&lt;start date&gt;<br/>"
        "/api/v1.0/&lt;start date&gt;/&lt;end date&gt;"
    )
    
    
@app.route("/api/v1.0/precipitation")
def precipitation():
    """Return the last 12 months of precipitation data as JSON"""
    # Calculate the date one year ago from the last date in the database
    recent_date = session.query(func.max(measurement.date)).scalar()
    year_before = dt.datetime.strptime(recent_date, '%Y-%m-%d') - dt.timedelta(days=365)
    
    # Query precipitation data for the last 12 months
    prcp_data = session.query(measurement.date, measurement.prcp).\
                filter(measurement.date >= year_before).order_by(measurement.date).all()

    # Convert the query results to a dictionary using date as the key and prcp as the value
    prcp_dict = [{"date": date, "prcp": prcp} for date, prcp in prcp_data]
    return jsonify(prcp_dict)
    
@app.route("/api/v1.0/stations")
def stations():
    """Return a JSON list of stations from the dataset."""
    # Query all stations
    unique_stations = session.query(measurement.station).distinct().all()

    # Extract station names from the query result
    station_names = [station[0] for station in unique_stations]

    return jsonify(station_names)


@app.route("/api/v1.0/tobs")
def tobs():  
    """Query the dates and temperature observations of the most-active station for the previous year of data"""
    
    # Calculate the date one year ago from the last date in the database
    recent_date = session.query(func.max(measurement.date)).scalar()
    year_before = dt.datetime.strptime(recent_date, '%Y-%m-%d') - dt.timedelta(days=365)
    
    # Querying the most-active station ID
    most_active_stations = session.query(measurement.station, func.count()).\
    group_by(measurement.station).\
    order_by(func.count().desc()).all()
    
    #storing the most active station id
    most_active_station_id = most_active_stations[0][0]
    
    # Querying dates and temperature observations for the most-active station for the last 12 months
    temperatures_mas = session.query(measurement.date, measurement.tobs).\
    filter(measurement.station == most_active_station_id).\
    filter(measurement.date >= year_before).all()
    
    tobs_data = [{"date": date, "tobs": tobs} for date, tobs in temperatures_mas]

    return jsonify(tobs_data)
  

@app.route("/api/v1.0/<start>")
def start(start):

# Using the helper function for date validation
    if not valid_date(start):
        return jsonify({"error": "Invalid date format. Please use followig format: YYYY-MM-DD."})
        
        
    """Query the database for temperature data for dates greater than or equal to the provided start date."""
    
    # Convert the start date string to a datetime object
    start_date = dt.datetime.strptime(start, "%Y-%m-%d")

    # Query the database for temperature data for dates greater than or equal to the start date
    temperature_data = session.query(func.min(measurement.tobs), func.avg(measurement.tobs), func.max(measurement.tobs)).\
        filter(measurement.date >= start_date).all()

    # Extract the temperature data from the query result
    tmin, tavg, tmax = temperature_data[0]

    # Create a dictionary to hold the temperature data
    temperature_dict = {
        "Start_date": start_date.strftime("%Y-%m-%d"),
        "Minimum Temperature": tmin,
        "Maximum Temperature": tmax,
        "Average Temperature": tavg
        
    }

    return jsonify(temperature_dict)
    
    
@app.route("/api/v1.0/<start>/<end>")
def start_end(start,end):

# Using the helper function for date validation
    if not valid_date(start) or not valid_date(end):
        return jsonify({"error": "Invalid date format. Please use followig format for date: YYYY-MM-DD."})   
        
    """Query the database for temperature data for dates within provided start dates."""
    
    # Convert the start and end date string to a datetime object
    start_date = dt.datetime.strptime(start, "%Y-%m-%d")
    end_date = dt.datetime.strptime(end, "%Y-%m-%d")

    # Query the database for temperature data for dates within provided start dates
    temperature_data = session.query(func.min(measurement.tobs), func.avg(measurement.tobs), func.max(measurement.tobs)).\
        filter(measurement.date >= start_date, measurement.date <= end).all()

    # Extract the temperature data from the query result
    tmin, tavg, tmax = temperature_data[0]

    # Create a dictionary to hold the temperature data using orderedDict
    temperature_dict = OrderedDict([
        ("Start_date", start_date.strftime("%Y-%m-%d")),
        ("End_date", end_date.strftime("%Y-%m-%d")),
        ("Minimum Temperature", tmin),
        ("Maximum Temperature", tmax),
        ("Average Temperature", tavg)
    ])

    return jsonify(temperature_dict)
    
if __name__ == "__main__":
    app.run(debug=True)
    
    # Close the SQLAlchemy session
    session.close()