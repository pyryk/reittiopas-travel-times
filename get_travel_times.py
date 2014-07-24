import requests
import json
from decimal import *
import sys
from time import sleep
from datetime import datetime,timedelta
import argparse

def get_config():
  configfile = open('config.json', 'r')
  localconfigfile = open('config.local.json', 'r')
  return dict(list(json.load(configfile).items()) + list(json.load(localconfigfile).items()))

config = get_config()

def get_coordinates(search_term):
  url = 'http://api.reittiopas.fi/hsl/prod/?request=geocode&user={0}&pass={1}&format=json&epsg_in={2}&epsg_out={3}&key={4}'.format(config['username'], config['password'], config['epsg'], config['epsg'], search_term)
  r = requests.get(url)
  json = r.json()
  if len(json) > 0:
    return json[0]['coords']
  else:
    return None

def get_routing(fromCoords,toCoords):
  url = 'http://api.reittiopas.fi/hsl/prod/?request=route&user={0}&pass={1}&format=json&epsg_in={2}&epsg_out={3}&from={4}&to={5}&date={6}&time={7}&show={8}'.format(config['username'], config['password'], config['epsg'], config['epsg'], fromCoords, toCoords, config['date'], config['time'], config['routes'])
  print('Getting {0}...'.format(url))
  r = requests.get(url)
  if (r.text != ''):
    print('Ok.')
    return r.json()
  else:
    print('No routes found for these coordinates.')
    return None

def get_average_travel_time(routing_json):
  durations = list(map(lambda route: route[0]['duration'], routing_json))
  return sum(durations) / len(durations) / 60.0

def get_average_duration_between_routes(routing_json):
  departure_times = list(map(lambda route: datetime.strptime(route[0]['legs'][0]['locs'][0]['depTime'], '%Y%m%d%H%M'), routing_json))

  betweens = []
  for i in range(0, len(departure_times)-1):
    delta = departure_times[i+1] - departure_times[i]
    betweens.append(delta)

  return sum(list(map(lambda time: time.total_seconds() / 60, betweens))) / len(betweens)

def get_travel_times_to(toCoords, lats, lngs, limit=0, offset=0):
  results = []
  noresults = []

  run = 0
  for lat in lats:
    for lng in lngs:
      if (offset == 0 or run >= offset) and (limit == 0 or run < offset + limit):
        fromCoords = str(lng) + ',' + str(lat)
        routing = get_routing(fromCoords, toCoords)
        if routing != None:
          results.append({"lat": lat, "lng": lng, "time": get_average_travel_time(routing), "every": get_average_duration_between_routes(routing)})
        else:
          noresults.append({"lat": lat, "lng": lng})

        if (config['sleep'] != 0):
          sleep(config['sleep'])
      run += 1

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
  file.write(json.dumps(results))
  file.close()

# a hack that is good enough for this purpose
def frange(start, end, step, precision=6):
  coeff = 10**precision
  return list(map(lambda x: x/coeff, range(int(start*coeff), int(end*coeff), int(step*coeff))))

# ---- the actual program

parser = argparse.ArgumentParser()
parser.add_argument("target_address", help="the destination address")
parser.add_argument("offset", type=int, help="the \"index\" of the first departure address to be included in this query")
parser.add_argument("limit", type=int, help="the number of departure addresses, starting from offset, to be included in this query")
parser.add_argument("-o", "--output", help="the output file name (defaults to stdout)")
parser.add_argument("-no", "--no-results-output", help="output file name for \"no results\" output, i.e. list of coordinates for which there is no result. Can be used to avoid trying to fetch routes from sea etc.")
parser.add_argument("-a", "--append", help="append the output files if they exist", action="store_true")

args = parser.parse_args()

target_addr = args.target_address
offset = args.offset
limit = args.limit

target = get_coordinates(target_addr)

data = get_travel_times_to(target, frange(config['minLatitude'], config['maxLatitude'], config['step']), frange(config['minLongitude'], config['maxLongitude'], config['step']), limit, offset)

if args.output != None:
  write_json(data['results'], args.output, args.append)
else:
  print(json.dumps(data['results']))

if args.no_results_output != None:
  write_json(data['noresults'], args.no_results_output, args.append)

total_count = len(data['results']) + len(data['noresults'])
print('\nAll done, total {0} queries.'.format(total_count))
