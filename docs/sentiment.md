# Sentiment Analysys Endpoint

file https://dev.azure.com/sceven/DataDetect/_git/Detect-AI?path=/nlp/app/endpoint_sentiment.py


## Endpoint to integrate with Detect
Testing Notebook [here](Notebooks/new_api-sentiment-endpoint.ipynb)

Endpoint runing in port 5005 under directory process-tika-output. Expect only POST request. This endpoint take directly the output from tika and return a list of objects to fit into a sentiment index
The endpoint receives a dictionary with 2 keys
- labels : string a list of words concatenated with "_" that the model will use to classify the document on the multilabel/topic classification
- docs: output from TIKA

Example


```python
# in this json file we have output of 100 documents returned from TIKA
with open("test-data.json", "rb") as f:
    docs = f.read() 

d =docs.decode()
docs = json.loads(d)
data1 = json.dumps(docs).encode()

# Sentiment Classification
url = "http://localhost:5005/process-tika-output" 

try:
    r = requests.post(url, data=data1)
    print(r.json())
finally:

    pass
```
### RESPONSE

The endpoint return a list of classification objects, ready to be load into a sentiment index

```python
[
  {
    "language": {
        "language": "en",
        "confidence": "1.0"
    },
    "file_name": "Sinclair Rider C.docx",
    "file_type": "docx",
    "scan_id": "3f958624a9ca1e9f2a55bce5f6c387cb5d779bb4c59c0845b66b6e19e2f289e6",
    "file_uri": "file:///home/demofilesystem/test_data/Large%20Control%20DataSet/Office%20Files%20and%20Documents/DOCX/Sinclair%20Rider%20C.docx",
    "embedding": [],
    "classification_labels": [
  
  ...... REMOVED FOR CLARITY ............  OTHER DOCUMENTS HERE

    "toxic_labels": [
        {
            "score": {
                "name": "toxicity",
                "score": 0.00037
            }
        },
        {
            "score": {
                "name": "severe_toxicity",
                "score": 3e-05
            }
        },
        {
            "score": {
                "name": "obscene",
                "score": 0.00015
            }
        },
        {
            "score": {
                "name": "identity_attack",
                "score": 0.00012
            }
        },
        {
            "score": {
                "name": "insult",
                "score": 0.00026
            }
        },
        {
            "score": {
                "name": "threat",
                "score": 4e-05
            }
        },
        {
            "score": {
                "name": "sexual_explicit",
                "score": 2e-05
            }
        }
    ]
}
]
```
