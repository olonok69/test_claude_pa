# Image Captioning / Image Summarization 

file https://dev.azure.com/sceven/DataDetect/_git/Detect-AI?path=/image/image_captioning/endpoint_image_captioning.py&version=GB5196-PoC-computer-Vision-Models&_a=contents

## Endpoint to integrate with Detect

Endpoint runing in port 5010 under url http://localhost:5010/process. Expect only POST request. This endpoint take an Image on base64 format and produce a summary of what you see on the image.

#### Parameters Request:

- max_new_tokens: The maximum numbers of tokens to generate, ignoring the number of tokens in the prompt.  Default 30
- min_new_tokens: The minimum numbers of tokens to generate, ignoring the number of tokens in the prompt. Default 10
- temperature: The value used to modulate the next token probabilities. Default .9
- repetition_penalty:The parameter for repetition penalty. 1.0 means no penalty. See this paper for more details. Default .1 
- diversity_penalty: This value is subtracted from a beam’s score if it generates a token same as any beam from other group at a particular time. Note that diversity_penalty is only effective if group beam search is enabled Default .8
- no_repeat_ngram_size: If set to int > 0, all ngrams of that size can only occur once. Default 3
- num_beams:  Number of beams for beam search. 1 means no beam search. Default 1
- prompt: Only works with Florence2. It must be MORE_DETAILED_CAPTION

If num_beams = 1 repetition_penalty  and diversity_penalty have no effect

## Run docker

This docker has GPU support and you will need to activate it at runing time

docker run --rm -it --gpus all -p 5010:5010/tcp image_captioning:latest


Example of request to endpoint:

Image : [here](../tests/dummy_data/test_nsfw/images.json) 



### RESPONSE

The endpoint return a list of image objects

Parameters:

    "max_new_tokens": 30,
    "min_new_tokens ": 20,
    "temperature": 1.0,
    "diversity_penalty": 0.1,
    "repetition_penalty": 0.8,
    "no_repeat_ngram_size": 3,
    "num_beams": 1
    "prompt" : "MORE_DETAILED_CAPTION"

#### Example Image captioning

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
                    " Image Summary for hen2.jpg is : a cartoon picture of a woman with horns and a body covered in paint and a blue dress with a white"
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
---

### Model Captioning Model API

```json
{
  "openapi": "3.1.0",
  "info": {
    "title": "Model Captioning Model API",
    "version": "0.1.0"
  },
  "paths": {
    "/test": {
      "get": {
        "summary": "Health Check",
        "operationId": "health_check_test_get",
        "responses": {
          "200": {
            "description": "Successful Response",
            "content": {
              "application/json": {
                "schema": {

                }
              }
            }
          }
        }
      }
    },
    "/health-check": {
      "get": {
        "summary": "Health Check",
        "operationId": "health_check_health_check_get",
        "responses": {
          "200": {
            "description": "Successful Response",
            "content": {
              "application/json": {
                "schema": {

                }
              }
            }
          }
        }
      }
    },
    "/work/status": {
      "get": {
        "summary": "Status Handler",
        "operationId": "status_handler_work_status_get",
        "responses": {
          "200": {
            "description": "Successful Response",
            "content": {
              "application/json": {
                "schema": {

                }
              }
            }
          }
        }
      }
    },
    "/process": {
      "post": {
        "summary": "Predict Image",
        "operationId": "predict_image_process_post",
        "responses": {
          "200": {
            "description": "Successful Response",
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/Index_Response"
                }
              }
            }
          }
        }
      }
    }
  },
  "components": {
    "schemas": {
      "Index_Response": {
        "properties": {
          "status": {
            "type": "object",
            "title": "Status",
            "default": {

            }
          },
          "data": {
            "anyOf": [
              {
                "type": "object"
              },
              {
                "items": {

                },
                "type": "array"
              },
              {
                "type": "null"
              }
            ],
            "title": "Data"
          },
          "error": {
            "type": "string",
            "title": "Error",
            "default": ""
          },
          "number_documents_treated": {
            "type": "integer",
            "title": "Number Documents Treated",
            "default": 0
          },
          "number_documents_non_treated": {
            "type": "integer",
            "title": "Number Documents Non Treated",
            "default": 0
          },
          "list_id_not_treated": {
            "items": {

            },
            "type": "array",
            "title": "List Id Not Treated",
            "default": []
          },
          "memory_used": {
            "type": "string",
            "title": "Memory Used",
            "default": ""
          },
          "ram_used": {
            "type": "string",
            "title": "Ram Used",
            "default": ""
          }
        },
        "type": "object",
        "title": "Index_Response",
        "description": "this class contains the response from the OCR process"
      }
    }
  }
}
```