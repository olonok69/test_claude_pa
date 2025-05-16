# Sentiment Analysys Endpoint

file https://dev.azure.com/sceven/DataDetect/_git/Detect-AI?path=/nlp/app/endpoint_sentiment-exp.py


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


## Local Version using Detect

Testing Notebook [here](Notebooks/API-classification-endpoint.ipynb)

Endpoint runing in port 5005 under directory get-index-docs. Expect only POST request.
The request is a dictionary with the following keys 

- query : query to send to Elastic search
- type : type query search_v2-->Internal Docker or outside--> External URL
- rindex : Index where to look for documents
- rindex_post : index where to post outcomes. It has to be a sentiment index
- num_docs : number of doct to post to the bulk index API
- file_types_all : bool if to use default file types or what it is included in this query
- filenames_types : list[strings] list of extensions to use case that file_types_all = True 
- labels : string a list of words concatenated with "_" that the model will use to classify the document on the multilabel/topic classification

Internally we have 3 models in this endpoint:
    
    - A Multilabel/topic classifier which returns you a score versus the keywords we send in the key labels
    - A Document summarizer or keyword extractor which extracts the most representative keywords which describe the content of the document
    - A profanity/toxicity analyser which returns you a score versus 7 toxicity classes  

### EXAMPLE

```python
# query to find documents
query = {
    "pit": {

        "id": ""

    },
    "query":{
        "bool":{
         "must":[
            {
               "exists":{
                  "field":"content"
               }
            },
            {
               "bool":{
                  "should":[
                     {
                        "term":{
                           "file_type":"docx"
                        }
                     },
                     {
                        "term":{
                           "file_type":"doc"
                        }
                     }
                     
                  ]
                    
               }
            },
            {
               "range":{
                  "fs.size":{
                     "gt":100,
                     "lt":5000000
                  }
               }
            }
         ]
      }
   },
    "from": 0,
    "size": 10000,
    "sort": [
        {
            "fs.size": {
                "order": "asc"
            }
        }
    ]
}

# create request
data = {}
data['query'] = query
data['type'] = "search_v2" # ingest or search
data['index'] = "unbias_it_data-doc" # control_data_set_5_resumes_demo-doc  # enron_data_set_demo_1-doc
data['index_post'] = "unbias_it_data-doc-sentiment"
data['labels'] = "fashion_business_finance_human resources_technology_international_politics_health_family_education_energy_mining_resume"
data['num_docs'] = 1000
data['file_types_all'] = 'False'
data['filenames_types']= ["doc", "docx", "pdf"]

# encode dict to bytes
data1 = json.dumps(data).encode()

# Send request to API
url = "http://localhost:5005/get-index-docs" 

try:
    r = requests.post(url, data=data1)
    print(r.text)
finally:

    pass
```

### RESPONSE

```python
{'status': 'SUCCESS',
 'Number doc read ': '6',
 'Number doc posted ': '6',
 'Total Time': '0:00:27.100904'}
```
### Document posted to the Index

```python
{
    "language": {
        "language": "en",
        "confidence": "1.0"
    },
    "file_name": "UnBiasIt Data Detect updated data set.xlsx",
    "file_type": "xlsx",
    "scan_id": "3a8fcee484eaef0beaf751d7236367029299acd58af319000b899e2e2f43b30b",
    "file_uri": "file:///home/demofilesystem/test_data/UnBiasIT%20Data%20Set/UnBiasIt%20Data%20Detect%20updated%20data%20set.xlsx",
    "embedding": [],
    "classification_labels": [
        {
            "score": {
                "name": "education",
                "score": 0.23322
            }
        },
        {
            "score": {
                "name": "health",
                "score": 0.20486
            }
        },
        {
            "score": {
                "name": "human resources",
                "score": 0.20012
            }
        },
        {
            "score": {
                "name": "business",
                "score": 0.19186
            }
        },
        {
            "score": {
                "name": "technology",
                "score": 0.15991
            }
        },
        {
            "score": {
                "name": "energy",
                "score": 0.15924
            }
        },
        {
            "score": {
                "name": "international",
                "score": 0.1465
            }
        },
        {
            "score": {
                "name": "mining",
                "score": 0.14572
            }
        },
        {
            "score": {
                "name": "family",
                "score": 0.13976
            }
        },
        {
            "score": {
                "name": "finance",
                "score": 0.13477
            }
        },
        {
            "score": {
                "name": "politics",
                "score": 0.13216
            }
        }
    ],
    "keywords": [
        {
            "score": {
                "name": "gender",
                "score": "0.4346"
            }
        },
        {
            "score": {
                "name": "cross",
                "score": "0.1897"
            }
        },
        {
            "score": {
                "name": "mentored",
                "score": "0.1868"
            }
        },
        {
            "score": {
                "name": "city",
                "score": "0.162"
            }
        },
        {
            "score": {
                "name": "performance",
                "score": "0.1512"
            }
        },
        {
            "score": {
                "name": "office",
                "score": "0.1502"
            }
        },
        {
            "score": {
                "name": "reasonable",
                "score": "0.1262"
            }
        },
        {
            "score": {
                "name": "credit",
                "score": "0.125"
            }
        },
        {
            "score": {
                "name": "cummings",
                "score": "0.0951"
            }
        },
        {
            "score": {
                "name": "toby",
                "score": "0.0288"
            }
        }
    ],
    "toxic_labels": [
        {
            "score": {
                "name": "toxicity",
                "score": 0.00642
            }
        },
        {
            "score": {
                "name": "severe_toxicity",
                "score": 0.00089
            }
        },
        {
            "score": {
                "name": "obscene",
                "score": 0.00142
            }
        },
        {
            "score": {
                "name": "identity_attack",
                "score": 0.00275
            }
        },
        {
            "score": {
                "name": "insult",
                "score": 0.00348
            }
        },
        {
            "score": {
                "name": "threat",
                "score": 0.00068
            }
        },
        {
            "score": {
                "name": "sexual_explicit",
                "score": 0.001
            }
        }
    ]
}

```

