# Processes the electronic navigational charts, which are S57 files (https://www.charts.noaa.gov/ENCs/ENCs.shtml)
# Generates and saves the labels of all permanent marine structures specified in the list, want_layers, in detection+spatial format
# This script currently treats all geometric features (POINTS, LINESTRINGS, POLYGONS) as bounding box detections.
#
# example command: python process_noaa_enc.py all /multisat/labels/noaa_enc_path/ 

import os
import sys
import math
import json
import geojson

from pathlib import Path
from osgeo import osr
from osgeo import ogr
from osgeo import gdal as gdal

from shapely.geometry import Polygon
from shapely.geometry import LineString


# The user needs to specify the NOAA ENC category they want labels for
if len(sys.argv) < 3:
    print("Please specify the NOAA ENC category you want to process and an out_dir.")
    exit()
else:
    task = sys.argv[1]  # {'bridge', 'buoy', 'dam', ...} OR 'all' to include all NOAA ENC classes in our dataset
    out_dir = sys.argv[2]  # /multisat/labels/X/

in_dir = '/Users/virajgoyal/Documents/Documents - Viraj’s MacBook Pro/UW/CSE 493G1/Satlas Research/ENC_ROOT/'

# Dictionary to map the marine structure codes to classes within our dataset
# NOTE: this dictionary contains all categories we've looked into, but want_layers doesn't need to use all of them
classes = {'OFSPLF': 'platform'}

# Layers we are interested in getting labels for...
if task == 'all':
    want_layers = ['OFSPLF']
else:
    want_layers = [k for k,v in classes.items() if v == task]

# features is a dictionary of distinct objects where the key is the finer category
features = {}

# offshore platform types
id_to_cat = {'1': 'oil derrick/rig', '2': 'production platform', '3': 'observation/research platform',
             '4': 'articulated loading platform (ALP)', '5': 'single anchor leg mooring (SALM)',
             '6': 'mooring tower', '7': 'artificial island', '8': 'floating production, storage and off-loading vessel (FPSO)',
             '9': 'accommodation platform', '10': 'navigation, communication and control buoy (NCCB)'}

# Iterate over every file, and process the .000 files by finding and creating point labels
pathlist = Path(in_dir).rglob('*.000')
for path in pathlist:
    path = str(path)

    # Open the S57 file, outputs osgeo.ogr DataSource object
    ds = ogr.Open(path, 0)  # 0 means read-only

    # Iterate over the layers and extract labels/coordinates from ones we're interseted in
    layer_count = ds.GetLayerCount()
    for i in range(layer_count):
        layer = ds.GetLayerByIndex(i)

        # Only want to dig into layers with features we're interested in
        if not layer.GetName() in want_layers:
            continue

        # Class name, as in the dataset
        cls = classes[layer.GetName()]

        # Iterate over features in the current file and layer
        for feature in layer:
            # load each feature 
            feature = json.loads(feature.ExportToJson())
            geometry = feature['geometry']
            geom_type = geometry['type']

            final_coordinates = None
            if geom_type == 'Point':
                final_coordinates = tuple(geometry['coordinates'])
            elif geom_type == 'Polygon':
                coordinates = geometry['coordinates']
                coordinates_tuples = [tuple(coord) for sublist in coordinates for coord in sublist]
                polygon = Polygon(coordinates_tuples)
                final_coordinates = tuple([polygon.centroid.x, polygon.centroid.y])
            elif geom_type == 'LineString':
                print("Invalid Type")
                coordinates = geometry['coordinates']
                coordinates_tuples = [tuple(coord) for sublist in coordinates for coord in sublist]
                line_string = LineString(coordinates_tuples)
                final_coordinates = tuple([line_string.centroid.x, line_string.centroid.y])
            
            # get category of offshore platforms
            final_category = "offshore_platform"
            if feature['properties']['CATOFP'] is not None:
                # special case encountered once
                if len(feature['properties']['CATOFP']) > 1:
                    print(f"More than 1: {feature['properties']['CATOFP']}")

                final_category = id_to_cat[feature['properties']['CATOFP'][0]]

            curr_feature = geojson.Feature(geometry = geojson.Point(final_coordinates), 
                           properties = {"category": "offshore_platform", 
                                         "finer_category": final_category})
            
            if final_category in features:
                features[final_category].append(curr_feature)
            else:
                features[final_category] = [curr_feature]


# Now for each distinct finer category in the dictionary, write out its features to separate geojson files.
for k,v in features.items():
    curr_feature_collection = geojson.FeatureCollection(v)
    modified_k = k.replace('/', '_')
    output_geojson = out_dir + modified_k + '.geojson'
    with open(output_geojson, 'w') as f:
        geojson.dump(curr_feature_collection, f, indent=2)