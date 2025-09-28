Examples
========

Real-world examples of using KML ORM for various tasks.

Store Locator Analysis
----------------------

Analyze store locations and find optimal coverage areas:

.. code-block:: python

   from kmlorm import KMLFile
   from kmlorm.spatial import DistanceUnit, SpatialCalculations
   import pandas as pd

   def analyze_store_coverage(kml_file_path, city_center, max_distance=25):
       """Analyze store coverage for a city using spatial calculations."""
       kml = KMLFile.from_file(kml_file_path)

       # Get all stores (including those in folders)
       stores = kml.placemarks.all().filter(name__icontains='store')
       print(f"Total stores: {stores.count()}")

       # Find stores within city limits
       city_stores = stores.near(*city_center, radius_km=max_distance)
       print(f"Stores within {max_distance}km of city center: {city_stores.count()}")

       # Analyze coverage using built-in spatial calculations
       coverage_analysis = []
       for store in city_stores:
           if store.coordinates:
               # Use built-in distance calculation
               distance_to_center = store.distance_to(city_center)
               bearing_to_center = store.bearing_to(city_center)

               coverage_analysis.append({
                   'name': store.name,
                   'address': store.address,
                   'distance_to_center': distance_to_center,
                   'bearing_to_center': bearing_to_center,
                   'longitude': store.longitude,
                   'latitude': store.latitude,
               })

       # Convert to DataFrame for analysis
       df = pd.DataFrame(coverage_analysis)
       df = df.sort_values('distance_to_center')

       print("\nClosest stores to city center:")
       print(df.head().to_string(index=False))

       # Find the store closest to city center
       if not df.empty:
           closest_store = city_stores[0]  # First in sorted list
           print(f"\nClosest store: {closest_store.name}")
           print(f"Distance: {closest_store.distance_to(city_center):.1f} km")
           print(f"Distance: {closest_store.distance_to(city_center, unit=DistanceUnit.MILES):.1f} miles")

           # Calculate midpoint between city center and closest store
           midpoint = closest_store.midpoint_to(city_center)
           print(f"Midpoint coordinates: {midpoint.longitude:.4f}, {midpoint.latitude:.4f}")

       return df

   # Usage
   baltimore_center = (-76.6, 39.3)
   coverage_df = analyze_store_coverage('stores.kml', baltimore_center)

Route Planning
--------------

Extract and analyze route data from KML paths:

.. code-block:: python

   def analyze_delivery_routes(kml_file_path):
       """Analyze delivery route efficiency."""
       kml = KMLFile.from_file(kml_file_path)

       routes = kml.paths.all()
       print(f"Found {routes.count()} delivery routes")

       route_analysis = []
       for route in routes:
           if route.coordinates:
               analysis = {
                   'route_name': route.name,
                   'total_points': len(route.coordinates),
                   'estimated_length': estimate_route_length(route.coordinates),
                   'start_point': route.coordinates[0] if route.coordinates else None,
                   'end_point': route.coordinates[-1] if route.coordinates else None,
               }
               route_analysis.append(analysis)

       # Sort by length
       route_analysis.sort(key=lambda x: x['estimated_length'], reverse=True)

       print("\nLongest routes:")
       for route in route_analysis[:5]:
           print(f"- {route['route_name']}: {route['estimated_length']:.1f}km")

       return route_analysis

   def estimate_route_length(coordinates):
       """Estimate total route length using spatial calculations."""
       from kmlorm.models.point import Coordinate

       if len(coordinates) < 2:
           return 0

       total_length = 0
       for i in range(1, len(coordinates)):
           # Calculate distance between consecutive points
           prev_coord = Coordinate(longitude=coordinates[i-1][0], latitude=coordinates[i-1][1])
           curr_coord = Coordinate(longitude=coordinates[i][0], latitude=coordinates[i][1])

           # Use built-in distance calculation
           segment_length = prev_coord.distance_to(curr_coord)
           total_length += segment_length

       return total_length

   # Usage
   route_data = analyze_delivery_routes('delivery_routes.kml')

Geographic Data Validation
--------------------------

Validate and clean geographic data:

