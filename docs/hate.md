# Hate/Offensive speech detector

file https://dev.azure.com/sceven/DataDetect/_git/Detect-AI?path=/nlp/app/endpoint_hate.py

Testing Notebook [here](Notebooks/Hate-Speech-Analyzer-API.ipynb)

Endpoint runing in port 5004 under directory hate-analyzer. Expect only POST request.

Note: This endpoint it is still experimental

### EXAMPLE

```python
text = "hey guy, dont be lazy"
data1 = text.encode()

# Hate Analyzer 
url = "http://localhost:5004/hate-analyzer" 

try:
    r = requests.post(url, data=data1)
    print(r.json())
finally:

    pass

```

### RESPONSE

```python
{
  "source": "hey guy, dont be lazy",
  "hate_prediction": [
    [
      {
        "label": "normal",
        "score": 0.636485755443573
      },
      {
        "label": "offensive",
        "score": 0.3253282308578491
      },
      {
        "label": "hate speech",
        "score": 0.03818602114915848
      }
    ]
  ]
}
```
