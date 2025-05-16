# ROT Analysys Endpoint

file https://dev.azure.com/sceven/DataDetect/_git/Detect-AI?version=GB5046-Create-Rot-Endpoint&path=/rot/app/endpoint_rot.py


## Endpoint to integrate with Detect
Testing Notebook [here](Notebooks/ROT model Analisys-test-endpoint.ipynb)

Endpoint runing in port 5007 under directory process-tika-output. Expect only POST request. This endpoint take directly the output from tika and return a list of objects to update the index
The endpoint receives a dictionary with 2 keys
- filters : dictionary of dictionaries containing the filters defined by the user in the UI
- docs: output from TIKA


## Filters 

### Redundant

{"col": "days_created", "type": "newest"} 

col options --> days_accesed | days_modified | days_created

type options --> newest | oldest

### Trivial

{"template_list": ["jpg", "gif"], "custom_list": ["doc"],}

template_list --> list of file extension from combox

custom_list --> list of file extension from Custom Defined box

### Obsolete

{"col": "days_created", "older_than": 60, "timeframe": "days"}

col options --> days_accesed | days_modified | days_created

older_than --> number of units

timeframe --> days | months | years

Example filters dictionary
```python
{'redundant': {'col': 'days_created', 'type': 'newest'},
 'trivial': {'template_list': ['jpg', 'gif'], 'custom_list': ['doc']},
 'obsolete': {'col': 'days_created', 'older_than': 300, 'timeframe': 'days'}}

```

```python
example Json to be send to endpoint

data1 = {}
data1['docs'] = tika_docs # here we have the output of tika
data1['filters'] = filters # here we have the filters

data2 = json.dumps(data1).encode()
url = "http://localhost:5007/process-tika-output" 

try:
    r = requests.post(url, data=data2)
    print(r.json())
finally:

    pass


```
OUTPUT example
```python
{'status': {'code': 200, 'message': 'Success'},
 'data': {'number_docs': 7452,
  'business_documents_counts': {'0': 6959, '1': 493},
  'image_documents_counts': {'0': 5448, '1': 2004},
  'rot_dictionary': [{'index': 'd66e28bb91b472ab862faa988e37f3a3dafc1ae417541183dad53c5800448d4f',
    'is_image': 0,
    'is_business': 0,
    'days_accesed': 53,
    'days_modified': 298,
    'days_created': 853,
    'seconds_accesed': 4658582.984768,
    'seconds_modified': 25818606.057642,
    'seconds_created': 73778583.131028,
    'outdated_group': 'Less 3 year',
    'trivial': 0,
    'obsolete': 1,
    'redundant': 0,
    'is_rot': 1}]},
 'error': ''}

example of an individual documents

{'index': 'd66e28bb91b472ab862faa988e37f3a3dafc1ae417541183dad53c5800448d4f',
    'is_image': 0,
    'is_business': 0,
    'days_accesed': 53,
    'days_modified': 298,
    'days_created': 853,
    'seconds_accesed': 4658582.984768,
    'seconds_modified': 25818606.057642,
    'seconds_created': 73778583.131028,
    'outdated_group': 'Less 3 year',
    'trivial': 0,
    'obsolete': 1,
    'redundant': 0,
    'is_rot': 1}

```