.. code-block:: python

   from kmlorm.core.exceptions import KMLValidationError

   def validate_geographic_data(kml_file_path):
       """Validate and report issues with geographic data."""
       kml = KMLFile.from_file(kml_file_path)

       validation_report = {
           'total_elements': 0,
           'valid_elements': 0,
           'invalid_elements': [],
           'missing_coordinates': [],
           'duplicate_names': [],
       }

       # Check placemarks
       all_placemarks = kml.placemarks.all()
       validation_report['total_elements'] = len(all_placemarks)

       names_seen = set()
       for placemark in all_placemarks:
           # Check for duplicates
           if placemark.name in names_seen:
               validation_report['duplicate_names'].append(placemark.name)
           names_seen.add(placemark.name)

           # Check coordinates
           if not placemark.coordinates:
               validation_report['missing_coordinates'].append(placemark.name)
               continue

           # Validate coordinates
           try:
               if placemark.validate():
                   validation_report['valid_elements'] += 1
           except KMLValidationError as e:
               validation_report['invalid_elements'].append({
                   'name': placemark.name,
                   'error': str(e)
               })

       # Generate report
       print("=== Geographic Data Validation Report ===")
       print(f"Total elements: {validation_report['total_elements']}")
       print(f"Valid elements: {validation_report['valid_elements']}")
       print(f"Invalid elements: {len(validation_report['invalid_elements'])}")
       print(f"Missing coordinates: {len(validation_report['missing_coordinates'])}")
       print(f"Duplicate names: {len(validation_report['duplicate_names'])}")

       if validation_report['invalid_elements']:
           print("\nInvalid elements:")
           for item in validation_report['invalid_elements']:
               print(f"- {item['name']}: {item['error']}")

       if validation_report['missing_coordinates']:
           print(f"\nElements missing coordinates:")
           for name in validation_report['missing_coordinates'][:10]:  # Show first 10
               print(f"- {name}")

       return validation_report

   # Usage
   report = validate_geographic_data('locations.kml')

Data Access with to_dict() Methods
------------------------------------

Convert KML objects to Python dictionaries for further processing:

.. code-block:: python

   # Load KML file
   kml = KMLFile.from_file('stores.kml')

   # Convert individual placemarks to dictionaries
   for placemark in kml.placemarks.has_coordinates():
       placemark_dict = placemark.to_dict()
       print(f"Placemark: {placemark_dict['name']}")
       print(f"Coordinates: {placemark_dict['coordinates']}")
       print(f"Point data: {placemark_dict['point']}")

   # Convert all placemarks to a list of dictionaries
   all_placemarks = [p.to_dict() for p in kml.placemarks.all()]
   print(f"Converted {len(all_placemarks)} placemarks to dictionaries")

   # Access coordinate data
   for placemark in kml.placemarks.has_coordinates():
       point_dict = placemark.point.to_dict()
       coord_dict = placemark.point.coordinates.to_dict()

       print(f"Point: {point_dict}")
       print(f"Coordinates: {coord_dict}")

   # Use dictionaries with external libraries (user's choice)
   # Example: JSON serialization
   import json
   json_data = json.dumps(all_placemarks, indent=2)

   # Example: Create your own export function
   def save_as_csv(placemarks, filename):
       """User-defined function using to_dict() data."""
       import csv
       if not placemarks:
           return

       with open(filename, 'w', newline='') as f:
           writer = csv.DictWriter(f, fieldnames=placemarks[0].keys())
           writer.writeheader()
           writer.writerows(placemarks)

Spatial Analysis
----------------

Perform spatial analysis on KML data:

.. code-block:: python

   def find_clusters(kml_file_path, cluster_radius=5):
       """Find clusters of nearby placemarks using spatial calculations."""
       from kmlorm.spatial import SpatialCalculations

       kml = KMLFile.from_file(kml_file_path)

       placemarks_with_coords = kml.placemarks.all().has_coordinates()
       clusters = []
       processed = set()

       for i, placemark in enumerate(placemarks_with_coords):
           if i in processed:
               continue

           # Find nearby placemarks using built-in spatial calculations
           nearby = []
           center = (placemark.longitude, placemark.latitude)

           for j, other in enumerate(placemarks_with_coords):
               if j != i and j not in processed:
                   # Use built-in distance calculation
                   distance = placemark.distance_to(other)
                   if distance <= cluster_radius:
                       nearby.append((j, other))

           if nearby:
               # Calculate cluster centroid using midpoint calculations
               cluster_points = [placemark] + [p[1] for p in nearby]

               # Calculate average bearing to understand cluster spread
               bearings = [placemark.bearing_to(other) for _, other in nearby]
               avg_bearing = sum(bearings) / len(bearings) if bearings else 0

               cluster = {
                   'center_placemark': placemark,
                   'nearby_placemarks': [p[1] for p in nearby],
                   'total_count': len(nearby) + 1,
                   'center_coordinates': center,
                   'average_bearing': avg_bearing,
                   'max_distance': max(placemark.distance_to(other) for _, other in nearby) if nearby else 0
               }
               clusters.append(cluster)
               processed.add(i)
               processed.update(p[0] for p in nearby)

       # Sort clusters by size
       clusters.sort(key=lambda x: x['total_count'], reverse=True)

       print(f"Found {len(clusters)} clusters:")
       for i, cluster in enumerate(clusters[:5]):  # Show top 5
           print(f"Cluster {i+1}: {cluster['total_count']} placemarks")
           print(f"  Center: {cluster['center_placemark'].name}")
           print(f"  Location: {cluster['center_coordinates']}")
           print(f"  Max distance from center: {cluster['max_distance']:.1f} km")

       return clusters

   # Usage
   clusters = find_clusters('locations.kml', cluster_radius=10)

Data Quality Assessment
-----------------------

Assess the quality of KML data:

