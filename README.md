# Satlas
Performing Finer-Grained Classification of Offshore Marine Platforms

# Dataset Info
This repository contains the original dataset, which has 2280 examples, and the refined dataset, which has 1847 examples. Each of these 1847 examples has 3 images associated with it.
The true label is located in the 'gt.txt' files. For the original dataset, 0 corresponds to the catch-all offshore platform category, 1 corresponds to production platforms, 2 corresponds
to oil derricks/rigs, and 3 corresponds to observation/research platforms. For the refined dataset, 0 corresponds to production platforms, 1 corresponds
to oil derricks/rigs, and 2 corresponds to observation/research platforms.

# Python Script Info
The process_noaa_enc.py script processes the NOAA ENC data. It saves the labels of all offshore marine platforms specified in the raw NOAA ENC data to separate .geojson files for
each distinct category of offshore platform. These .geojson files live under ENC_JSONS.

The intersect_satlas_enc.py script intersects all the marine objects derived from the NOAA ENC data with the objects that are currently in the Satlas data. It then outputs how many matches we found.

The get_enc_images.py script calls an internal Allen Institute for AI (AI2) url to retrieve the Sentinel-2 images corresponding to the images we desire. It also puts all the images and true label files
into a directory format that AI2's internal multisat training library supports.
