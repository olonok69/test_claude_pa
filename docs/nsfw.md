# Non Suitable for Work (NSFW Model) 

file https://dev.azure.com/sceven/DataDetect/_git/Detect-AI?path=/image/nsfw/app/endpoint_nsfw.py&version=GB5196-PoC-computer-Vision-Models&_a=contents

## Endpoint to integrate with Detect

Endpoint runing in port 5009 under url http://localhost:5009/process. Expect only POST request. This endpoint take an Image or video on base64 format and produce and score 0 (suitable for work) or 1 (non-suitable for work). In the case of images we also provide a second classification of the image among these 5 categories ["sexy", "porn", "hentai","neutral", "drawing"]

#### Parameters Request:

- threshold: Probability threshold. Above this number the content it is consider nsfw. Default .5

## Run docker

This docker has GPU support and you will need to activate it at runing time

docker run --rm -it --gpus all -p 5009:5009/tcp nsfw:latest


Example of request to endpoint:

Image : [here](../tests/dummy_data/test_nsfw/image_jpg.json) 

Video : [here](../tests/dummy_data/test_nsfw/video_mov.json) 

### RESPONSE

The endpoint return a list of nsfw objects

#### Example Image

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
                        "data": {
                            "drawings": 3.9,
                            "hentai": 96.0,
                            "neutral": 0.09,
                            "porn": 0.01,
                            "sexy": 0.0
                        },
                        "nsfw": 1
                    }
                ],
                "fs": {
                    "uri": "file:///home/demofilesystem/test_data/Large%20Control%20DataSet/Office%20Files%20and%20Documents/images/hen2.jpg"
                },
                "file_name": "hen2.jpg",
                "file_type": "jpg",
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
#### Example Video

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
                        "prediction": 0.020678410655948085,
                        "description": "video file_example_MOV_480_700kB.mov is Suitable for Work with a score of 0.020678410655948085",
                        "nsfw": 0
                    }
                ],
                "fs": {
                    "uri": "file:///home/demofilesystem/test_data/Large%20Control%20DataSet/Office%20Files%20and%20Documents/DOC/file_example_MOV_480_700kB.mov"
                },
                "file_name": "file_example_MOV_480_700kB.mov",
                "file_type": "mov",
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