#!/usr/bin/env python
import click
import cligj
import json

import mapbox
from pyconcorde import atsp_tsp, run_concorde, dumps_matrix


def split(a, chunk_size):
    """ Given a list a,
    generate ordered lists no larger than chunk_size"""
    n = int((len(a) / float(chunk_size)) + 1)
    k, m = len(a) / n, len(a) % n
    return (a[i * k + min(i, m):(i + 1) * k + min(i + 1, m)]
            for i in xrange(n))


@click.command()
@cligj.features_in_arg
@click.option("--directions/--no-directions", default=True,
              help="Find turn-by-turn directions between waypoints")
def optimal_tour(features, directions):
    """
    Collect some waypoints (need three or more)
      $ mapbox geocoding "Arcata, CA" | jq -c .features[0] >> waypoints.txt

    Then pipe to the optimize_route CLI
      $ cat waypoints.txt | optimal_tour | geojson-summary
      19 points and 1 line
    """
    features = [f for f in features if f['geometry']['type'] == 'Point']
    if len(features) <= 2:
        raise click.UsageError(
            "Need at least 3 point features to create route")

    dist_api = mapbox.Distance()
    res = dist_api.distances(features)
    if res.status_code == 200:
        matrix = res.json()['durations']
    else:
        raise Exception("Got a {0} error from the Distances API: {1}".format(
            res.status_code, res.content))

    matrix_sym = atsp_tsp(matrix, strategy="avg")

    outf = "/tmp/myroute.tsp"
    with open(outf, 'w') as dest:
        dest.write(dumps_matrix(matrix_sym, name="My Route"))

    tour = run_concorde(outf, start=0)
    order = tour['tour']

    features_ordered = [features[i] for i in order]

    if directions:
        # gather geojson linestring features along actual route via directions
        directions_api = mapbox.Directions()
        route_features = []
        for chunk in split(features_ordered + [features_ordered[0]], 25):
            res = directions_api.directions(chunk)
            if res.status_code == 200:
                route_features.append(res.geojson()['features'][0])
            else:
                raise Exception(
                    "Got a {0} error from the Directions API: {1}".format(
                        res.status_code, res.content))
    else:
        # Alternative, straight line distance between points
        route_coords = [f['geometry']['coordinates'] for f in features_ordered]
        route_coords.append(features_ordered[0]['geometry']['coordinates'])
        route_features = [{
            'type': 'Feature',
            'properties': {'tour': tour},
            'geometry': {
                'type': 'LineString',
                'coordinates': route_coords}}]

    # meld into one geojson feature collection
    collection = {
        'type': 'FeatureCollection',
        'features': features_ordered + route_features}

    click.echo(json.dumps(collection))

if __name__ == "__main__":
    optimal_tour()
