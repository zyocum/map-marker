#!/usr/bin/env python3

"""Given a list of location queries, mark the locations on a Foium 
(https://github.com/python-visualization/folium) map via the OpenCage 
(https://geocoder.opencagedata.com/) geocoder service
"""

import os
import sys
import getpass

from itertools import chain
from math import pi, sin, cos, atan2, sqrt

import folium

from opencage.geocoder import OpenCageGeocode

def middle(*coordinates):
    """Finde the middle point between a collection of coordinates
    
    coordinates: iterable of (lat, lng) points
    
    From: https://stackoverflow.com/a/18623672"""
    if len(coordinates) == 1:
        return coordinates[0]
    if len(coordinates) < 2:
        print(
            f'Need at least one coordinate (got {len(coordinates)}',
            file=sys.stderr
        )
        return None
    x, y, z = 0.0, 0.0, 0.0
    for coordinate in coordinates:
        lat, lng = coordinate
        lat_angle = lat * pi / 180
        lng_angle = lng * pi / 180
        x += cos(lat_angle) * cos(lng_angle)
        y += cos(lat_angle) * sin(lng_angle)
        z += sin(lat_angle)
    x /= len(coordinates)
    y /= len(coordinates)
    z /= len(coordinates)
    longitude = atan2(y, x)
    hypotenuse = sqrt(x * x + y * y)
    latitude = atan2(z, hypotenuse)
    return (latitude * 180 / pi, longitude * 180 / pi)

def coordinates(location):
    """Return a (lat, lng) tuple from an OpenCage location result
    
    location: a dict (from opencage.geocoder.OpenCageGeocode.geocode)
    """
    geometry = location['geometry']
    return geometry['lat'], geometry['lng']

def mark(query, location, map_, rank, total):
    """Given a location query, its rank, the location result for the query,
    a map and the total number of results, mark the location on the map with
    useful information.
    
    query: a location query string
    rank: the rank of the location within the results
    location: a result from opencage.geocoder.OpenCageGeocode.geocode
    map_: a folium.Map
    total: the total number of results returned by 
           opencage.geocoder.OpenCageGeocode.geocode
    """
    label = (
        f'<p>Query: {query}</p>'
        f'<p>Rank: {rank} (of {total})</p>'
        f'<p>Formatted: {location["formatted"]}</p>'
        f'<p>Coordinates: {coordinates(location)!r}</p>'
    )
    folium.Marker(
        coordinates(location),
        popup=label
    ).add_to(map_)

def main(geocoder, queries, outfile, zoom=0):
    """Given a geocoder, a list of query strings, and an output file name
    create a map, mark the results, and write the map to the file.  An optional
    zoom parameter can be supplied to zoom in on the midpoint between the 
    marked results.
    
    geocoder: an opencage.geocoder.OpenCageGeocode
    queries: a list of query strings
    outfile: path to a file where the output will be written
    zoom: specify a starting zoom level (default=0)
    """
    results = {query: geocoder.geocode(query) for query in queries}
    locations = list(chain(*results.values()))
    candidate_coordinates = []
    for locations in results.values():
        for location in locations:
            candidate_coordinates.append(coordinates(location))
    map_ = folium.Map(
        location=middle(*candidate_coordinates),
        zoom_start=zoom,
        detect_retina=True
    )
    for query, locations in results.items():
        for rank, location in enumerate(locations, 1):
            mark(query, location, map_, rank, len(locations))
    map_.save(outfile)

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description=__doc__
    )
    parser.add_argument(
        'input',
        type=argparse.FileType('r'),
        help=(
            'a file with a list of queries (one query per line; use "-" '
            'to read queries from stdin)'
        )
    )
    parser.add_argument(
        'output',
        type=argparse.FileType('wb'),
        help='a file where a folio.Map map will be written as HTML'
    )
    parser.add_argument(
        '-z', '--zoom',
        type=int,
        default=0,
        help='starting zoom level'
    )
    parser.add_argument(
        '-k', '--key',
        default=None,
        help=(
            'your OpenCage API key (get a key here: '
            'https://geocoder.opencagedata.com/users/sign_up)'
        )
    )
    args = parser.parse_args()
    queries = [line.rstrip() for line in args.input]
    key = (
        os.environ.get('OPENCAGE_USER_KEY')
        or args.key
        or getpass(prompt='OpenCage API key: ')
    )
    main(
        OpenCageGeocode(key),
        queries,
        args.output,
        zoom=args.zoom
    )
