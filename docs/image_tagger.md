# Image Classification / Tagging 

file https://dev.azure.com/sceven/DataDetect/_git/Detect-AI?path=/image/image_tagger/endpoint_image_tagger.py&version=GB5196-PoC-computer-Vision-Models&_a=contents

## Endpoint to integrate with Detect

Endpoint runing in port 5011 under url http://localhost:5011/process. Expect only POST request. This endpoint take an Image or video on base64 format and produce list of dictionaries , with length according to attribute num_classes in the request. Each dictionary contains the label and its probability

#### Parameters Request:

- num_labels: Number of top more probable classes which describe the image. Default 5

#### Run docker

This docker has GPU support and you will need to activate it at runing time

docker run --rm -it --gpus all -p 5011:5011/tcp image_tagger:latest


Example of request to endpoint:

Image : [here](../tests/dummy_data/test_nsfw/images.json) 



### RESPONSE

The endpoint return a list of image objects

#### Example Image and 8 classes

```python
{
    "status": {
        "code": 200,
        "message": "Success"
    },
    "data": [
        {
            "id": "7587bcb2-4ea6-4a64-a426-040b40bf414b",
            "index": "large_control_dataset-doc",
            "source": {
                "content": [
                    {
                        "label": "lakeside",
                        "probability": 0.18950766324996948
                    },
                    {
                        "label": "castle",
                        "probability": 0.08638923615217209
                    },
                    {
                        "label": "valley",
                        "probability": 0.06290815770626068
                    },
                    {
                        "label": "lawn mower",
                        "probability": 0.052732914686203
                    },
                    {
                        "label": "boathouse",
                        "probability": 0.03214750438928604
                    },
                    {
                        "label": "palace",
                        "probability": 0.024455752223730087
                    },
                    {
                        "label": "rapeseed",
                        "probability": 0.022522615268826485
                    },
                    {
                        "label": "worm fence",
                        "probability": 0.019660627469420433
                    }
                ],
                "fs": {
                    "uri": "file:///home/demofilesystem/test_data/Large%20Control%20DataSet/Office%20Files%20and%20Documents/images/images.jpeg"
                },
                "file_name": "images.jpeg",
                "file_type": "jpeg",
                "embedded_depth": 0
            }
        }
    ],
    "error": "",
    "number_documents_treated": 1,
    "number_documents_non_treated": 0,
    "list_id_not_treated": []
}
```
