# Optimal Tour

A convenient command-line interface for solving the classic
[Traveling Salesman Problem](https://simple.wikipedia.org/wiki/Travelling_salesman_problem) (TSP)

Given locations as GeoJSON point features, find the shortest tour (based on driving travel times) visiting all points.

    fio cat point_locations.shp | optimal_tour > points_plus_route.geojson

<img src="tour.png" width="50%">

## Usage

```
$ optimal_tour.py --help
Usage: optimal_tour.py [OPTIONS] FEATURES...

  A command line interface for solving the traveling salesman problem

  Input geojson features with point geometries and output the optimal tour
  as geojson feature collection.

     $ optimal_tour waypoints.geojson | geojson-summary
     19 points and 1 line

  If using geodesic or directions modes, input must be in lonlat coordinates

  Directions mode requires a Mapbox account and a valid token set as the
  MAPBOX_ACCESS_TOKEN environment variable.

Options:
  --mode [directions|geodesic|cartesian]
                                  Mode for calculating travel costs between
                                  points
  --profile [driving|cycling|walking]
                                  Mapbox profile if using directions
  --out-points / --no-out-points  output points along with tour linestring
  --help                          Show this message and exit.
```

## Installation

1. Install the [concorde](http://www.math.uwaterloo.ca/tsp/concorde.html) TSP solver according to [these instructions](https://github.com/perrygeo/pyconcorde/wiki/Installing-Concorde)
1. Install python dependencies with `pip install -r requirements.txt`
1. If you want to use directions mode, you'll need a [Mapbox account](https://www.mapbox.com/studio/signup/) and a valid token set as the `MAPBOX_ACCESS_TOKEN` environment variable.
1. Test it: `optimal_tour.py < waypoints.txt` and you should see a geojson feature collection printed to stdout.

## TODO 

This is just a proof of concept. The continued development will be driven by our
collective interest in the project so please contact me via github issues if you have ideas.
