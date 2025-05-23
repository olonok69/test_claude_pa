from elasticsearch import Elasticsearch
from langchain_ollama import ChatOllama
from langchain_core.prompts import PromptTemplate
import requests
import json
from .prompts import *
import logging


def search_documents(index_name, query, elastic_url="http://localhost:9200"):
    """
    Searches documents in an Elasticsearch index.

    Args:
        index_name (str): The name of the Elasticsearch index.
        query (dict): The Elasticsearch query dictionary.
        elastic_url (str, optional): The Elasticsearch server URL. Defaults to "http://localhost:9200".

    Returns:
        list: A list of matching documents (dictionaries), or None if an error occurs.
    """
    try:
        es = Elasticsearch(elastic_url)

        response = es.search(index=index_name, query=query)

        hits = response["hits"]["hits"]
        documents = [hit["_source"] for hit in hits]

        return documents

    except Exception as e:
        print(f"An error occurred during Elasticsearch search: {e}")
        return None


def get_schema_elastic(es_host: str, index_name: str):
    """
    Get Schema of Elastic Index in es_host with name index_name
    """

    schema = ""
    # Make the request to get the mapping
    response = requests.get(f"{es_host}/{index_name}/_mapping")

    # Check if the request was successful
    if response.status_code == 200:
        mapping = response.json()
        schema = json.dumps(mapping, indent=4)
    return schema


def get_elastic(config):
    """
    Get ELastic Client
    """

    es_client = None
    try:
        es_endpoint = config.get("ELASTIC_HOST")
        es_client = Elasticsearch(
            es_endpoint,
            # api_key=os.environ.get("ELASTIC_API_KEY")
        )
    except Exception as e:
        print("No Client")

    return es_client


def get_llama_chain(llm_id: str, url: str):
    """
    build chain with LLama Model llama3.1:latest
    """
    llm = ChatOllama(
        model=llm_id,
        format="json",
        temperature=0.5,
        top_p=0.9,
        tok_k=30,
        num_ctx=8192,
        base_url=url,
    )

    prompt2 = PromptTemplate(
        template="""<|begin_of_text|><|start_header_id|>system<|end_header_id|> {prompt}
        <|eot_id|><|start_header_id|>user<|end_header_id|>

        Here is the user question: {question} \n <|eot_id|><|start_header_id|>assistant<|end_header_id|>
        """,
        input_variables=["question", "prompt"],
    )

    elastic_llm = prompt2 | llm
    return elastic_llm


def get_qwen_chain(llm_id: str, url: str):
    """
    build chain with Qwen Model qwen2.5:latest
    """
    llm2 = ChatOllama(
        model=llm_id,
        format="json",
        temperature=0.5,
        top_p=0.9,
        tok_k=30,
        num_ctx=8192,
        base_url=url,
    )

    prompt2 = PromptTemplate(
        template="""{prompt}    

        Here is the user question: {question} \n
        """,
        input_variables=["question", "prompt"],
    )

    elastic_llm2 = prompt2 | llm2
    return elastic_llm2


def process_question(host, index, question, model: str = "llama3.1:latest"):
    """
    Process the question
    Args:
        host (str): The Elasticsearch host.
        index (str): The Elasticsearch index.
        question (str): The question to ask.
        model (str): The model to use for processing the question
    Returns:
        dict: A JSON response with the answer or an error message.
    """

    if model == "llama3.1:latest":

        elastic_llm = get_llama_chain(llm_id=model, url=host)
    elif model == "qwen2.5:latest":
        elastic_llm = get_qwen_chain(llm_id=model, url=host)

    response = elastic_llm.invoke({"question": question, "prompt": prompt})

    es_query = json.loads(response.content)

    llamaresp = search_documents(
        index, query=es_query["query"], elastic_url="http://135.234.233.194:9200"
    )

    return llamaresp
