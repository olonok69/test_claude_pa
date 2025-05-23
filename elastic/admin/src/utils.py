import requests
import json
from fastapi.encoders import jsonable_encoder
import sys
import traceback


def get_ollama_models(
    ollama_url: str = "http://ollama:11434/api/tags",
    ollama_embeddings: str = "qwen:0.5b-text",
    ollama_url_get_model: str = "http://ollama:11434/api/pull",
):
    """
    Verify if the model to create embbedding it is available in OLLAMA, it is not download it

    """
    # Get list of models
    get_models = requests.get(ollama_url)
    # if Ollama it is available
    if get_models.status_code == 200:
        # get list of models
        models_list = get_models.json()["models"]
        # if list empty or model ollama empty
        if (len(models_list) == 0 and not ollama_embeddings) or (
            len(models_list) == 0 and len(ollama_embeddings) == 0
        ):
            raise AttributeError("No models available in OLLama for embeddings")
        else:
            # get list of present models in OLLAMA
            models_names_list = [x["name"] for x in models_list]
            # if OLLAMA embedding model not in the list , pull the model
            if ollama_embeddings not in models_names_list:
                print(f"Pulling Model {ollama_embeddings}")
                model_dict = {"name": ollama_embeddings, "stream": False}
                model_dict = json.dumps(model_dict).encode()
                r = requests.post(ollama_url_get_model, data=model_dict)
                response = r.json()
                if response["status"] != "success":
                    raise AttributeError(f"Error pulling model {ollama_embeddings}")
    else:
        raise AttributeError("OLLama it is not available")

    return "success"


def list_ollama_models(
    ollama_url: str = "http://ollama:11434/api/tags",
):
    """
    List models available in OLLAMA

    """
    # Get list of models
    get_models = requests.get(ollama_url)
    # if Ollama it is available

    return get_models.json()


def show_ollama_model(
    model: str,
    ollama_url: str = "http://ollama:11434/api/show",
):
    """
    List models available in OLLAMA

    """
    # show model
    print(f"Pulling Model {model}")
    model_dict = {"name": model}
    model_dict = json.dumps(model_dict).encode()
    r = requests.post(ollama_url, data=model_dict)
    response = r.json()

    if len(response.keys()) == 0:
        raise AttributeError(f"Error showing model {model}")

    return response


def delete_ollama_model(
    model: str,
    ollama_url: str = "http://ollama:11434/api/delete",
):
    """
    delete model OLLAMA

    """
    # show model
    print(f"Deleting Model {model}")
    model_dict = {"name": model}
    model_dict = json.dumps(model_dict).encode()
    r = requests.delete(ollama_url, data=model_dict)

    return r.status_code


def print_stack(out):
    # cath exception with sys and return the error stack
    out.status = {"code": 500, "message": "Error"}
    ex_type, ex_value, ex_traceback = sys.exc_info()
    # Extract unformatter stack traces as tuples
    trace_back = traceback.extract_tb(ex_traceback)

    # Format stacktrace
    stack_trace = list()

    for trace in trace_back:
        stack_trace.append(
            "File : %s , Line : %d, Func.Name : %s, Message : %s"
            % (trace[0], trace[1], trace[2], trace[3])
        )

    error = ex_type.__name__ + "\n" + str(ex_value) + "\n"
    for err in stack_trace:
        error = error + str(err) + "\n"
    out.error = error
    json_compatible_item_data = jsonable_encoder(out)
    return json_compatible_item_data
