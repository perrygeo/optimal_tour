#!/usr/bin/env python
import click
import cligj
import json
import math

import mapbox
from pyconcorde import atsp_tsp, run_concorde, dumps_matrix


def split(a, chunk_size):
    """ Given a list a,
    generate ordered lists no larger than chunk_size"""
    n = int((len(a) / float(chunk_size)) + 1)
    k, m = len(a) / n, len(a) % n
    return (a[i * k + min(i, m):(i + 1) * k + min(i + 1, m)]
            for i in xrange(n))


def great_circle(a, b, R=3959):
    """Calculates distance between two latitude-longitude coordinates.
    default radius in miles
    """
    if a == b:
        return 0
    lat1, lon1 = math.radians(a[0]), math.radians(a[1])
    lat2, lon2 = math.radians(b[0]), math.radians(b[1])
    return math.acos(math.sin(lat1) * math.sin(lat2) +
                     math.cos(lat1) * math.cos(lat2) * math.cos(lon1 - lon2)) * R


def local_matrix(features, method):
    matrix = []
    for fa in features:
        row = []
        for fb in features:
            pa = fa['geometry']['coordinates']
            pb = fb['geometry']['coordinates']
            if method == 'geodesic':
                dist = great_circle(pa, pb)
            else:  # cartesian
                dist = ((pb[0] - pa[0])**2 + (pb[1] - pa[1])**2) ** 0.5
            row.append(dist)
        matrix.append(row)
    return matrix


def is_lonlat(features):
    for f in features:
        p = f['geometry']['coordinates']
        if p[0] <= -180 or p[1] <= -90 or p[0] >= 180 or p[1] >= 90:
            return False
    return True


def log(txt):
    click.echo("# " + txt, err=True)


@click.command()
@cligj.features_in_arg
@click.option("--mode", default="directions",
              type=click.Choice(['directions', 'geodesic', 'cartesian']),
              help="Mode for calculating travel costs between points")
@click.option('--profile', default="driving",
              type=click.Choice(mapbox.Distance().valid_profiles),
              help="Mapbox profile if using directions")
@click.option('--out-points/--no-out-points', default=True,
              help="output points along with tour linestring")
def optimal_tour(features, mode, profile, out_points):
    """
    A command line interface for solving the traveling salesman problem

    Input geojson features with point geometries
    and output the optimal tour as geojson feature collection.

     \b
      $ optimal_tour waypoints.geojson | geojson-summary
      19 points and 1 line

    If using geodesic or directions modes, input must be in lonlat coordinates

    Directions mode requires a Mapbox account and a valid token set as
    the MAPBOX_ACCESS_TOKEN environment variable.
    """
    log("Get point features")
    features = [f for f in features if f['geometry']['type'] == 'Point']
    if len(features) <= 2:
        raise click.UsageError(
            "Need at least 3 point features to create route")

    if mode != 'cartesian' and not is_lonlat(features):
        raise click.UsageError(
            "For this {} mode, input must be in lonlat coordinates".format(
                mode))

    log("Create travel cost matrix")
    if mode == 'cartesian':
        matrix = local_matrix(features, 'cartesian')
    elif mode == 'geodesic':
        matrix = local_matrix(features, 'geodesic')
    elif mode == 'directions':
        dist_api = mapbox.Distance()
        res = dist_api.distances(features, profile=profile)
        if res.status_code == 200:
            matrix = res.json()['durations']
        else:
            raise Exception("Got a {0} error from the Distances API: {1}".format(
                res.status_code, res.content))

    log("Prep data for concorde")
    matrix_sym = atsp_tsp(matrix, strategy="avg")

    outf = "/tmp/myroute.tsp"
    with open(outf, 'w') as dest:
        dest.write(dumps_matrix(matrix_sym, name="My Route"))

    log("Run concorde")
    tour = run_concorde(outf, start=0)
    order = tour['tour']

    features_ordered = [features[i] for i in order]

    log("Create lines connecting the tour")
    if mode == 'directions':
        # gather geojson linestring features along actual route via directions
        directions_api = mapbox.Directions()
        route_features = []
        for chunk in split(features_ordered + [features_ordered[0]], 25):
            res = directions_api.directions(chunk, profile='mapbox.' + profile)
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
    log("Output feature collection")
    out_features = route_features
    if out_points:
        out_features += features_ordered

    collection = {
        'type': 'FeatureCollection',
        'features': out_features}

    click.echo(json.dumps(collection))

if __name__ == "__main__":
    optimal_tour()
