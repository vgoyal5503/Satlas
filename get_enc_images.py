import os
import json
import math
from tqdm import tqdm
import io
import numpy as np
import rasterio.features
import requests
import skimage.io
from intersect_satlas_enc import intersections

import multisat.util
from PIL import Image
from PIL.PngImagePlugin import PngInfo

sentinel2_url = 'https://se-tile-api.allen.ai/image_mosaic/sentinel2/[LABEL]/tci/[ZOOM]/[COL]/[ROW].png'
chip_size = 512

def get_sentinel2_callback(label):
    def callback(tile):
        cur_url = sentinel2_url
        cur_url = cur_url.replace('[LABEL]', label)
        cur_url = cur_url.replace('[ZOOM]', '13')
        cur_url = cur_url.replace('[COL]', str(tile[0]))
        cur_url = cur_url.replace('[ROW]', str(tile[1]))

        response = requests.get(cur_url)
        if response.status_code != 200:
            print('got status_code={} url={}'.format(response.status_code, cur_url))
            if response.status_code == 404 or response.status_code == 500:
                return np.zeros((chip_size, chip_size, 3))
            raise Exception('bad status code {}'.format(response.status_code))

        buf = io.BytesIO(response.content)
        im = skimage.io.imread(buf)
        return im

    return callback

directory_path = 'ENC_JSONS'
enc_objects = {}
final_labels = {
    'production platform': '0',
    'oil derrick/rig': '1',
    'observation/research platform': '2'
}

# Get enc objects
for file_name in os.listdir(directory_path):
    if (file_name).endswith('.geojson'):
        file_path = os.path.join(directory_path, file_name)

        # Open and Read GeoJson file
        with open(file_path, 'r') as curr_enc:
            curr_enc_data = json.load(curr_enc)
            enc_obj_name = curr_enc_data["features"][0]["properties"]["finer_category"]
            enc_objects[enc_obj_name] = curr_enc_data["features"]

crop_size = 64
datapoint_num = 0
time = '2024-01'
for finer_category, category_list in enc_objects.items():
    if (finer_category == 'oil derrick/rig' or finer_category == 'production platform' or 
        finer_category == 'observation/research platform'):
        intersected_enc_objs = intersections[finer_category]
        num_enc_entries = len(category_list)
        decimals = 4
        curr_label = final_labels[finer_category]
        for i in tqdm(range(num_enc_entries), desc=finer_category, unit="iteration"):
            curr_enc_object = category_list[i]
            coords = curr_enc_object["geometry"]["coordinates"]
            long = coords[0]
            lat = coords[1]
            intersects_w_satlas = curr_enc_object in intersected_enc_objs
            # alaska covered in darkness
            if long > -150:
                if ((finer_category == 'production platform')
                    and not intersects_w_satlas):
                    continue
                else:
                    curr_datapoint = 'datapoint_' + str(datapoint_num)
                    first_img_dir = os.path.join('finer_platform_classification', curr_datapoint)
                    if not os.path.exists(first_img_dir):
                        os.makedirs(first_img_dir)
                    
                    label_dir = f"{first_img_dir}/gt.txt"
                    with open(label_dir, 'w') as file:
                        file.write(curr_label)
                    
                    next_img_dir = os.path.join(first_img_dir, 'images')
                    if not os.path.exists(next_img_dir):
                        os.makedirs(next_img_dir)

                    curr_img_dir = os.path.join(next_img_dir, curr_datapoint)
                    if not os.path.exists(curr_img_dir):
                        os.makedirs(curr_img_dir)

                    file_name = str(round(long, decimals)) + '_' + str(round(lat, decimals))
                    out_fname = os.path.join(curr_img_dir, '{}.png'.format('tci'))

                    col, row = multisat.util.geo_to_mercator((long, lat), zoom=13, pixels=512)

                    callback = get_sentinel2_callback(time)
                    im = multisat.util.load_window_callback(callback, int(col) - (crop_size//2), 
                                                            int(row) - (crop_size//2), crop_size, crop_size)
                    skimage.io.imsave(out_fname, im, check_contrast=False)

                    image = Image.open(out_fname)

                    metadata = PngInfo()
                    metadata.add_text('timestamp', time)
                    metadata.add_text('noaa_enc_label', curr_label)
                    metadata.add_text('satlas_intersection', str(intersects_w_satlas))
                    
                    image.save(out_fname, pnginfo=metadata)

                    datapoint_num += 1

print("Done getting corresponding Satlas images to ENC data")


