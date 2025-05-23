import numpy as np
from sklearn.cluster import KMeans, DBSCAN
from sklearn.preprocessing import StandardScaler
import os 
import json

from IPython import embed


def read_json_data(file_path):
    with open(file_path) as json_file:
        return json.load(json_file)

def json_to_list(json_dict, replace_nans=False, replacement_value=0):
    badge_ids = []
    embeddings = []
    nan_count = 0  # Track embeddings with NaNs

    for badge_id, embedding in json_dict.items():
        embedding_array = np.array(embedding[0], dtype=np.float32)
        
        # Check for NaNs in the embedding
        if np.isnan(embedding_array).any():
            nan_count += 1
            if replace_nans:
                # Replace NaNs with a specified value
                embedding_array = np.nan_to_num(embedding_array, nan=replacement_value)
        
        badge_ids.append(badge_id)
        embeddings.append(embedding_array)
    
    if nan_count > 0:
        print(f"Found NaNs in {nan_count} embeddings. {'Replaced NaNs with ' + str(replacement_value) if replace_nans else 'No replacements made.'}")
    
    return badge_ids, embeddings


badge_ids, session_embeddings = json_to_list(read_json_data("/mnt/wolverine/home/samtukra/LLMU/embeddings/new_claire_db/fluff/session_embeddings_Meta-Llama-3-8B.json"))
cluster_ids, cluster_embeddings = json_to_list(read_json_data("/mnt/wolverine/home/samtukra/LLMU/embeddings/cluster_numeculature_embeddings_Meta-Llama-3-8B.json"))
embed()