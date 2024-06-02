import os
import json
import math
from tqdm import tqdm

def coordinates_match(enc_coords, satlas_coords, decimal_places):
    delta = 10 ** (-decimal_places)
    return (abs(satlas_coords[0] - enc_coords[0]) < delta) and ((abs(satlas_coords[1] - enc_coords[1]) < delta))

directory_path = 'ENC_JSONS_UPDATED'
enc_objects = {}
satlas_object = {}
accepted_categories = {}
intersections = {}

# Get enc objects
for file_name in os.listdir(directory_path):
    if (file_name).endswith('.geojson'):
        file_path = os.path.join(directory_path, file_name)

        # Open and Read GeoJson file
        with open(file_path, 'r') as curr_enc:
            curr_enc_data = json.load(curr_enc)
            enc_obj_name = curr_enc_data["features"][0]["properties"]["finer_category"]
            enc_objects[enc_obj_name] = curr_enc_data["features"]

# Get satlas objects
with open('satlas.geojson', 'r') as satlas_file:
    curr_satlas_data = json.load(satlas_file)
    final_features = []
    for curr_feature in curr_satlas_data["features"]:
        curr_feature_category = curr_feature["properties"]["category"]
        if (curr_feature_category == "offshore_platform"):
            final_features.append(curr_feature)
    
    satlas_object["features"] = final_features

num_satlas_entries = len(satlas_object["features"])
total_matches = 0
for finer_category, category_list in enc_objects.items():
    num_enc_entries = len(category_list)
    threshold = 0.01
    decimals = 3
    num_matches_needed = math.ceil(num_enc_entries * threshold)
    num_matches = 0
    curr_intersections = []
    if (finer_category == 'oil derrick/rig' or finer_category == 'production platform' or 
        finer_category == 'observation/research platform' or finer_category == 'offshore_platform'):
        for i in tqdm(range(num_enc_entries), desc=finer_category, unit="iteration"):
            curr_enc_object = category_list[i]
            curr_match = False
            for j in range(num_satlas_entries - total_matches):
                curr_satlas_object = satlas_object["features"][j]
                match = coordinates_match(curr_enc_object["geometry"]["coordinates"], 
                                        curr_satlas_object["geometry"]["coordinates"], decimals)
                if match:
                    curr_match = True
                    # appends enc object, not satlas object now, just getting coordinates for now.
                    curr_intersections.append(curr_enc_object["geometry"]["coordinates"])
                    satlas_object["features"].remove(curr_satlas_object)
                    break
            
            if curr_match:
                num_matches += 1
                total_matches += 1
    
    #if num_matches >= num_matches_needed:
    accepted_categories[finer_category] = (num_matches_needed, num_matches, num_enc_entries)
    intersections[finer_category] = curr_intersections

print("Done Matching!")
print(accepted_categories)


