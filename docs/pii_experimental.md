# PII/PHI detector Experimental
Here we have Experimental Endpoints and Testing Endpoinds

file https://dev.azure.com/sceven/DataDetect/_git/Detect-AI?path=/nlp/app/endpoint_classification-exp.py

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





## Local Version using Detect
Testing Notebook [here](Notebooks/API-classification-endpoint.ipynb)

Endpoint runing in port 5000 under directory get-index-docs. Expect only POST request.
The request is a dictionary with the following keys 

- query : query to send to Elastic search
- type : type query search_v2-->Internal Docker or outside--> External URL
- rindex : Index where to look for documents
- rindex_post : index where to post outcomes. It has to be a classification index
- num_docs : number of doct to post to the bulk index API
- file_types_all : bool if to use default file types or what it is included in this query
- filenames_types : list[strings] list of extensions to use case that file_types_all = True 

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
data['index'] = "large_control_dataset-doc"
data['index_post'] = "large_control_dataset-doc-classification"
data['num_docs'] = 1000
data['file_types_all'] = 'False'
data['filenames_types']= ["doc", "docx"]

# encode dict to bytes
data1 = json.dumps(data).encode()

# Send request to API
url = "http://localhost:5000/get_index_docs" 

try:
    r = requests.post(url, data=data1)
    print(r.text)
finally:

    pass
```

### RESPONSE

```python
{'status': 'SUCCESS',
 'Number doc read ': '19743',
 'Number doc posted ': '830532',
 'Total Time': '10:05:42.326961'}
```
### Document posted to the Index

```python
{
    "language": {
        "language": "en",
        "confidence": "1.0"
    },
    "file_name": "NY Market Update -- March 2001.doc",
    "file_type": "doc",
    "scan_id": "00e7365ec6f72b0d18a954bc7640e1bbb781f87fd4b1f9091f10d70a8bcf8462",
    "file_uri": "file:///home/demofilesystem/test_data/Large%20Control%20DataSet/Office%20Files%20and%20Documents/DOC/NY%20Market%20Update%20--%20March%202001.doc",
    "pii_type_detected": "DATE_TIME",
    "risk_level": 2,
    "risk_level_definition": "Semi-Identifiable",
    "cluster_membership_type": "Basic Demographics",
    "hipaa_category": "Protected Health Information",
    "dhs_category": "Linkable",
    "nist_category": "Linkable",
    "entity_type": "DATE_TIME",
    "score": 0.85,
    "start": 21046,
    "end": 21059,
    "pii_text": "June 30, 2001"
}
```

### Other testing Endpoints

We have another 3 endpoints to query presidio with spanish language on the adresses pii-Analyzer-v2-spanish,  pii-Analyzer-v2 and anonymize

### Example pii-Analyzer-v2-spanish

```python
url = "http://localhost:5000/pii-Analyzer-v2-spanish" 

text = " me llamo juan huertas y mi email es olonok@gmail.com"
data1 = text.encode()

try:
    r = requests.post(url, data=data1)#files=files)
    print(r.json())
finally:

    pass
```

### Output

```python
{
  "data": [
    {
      "pii": "olonok@gmail.com",
      "type": "EMAIL_ADDRESS",
      "score": 1.0
    },
    {
      "pii": "juan huertas",
      "type": "PERSON",
      "score": 0.85
    },
    {
      "pii": "gmail.com",
      "type": "URL",
      "score": 0.5
    }
  ]
}
```

### Example pii-Analyzer-v2

```python
url = "http://localhost:5000/pii-Analyzer-v2" 

text = " me llamo juan huertas y mi email es olonok@gmail.com"
data1 = text.encode()

try:
    r = requests.post(url, data=data1)#files=files)
    print(r.json())
finally:

    pass
```
### Output

```python
[
  {
    "analysis": [
      {
        "pii_type_detected": "EMAIL_ADDRESS",
        "risk_level": 3,
        "risk_level_definition": "Identifiable",
        "cluster_membership_type": "Personal Preferences",
        "hipaa_category": "Protected Health Information",
        "dhs_category": "Stand Alone PII",
        "nist_category": "Directly PII",
        "entity_type": "EMAIL_ADDRESS",
        "score": 1.0,
        "start": 37,
        "end": 53
      },
      {
        "pii_type_detected": "PERSON",
        "risk_level": 3,
        "risk_level_definition": "Identifiable",
        "cluster_membership_type": "Financial Information",
        "hipaa_category": "Protected Health Information",
        "dhs_category": "Linkable",
        "nist_category": "Directly PII",
        "entity_type": "PERSON",
        "score": 0.85,
        "start": 10,
        "end": 22
      },
      {
        "pii_type_detected": "URL",
        "risk_level": 2,
        "risk_level_definition": "Semi-Identifiable",
        "cluster_membership_type": "Community Interaction",
        "hipaa_category": "Not Protected Health Information",
        "dhs_category": "Linkable",
        "nist_category": "Linkable",
        "entity_type": "URL",
        "score": 0.5,
        "start": 44,
        "end": 53
      }
    ],
    "index": 0,
    "risk_score_mean": 2.6666666666666665,
    "sanitized_text": " me llamo <REDACTED> y mi email es <REDACTED>"
  }
]
```

### Example anonymize

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
    Andrew will comment
"""
url = "http://localhost:5000/anonymizer" 

data1 = json.dumps(doc2).encode()

try:
    r = requests.post(url, data=data1)
    print(r.json())
finally:

    pass
```
### Output

```python

{'data': '"\\n    Computer Science is the study of computers and computational systems.\\n    Unlike electrical and computer engineers, computer scientists deal mostly\\n    with software and software systems; this includes their theory, design,\\n    development, and application. Principal areas of study within Computer\\n    Science include artificial intelligence, computer systems and networks,\\n    security, database systems, human computer interaction, vision and graphics,\\n    numerical analysis, programming languages, software engineering, bioinformatics\\n    and theory of computing. Although knowing how to program is essential to\\n    the study of computer science, it is only one element of the field. Computer\\n    scientists design and analyze algorithms to solve programs and study the\\n    performance of computer hardware and software. The problems that computer\\n    scientists encounter range from the abstract-- determining what problems\\n    can be solved with computers and the complexity of the algorithms that\\n    solve them \\u2013 to the tangible \\u2013 designing applications that perform well\\n    on handheld devices, that are easy to use, and that uphold security measures.\\n    [PER] will comment\\n"'}
```
