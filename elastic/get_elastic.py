import requests
import json

# Replace with your Elasticsearch host and index name
es_host = "http://135.234.233.194:9200"
index_name = "curated_data_set_jg_test-doc"

# Make the request to get the mapping
response = requests.get(f"{es_host}/{index_name}/_mapping")

# Check if the request was successful
if response.status_code == 200:
    mapping = response.json()
    with open("mapping.json", "w") as f:
        json.dump(mapping, f, indent=4)

else:
    print(f"Error: {response.status_code}")
