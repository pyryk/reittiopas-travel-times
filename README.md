# Travel Time Visualization Utility for HSL Reittiopas
A utility for fetching travel times to a specific location from [HSL Reittiopas](http://reittiopas.fi). Does not provide the actual visualization in any way, just a way to get the data needed for it. Requires a [Reittopas developer account](http://developer.reittiopas.fi/pages/en/account-request.php).

# Prerequisites / Installation
1. [python](http://www.python.org). Developed and tested with Python 3.4, earlier versions *may* also work.
2. [pip](https://pip.pypa.io/). Bundled with the installation of the more recent versions of python.
3. Python module dependencies. Install by running `pip install -r requirements` in the project directory.

## Usage
1. Copy/rename `config.local.json.sample` to `config.local.json`. Input your [reittiopas credentials](http://developer.reittiopas.fi/pages/en/account-request.php) there.
2. run the tool with `python get_travel_times.py "destination address" 0 0`
	* The `0 0` part denotes the "request bounds". The tool divides the HSL area to multiple subareas (or dots) for which the travel times are fetched. As the Reittiopas API has usage quota in place, it may be beneficial to limit the number of requests. The first `0` denotes the request offset and the second the number of requests to be made. The tool is most effectively used by first running e.g. `python get_travel_times.py "kamppi" 0 500`, and then continuing the process in the future with `python get_travel_times.py "kamppi" 501 500`.
	* All command line options can be seen by running `python get_travel_times.py -h`.
* The data is printed in JSON format to stdout or (with -o option) a file.

## Configuration file
The configuration file `config.json` can be used to tweak the program.

Configuration option | Description           
-------------------- | ---------------------
time, date           | travel time for these date/time values.
epsg                 | the coordinate format for the API. See [the API instructions](http://developer.reittiopas.fi/pages/en/http-get-interface-version-2.php) Currently only "4326" supported internally
routes               | the number of different alternatives used to calculate average travel times and the average durations between alternatives. Reittiopas API supports values 1-5.
minLatitude, maxLatitude, minLongitude, maxLongitude | the bounds for the area for which the data is fetched.
step_meters          | the distance between dots for which the travel time data is fetched. Smaller number means more accurate data but more requests. 

## Examples
### Simple use case
	python get_travel_times.py "Vattuniemenranta 2" 0 0
### Output to file
	python get_travel_times.py "Vattuniemenranta 2" 0 0 -o vattuniemenranta2.json
### Split to several sessions
	python get_travel_times.py "Vattuniemenranta 2" 0 500 -o vattuniemenranta2.json
	python get_travel_times.py "Vattuniemenranta 2" 501 500 -o vattuniemenranta2.json -a
### Several destinations, skip sea on subsequent runs
Use the -no option to save dots that yield no routes (most likely dots on sea) in order to skip those with -i dots on subsequent runs

	python get_travel_times.py "Vattuniemenranta 2" 0 0 -o vattuniemenranta2.json --no-results-output noresults.json
	python get_travel_times.py "Hanasaari" 0 0 -o hanasaari.json --ignore noresults.json

Note that the first run has no-results-output option while the second one has ignore.