.. code-block:: python

   def assess_data_quality(kml_file_path):
       """Comprehensive data quality assessment."""
       kml = KMLFile.from_file(kml_file_path)

       quality_metrics = {
           'completeness': {},
           'accuracy': {},
           'consistency': {},
           'coverage': {}
       }

       all_placemarks = kml.placemarks.all()
       total_count = len(all_placemarks)

       # Completeness metrics
       with_names = sum(1 for p in all_placemarks if p.name)
       with_coords = sum(1 for p in all_placemarks if p.coordinates)
       with_descriptions = sum(1 for p in all_placemarks if p.description)
       with_addresses = sum(1 for p in all_placemarks if p.address)

       quality_metrics['completeness'] = {
           'total_records': total_count,
           'name_completion': with_names / total_count * 100,
           'coordinate_completion': with_coords / total_count * 100,
           'description_completion': with_descriptions / total_count * 100,
           'address_completion': with_addresses / total_count * 100,
       }

       # Accuracy metrics (coordinate validation)
       valid_coords = 0
       invalid_coords = []
       for placemark in all_placemarks:
           if placemark.coordinates:
               try:
                   if placemark.validate():
                       valid_coords += 1
               except KMLValidationError:
                   invalid_coords.append(placemark.name)

       quality_metrics['accuracy'] = {
           'valid_coordinates': valid_coords / with_coords * 100 if with_coords > 0 else 0,
           'invalid_coordinate_count': len(invalid_coords),
       }

       # Consistency metrics
       name_lengths = [len(p.name) for p in all_placemarks if p.name]
       duplicate_names = len(all_placemarks) - len(set(p.name for p in all_placemarks if p.name))

       quality_metrics['consistency'] = {
           'duplicate_names': duplicate_names,
           'avg_name_length': sum(name_lengths) / len(name_lengths) if name_lengths else 0,
           'name_length_std': calculate_std_dev(name_lengths) if name_lengths else 0,
       }

       # Geographic coverage
       if with_coords > 0:
           lats = [p.latitude for p in all_placemarks if p.coordinates]
           lons = [p.longitude for p in all_placemarks if p.coordinates]

           quality_metrics['coverage'] = {
               'lat_range': (min(lats), max(lats)),
               'lon_range': (min(lons), max(lons)),
               'geographic_spread': max(lats) - min(lats) + max(lons) - min(lons),
           }

       # Print report
       print("=== Data Quality Assessment ===")
       print(f"Dataset size: {total_count} placemarks")
       print(f"Coordinate coverage: {quality_metrics['completeness']['coordinate_completion']:.1f}%")
       print(f"Name coverage: {quality_metrics['completeness']['name_completion']:.1f}%")
       print(f"Coordinate accuracy: {quality_metrics['accuracy']['valid_coordinates']:.1f}%")
       print(f"Duplicate names: {quality_metrics['consistency']['duplicate_names']}")

       return quality_metrics

   def calculate_std_dev(values):
       """Calculate standard deviation."""
       if len(values) < 2:
           return 0
       mean = sum(values) / len(values)
       variance = sum((x - mean) ** 2 for x in values) / len(values)
       return variance ** 0.5

   # Usage
   quality_report = assess_data_quality('dataset.kml')

Batch Processing
----------------

Process multiple KML files:

.. code-block:: python

   import os
   from pathlib import Path

   def batch_process_kml_files(directory_path, output_dir):
       """Process all KML files in a directory."""
       kml_files = Path(directory_path).glob('*.kml')
       results = []

       for kml_file in kml_files:
           try:
               print(f"Processing {kml_file.name}...")
               kml = KMLFile.from_file(str(kml_file))

               # Extract summary information
               summary = {
                   'filename': kml_file.name,
                   'document_name': kml.document_name,
                   'placemark_count': kml.placemarks.all().count(),
                   'folder_count': kml.folders.all().count(),
                   'path_count': kml.paths.all().count(),
                   'polygon_count': kml.polygons.all().count(),
                   'has_coordinates': kml.placemarks.all().has_coordinates().count(),
               }

               results.append(summary)

               # Export each file to CSV
               output_csv = Path(output_dir) / f"{kml_file.stem}.csv"
               export_to_csv(str(kml_file), str(output_csv))

           except Exception as e:
               print(f"Error processing {kml_file.name}: {e}")
               results.append({
                   'filename': kml_file.name,
                   'error': str(e)
               })

       # Create summary report
       summary_path = Path(output_dir) / 'batch_summary.csv'
       with open(summary_path, 'w', newline='') as f:
           if results and 'error' not in results[0]:
               fieldnames = results[0].keys()
               writer = csv.DictWriter(f, fieldnames=fieldnames)
               writer.writeheader()
               writer.writerows(results)

       print(f"Processed {len(results)} files. Summary saved to {summary_path}")
       return results

   # Usage
   results = batch_process_kml_files('./kml_files/', './output/')

These examples demonstrate practical applications of KML ORM for real-world geospatial data processing tasks. Each example can be adapted and extended based on your specific needs.