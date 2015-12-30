# Optimal Tour

A convenient command-line interface for solving the classic
[*Traveling Salesman Problem*](https://simple.wikipedia.org/wiki/Travelling_salesman_problem) (TSP)

Given locations as GeoJSON point features, find the shortest tour (based on driving travel times) visiting all points.

    fio cat point_locations.shp | optimal_tour > points_plus_route.geojson

<img src="tour.png" width="50%">

## Dependencies

* [Mapbox APIs](https://www.mapbox.com/developers/) for directions and distance matrix
* [pyconcorde](https://github.com/perrygeo/pyconcorde) to interface with...
* [concorde](http://www.math.uwaterloo.ca/tsp/concorde.html) TSP solver
* `click` and `cligj` python libs

## TODO 

This is just a proof of concept. The continued development will be driven by our
collective interest in the project so please contact me via github issues if you have ideas.
