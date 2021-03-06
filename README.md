# Travel Time Visualization Utility for HSL Reittiopas
A utility for fetching travel times to a specific location from [HSL Reittiopas](http://reittiopas.fi). Does not provide the actual visualization in any way, just a way to get the data needed for it.

# Prerequisites / Installation
1. [python](http://www.python.org). Developed and tested with Python 3.4, earlier versions *may* also work.
2. [pip](https://pip.pypa.io/). Bundled with the installation of the more recent versions of python.
3. Python module dependencies. Install by running `pip install -r requirements.txt` in the project directory.

## Usage
Run the tool with `python get_travel_times.py "destination address"`.

* The tool divides the HSL area to multiple subareas (or dots) for which the travel times are fetched, resulting in hundreds (or thousands) of requests. Therefore, it may be beneficial to split requests into multiple sessions. This can be done with `python get_travel_times.py "destination address" 0 500`. The `0` denotes the request offset (in this case, start from the beginning) and the `500` denotes the number of requests to be made. This feature is most effectively used by first running e.g. `python get_travel_times.py "kamppi" 0 500`, and then continuing the process in the future with `python get_travel_times.py "kamppi" 501 500`.
* All command line options can be seen by running `python get_travel_times.py -h`.
* The data is printed in JSON format to stdout or (with -o option) a file.
* See [Examples](#examples) below for more advanced usage.

## Configuration file
The configuration file `config.json` can be used to tweak the program. Alternatively, it is possible to retain `config.json` as default configuration and override values in `config.local.json`.

Configuration option | Description           
-------------------- | ---------------------
time, date           | travel time for these date/time values. Should be in the API format (HH:MM:SS, YYYY-MM-DD)
sleep                | the number of seconds between each request. This should be set to a minimum of couple of seconds to avoid flooding the API.
routes               | the number of different alternatives used to calculate average travel times and the average durations between alternatives. Reittiopas API supports values 1-5.
min_latitude, max_latitude, min_longitude, max_longitude | the bounds for the area for which the data is fetched.
step_meters          | the distance between dots for which the travel time data is fetched. Smaller number means more accurate data but more requests.

## Returned data
The tool divides the area into several configurable-sized subareas for which the travel times are approximated by fetching the travel time for the center point of the area. The travel time data is then returned as JSON array of objects, as shown next.

	[
	    {
	        "every": 30.0,
	        "lat": 60.109342,
	        "time": 203.2,
	        "lng": 24.638042
	    },
	    {
	        "every": 59.75,
	        "lat": 60.109342,
	        "time": 39.4,
	        "lng": 24.692321
	    },
	    {
	        "every": 59.75,
	        "lat": 60.109342,
	        "time": 44.4,
	        "lng": 24.710414
	    }
	]

In the JSON above, `lat` and `lng` fields represent the latitude and longitude of the departure point, in WGS84 coordinate system. `time` field contains the average travel time to the specified destination and `every` the time difference between proposed departures (i.e. "the bus/etc. runs every 30 minutes")

## Examples
### Simple use case
	python get_travel_times.py "Vattuniemenranta 2"
### Output to file
	python get_travel_times.py "Vattuniemenranta 2" -o vattuniemenranta2.json
### Split fetching to several sessions
	python get_travel_times.py "Vattuniemenranta 2" 0 500 -o vattuniemenranta2.json
	python get_travel_times.py "Vattuniemenranta 2" 501 500 -o vattuniemenranta2.json -a
### Several destinations, skip sea on subsequent runs
Use the --no-results-output (-no) option to save dots that yield no routes (most likely dots on sea) in order to skip those with --ignore (-i) on subsequent runs

	python get_travel_times.py "Vattuniemenranta 2" -o vattuniemenranta2.json --no-results-output noresults.json
	python get_travel_times.py "Hanasaari" -o hanasaari.json --ignore noresults.json

Note that the first run has no-results-output option while the second one has ignore.
