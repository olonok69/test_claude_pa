# Classification (PII/PHI detector)

file https://dev.azure.com/sceven/DataDetect/_git/Detect-AI?path=/nlp/app/endpoint_classification.py

## Endpoint to integrate with Detect
Testing Notebook [here](Notebooks/new_api-classification.ipynb)

Endpoint runing in port 5000 under directory process-tika-output. Expect only POST request. This endpoint take directly the output from tika and return a list of objects to fit into a classification index

Example:

```python
# in this json file we have output of 100 documents returned from TIKA
with open("test-data.json", "rb") as f:
    docs = f.read() 

d =docs.decode()
docs = json.loads(d)
data1 = json.dumps(docs).encode()

# PII/PHI classification
url = "http://localhost:5000/process-tika-output" 

try:
    r = requests.post(url, data=data1)
    print(r.json())
finally:

    pass
```

### RESPONSE

The endpoint return a list of classification objects, ready to be load into a classification index

```python
[
  {
    "language": {
      "language": "vi",
      "confidence": "1.0"
    },
    "file_name": "Word6.doc",
    "file_type": "doc",
    "scan_id": "c5613d504ddd3367d15ba6ab9245c062018fa21135aec4d452f9b3e4d88c441b",
    "file_uri": "file:///home/demofilesystem/test_data/Large%20Control%20DataSet/Office%20Files%20and%20Documents/DOC/Word6.doc",
    "pii_type_detected": "LOCATION",
    "risk_level": 2,
    "risk_level_definition": "Semi-Identifiable",
    "cluster_membership_type": "Secure Identifiers",
    "hipaa_category": "Protected Health Information",
    "dhs_category": "Not Mentioned",
    "nist_category": "Linkable",
    "entity_type": "LOCATION",
    "score": 0.85,
    "start": 132,
    "end": 136,
    "pii_text": "sông"
  },
  {
    "language": {
      "language": "vi",
      "confidence": "1.0"
    },
    "file_name": "Word6.doc",
    "file_type": "doc",
    "scan_id": "c5613d504ddd3367d15ba6ab9245c062018fa21135aec4d452f9b3e4d88c441b",
    "file_uri": "file:///home/demofilesystem/test_data/Large%20Control%20DataSet/Office%20Files%20and%20Documents/DOC/Word6.doc",
    "pii_type_detected": "DATE_TIME",
    "risk_level": 2,
    "risk_level_definition": "Semi-Identifiable",
    "cluster_membership_type": "Basic Demographics",
    "hipaa_category": "Protected Health Information",
    "dhs_category": "Linkable",
    "nist_category": "Linkable",
    "entity_type": "DATE_TIME",
    "score": 0.85,
    "start": 137,
    "end": 141,
    "pii_text": "chợ"
  }
]
```