### Other testing Endpoints

We have another 2 endpoints to query keywords model and multilabel/topic classifier model. Endpoints --> api/keywords and /api/classifier

### Example api/keywords

```python
doc2 = """
    Computer Science is the study of computers and computational systems.
    Unlike electrical and computer engineers, computer scientists deal mostly
    with software and software systems; this includes their theory, design,
    development, and application. Principal areas of study within Computer
    Science include artificial intelligence, computer systems and networks,
    security, database systems, human computer interaction, vision and graphics,
    numerical analysis, programming languages, software engineering, bioinformatics
    and theory of computing. Although knowing how to program is essential to
    the study of computer science, it is only one element of the field. Computer
    scientists design and analyze algorithms to solve programs and study the
    performance of computer hardware and software. The problems that computer
    scientists encounter range from the abstract-- determining what problems
    can be solved with computers and the complexity of the algorithms that
    solve them – to the tangible – designing applications that perform well
    on handheld devices, that are easy to use, and that uphold security measures.
"""

text = " me llamo juan huertas y mi email es olonok@gmail.com"
data1 =  doc2.encode()

url = "http://localhost:5005/api/keywords" 

try:
    r = requests.post(url, data=data1)
    print(r.json())
finally:

    pass
```

### Output

```python
{
  "status": "SUCCESS",
  "data": {
    "computers": "0.6053",
    "bioinformatics": "0.3461",
    "electrical": "0.3338",
    "theory": "0.3067",
    "database": "0.2612",
    "principal": "0.195",
    "security": "0.1437",
    "languages": "0.1307",
    "vision": "0.0805",
    "element": "0.0796"
  }
}
```

### Example /api/classifier

```python
import os
files_path = "D:\\files\\nlp6"
file1 ="4SD.ThreeStoogesbw.OL.txt.txt"
file2 = "612CCORSONY2410.txt.txt"
file3 = "14070413.fs.txt"

# open files from filesystem
fin = open(os.path.join(files_path, file1), 'rb')
minuta = open(os.path.join(files_path, file2), 'rb')
data1=fin.read()
data2=minuta.read()
data3 = open(os.path.join(files_path, file3), 'rb').read()
payload_dict={'file1': data2, 'file2': data3}
# create payload to send API
labels = "business_financial_Human resources_technology_food_international"
# labels = "positive_negative_neutral"
# labels = "confidential_public_secret"
payload_dict={'file1': data1, 'file2': labels, 'mode':'False'}

# send request
url = "http://localhost:5005/api/classifier" 

try:
    r = requests.post(url, data=payload_dict)
    print(eval(r.text))
finally:
    pass

```
### Output

```python
{
  "status": "SUCCESS",
  "results": [
    {
      "score": {
        "name": "financial",
        "score": "0.227"
      }
    },
    {
      "score": {
        "name": "business",
        "score": "0.217"
      }
    },
    {
      "score": {
        "name": "technology",
        "score": "0.206"
      }
    },
    {
      "score": {
        "name": "international",
        "score": "0.205"
      }
    },
    {
      "score": {
        "name": "food",
        "score": "0.194"
      }
    },
    {
      "score": {
        "name": "Human resources",
        "score": "0.182"
      }
    }
  ]
}
```