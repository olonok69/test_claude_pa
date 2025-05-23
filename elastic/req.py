import requests
import json


def make_question_request(
    host: str,
    index: str,
    question: str,
    model: str = "qwen2.5:latest",
    api_url: str = "http://localhost:8000",
) -> dict:
    """
    Send a question request to the FastAPI endpoint

    Args:
        host (str): Elasticsearch host
        index (str): Index name to search
        question (str): Question to process
        model (str): Model to use for processing the question
        api_url (str): Base URL of the API

    Returns:
        dict: Response from the API
    """
    headers = {"Content-Type": "application/json"}

    payload = {"host": host, "index": index, "question": question, "model": model}

    response = requests.post(f"{api_url}/process", json=payload)
    response.raise_for_status()

    return response.json()


# Example usage
if __name__ == "__main__":
    try:
        result = make_question_request(
            host="http://ollama1:11434",
            index="curated_data_set_jg_test-doc",
            question="Give me documents with file type jpg and size higher",
            model="qwen2.5:latest",
            api_url="https://ai.demo.datadetect.com/elastic_llm",
        )
        print(f"Answer: {result['answer']}")
    except requests.exceptions.RequestException as e:
        print(f"Error making request: {e}")
