import requests
import json
from decimal import *
import sys
from time import sleep
from datetime import datetime,timedelta
import argparse
import math
from requests.exceptions import *

def get_config():
  configfile = open('config.json', 'r')
  return json.load(configfile)

config = get_config()

def get_coordinates(search_term):
  url = 'http://api.digitransit.fi/geocoding/v1/search?text={0}&size=1'.format(search_term)
  r = requests.get(url)
  json = r.json()
  if len(json['features']) > 0:
    coords = json['features'][0]['geometry']['coordinates']
    return {'lat': coords[1], 'lng': coords[0]} # geojson coordinate array is lng, lat
  else:
    return None

def get_payload(fromCoords, toCoords):
  return {
  'query': '''
    {{
      plan(
        from: {{lat: {0}, lon: {1}}}
        to: {{lat: {2}, lon: {3}}}
        numItineraries: {4}
        date: "{5}"
        time: "{6}"
      ) {{
        itineraries {{
          duration
          startTime
        }}
      }}
    }}
    '''.format(fromCoords['lat'], fromCoords['lng'], toCoords['lat'], toCoords['lng'], config['routes'], config['date'], config['time']),
    'variables': None
    }

def get_routing(fromCoords,toCoords):

  payload=get_payload(fromCoords, toCoords)

  print('Getting data for point ({0},{1})'.format(fromCoords['lat'], fromCoords['lng']))
  r = requests.post(config['endpoint'], json=payload)
  json = r.json()
  if len(json['data']['plan']['itineraries']) > 0:
    return json
  else:
    print('No routes found for these coordinates.')
    return None
  #if (r.text != ''):
#    print('Ok.')
#    return r.json()
#  else:
#    print('No routes found for these coordinates.')
#    return None

# should work with relatively small areas sufficiently far away from the poles
# from http://stackoverflow.com/questions/1253499/simple-calculations-for-working-with-lat-lon-km-distance
def get_step_in_coordinates(property, step_meters, latitude=None):
  if property == 'latitude':
    return math.fabs(step_meters / 110540.0)
  elif property == 'longitude' and latitude != None:
    return math.fabs(step_meters / (111320.0 * math.cos(math.radians(latitude))))
  else:
    raise ValueError('property is not latitude or longitude or latitude is not specified when getting longitude property')

def get_average_travel_time(routing_json):
  durations = list(map(lambda route: route['duration'], routing_json['data']['plan']['itineraries']))
  return sum(durations) / len(durations) / 60.0

def get_average_duration_between_routes(routing_json):
  itineraries = routing_json['data']['plan']['itineraries']
  earliest_departure = min(itineraries, key=lambda itinerary: itinerary['startTime'])
  latest_departure = max(itineraries, key=lambda itinerary: itinerary['startTime'])

  return (latest_departure['startTime'] - earliest_departure['startTime']) / 1000 / 60

def get_travel_times_to(toCoords, lats, lngs, limit=0, offset=0, ignore_file=None):
  results = []
  noresults = []

  print('Total {0} points, limiting to {1}'.format(len(lats)*len(lngs), limit))

  try:
    run = 0
    for lat in lats:
      for lng in lngs:
        if (offset == 0 or run >= offset) and (limit == 0 or run < offset + limit):
          fromCoords = {'lng': lng,  'lat': lat}
          if ignore_file is None or not should_ignore(lat, lng, ignore_file):
            print('Fetching routing for point {0}'.format(run))
            try:
              routing = get_routing(fromCoords, toCoords)
              if routing != None:
                results.append({"lat": lat, "lng": lng, "time": get_average_travel_time(routing), "every": get_average_duration_between_routes(routing)})
              else:
                noresults.append({"lat": lat, "lng": lng})
            except RequestException as e:
                print('Got {0} when trying to fetch routing for point {1} (from {2} to {3}): {4}'.format(type(e), run, fromCoords, toCoords, e.args))
                raise e

            if (config['sleep'] != 0):
              sleep(config['sleep'])
          else:
            print('Ignoring point ({0}, {1})'.format(lat, lng))
        run += 1
  except (RequestException, KeyboardInterrupt):
    pass

  return {"results": results, "noresults": noresults}

def write_json(to_write, filename, append):
  results = None
  if append:
    rfile = open(filename, 'r')
    results = json.load(rfile) + to_write
    rfile.close()
  else:
    results = to_write

  file = open(filename, 'w')
  file.write(json.dumps(results, indent=4))
  file.close()

def should_ignore(lat, lng, ignores):
  for loc in ignores:
    if loc['lat'] == lat and loc['lng'] == lng:
      return True
  return False

# a hack that is good enough for this purpose
def frange(start, end, step, precision=6):
  coeff = 10**precision
  return list(map(lambda x: 1.0*x/coeff, range(int(start*coeff), int(end*coeff), int(step*coeff))))

# ---- the actual program

parser = argparse.ArgumentParser()
parser.add_argument("target_address", help="the destination address")
parser.add_argument("offset", type=int, help="the \"index\" of the first departure address to be included in this query")
parser.add_argument("limit", type=int, help="the number of departure addresses, starting from offset, to be included in this query")
parser.add_argument("-o", "--output", help="the output file name (defaults to stdout)")
parser.add_argument("-no", "--no-results-output", help="output file name for \"no results\" output, i.e. list of coordinates for which there is no result. Can be used in combination to --ignore to avoid trying to fetch routes from sea etc.")
parser.add_argument("-a", "--append", help="append the output files if they exist", action="store_true")
parser.add_argument("-i", "--ignore", help="path to file that contains points to be ignored. Uses --no-results-output formatting.")

args = parser.parse_args()
ignore = json.load(open(args.ignore, 'r')) if args.ignore != None else None

target = get_coordinates(args.target_address)
step_latitude = get_step_in_coordinates('latitude', config['step_meters'])
step_longitude = get_step_in_coordinates('longitude', config['step_meters'], (config['max_latitude'] + config['min_latitude']) / 2)
data = get_travel_times_to(target, frange(config['min_latitude'], config['max_latitude'], step_latitude), frange(config['min_longitude'], config['max_longitude'], step_longitude), args.limit, args.offset, ignore)

if args.output != None:
  write_json(data['results'], args.output, args.append)
else:
  print(json.dumps(data['results'], indent=4))

if args.no_results_output != None:
  write_json(data['noresults'], args.no_results_output, True) # always append

total_count = len(data['results']) + len(data['noresults'])
print('\nAll done, total {0} queries.'.format(total_count))
