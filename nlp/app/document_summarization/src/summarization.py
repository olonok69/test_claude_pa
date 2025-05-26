from typing import List
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, pipeline
import torch
from langchain_community.llms import HuggingFacePipeline
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings, OllamaEmbeddings
import numpy as np
from sklearn.cluster import KMeans
import requests
import json
import logging


def get_tokenizer(path: str):
    """
    load Tokenizer SeqtoSeq from path
    params:
    path: str Local path to tokenizer
    """
    tokenizer = AutoTokenizer.from_pretrained(path)
    return tokenizer


def get_fine_tuned_model(path: str, bfloat: bool = True):
    """
    load Fine Tuned SeqtoSeq model from path
    """
    fine_tune_model = None
    if bfloat:
        fine_tune_model = AutoModelForSeq2SeqLM.from_pretrained(
            path, torch_dtype=torch.bfloat16, device_map="auto"
        )
    else:
        fine_tune_model = AutoModelForSeq2SeqLM.from_pretrained(path, device_map="auto")

    return fine_tune_model


def get_summarizer(tokenizer, model, device: str = "cuda", task: str = "summarization"):
    """
    Create pipeline type task from model and tokenizer and send it to device
    """
    summarizer = pipeline(task=task, model=model, tokenizer=tokenizer)
    return summarizer


def get_llm(transformer: pipeline):
    """
    Get LLM from HuggingFace Transformer
    """
    return HuggingFacePipeline(pipeline=transformer)


def split_text(
    text: str,
    chunk_size: int = 5000,
    chunk_overlap: int = 300,
):
    """
    Split text into chunks of chunk_size
    """
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size, chunk_overlap=chunk_overlap
    )
    docs = text_splitter.create_documents([text])
    num_documents = len(docs)
    return docs, num_documents


def get_embeddings(docs, tokenizer, model, device: str = "gpu"):
    """
    Get embeddings from docs
    """
    embeddings = []
    for doc in docs:
        inputs = tokenizer(doc.page_content, return_tensors="pt", truncation=True)
        outputs = model(**inputs.to(device))
        embeddings.append(outputs.last_hidden_state.cpu().detach().numpy())
    embeddings = np.concatenate(embeddings, axis=0)
    return embeddings


def get_vectors(docs, model):
    """
    Get vectors from docs
    """

    vectors = model.embed_documents([x.page_content for x in docs])
    return vectors


def get_embedding_model(
    model_name: str,
    device: str = "cpu",
    use_ollana: bool = True,
    ollama_model: str = "qwen:0.5b-text",
    base_url: str = "http://ollama:11434",
):
    """ """
    if use_ollana:
        embeddings = OllamaEmbeddings(
            model=ollama_model,
            show_progress=True,
            base_url=base_url,
        )
    else:
        model_kwargs = {"device": device}
        encode_kwargs = {"normalize_embeddings": False}
        embeddings = HuggingFaceEmbeddings(
            model_name=model_name,
            model_kwargs=model_kwargs,
            encode_kwargs=encode_kwargs,
        )
    return embeddings


def get_kmeans_model(vectors, docs, n_clusters: int = 8):
    """
    Get the most representative document of each cluster of documents
    """
    kmeans = KMeans(n_clusters=n_clusters, random_state=42).fit(vectors)

    # Find the closest embeddings to the centroids

    # Create an empty list that will hold your closest points
    closest_indices = []

    # Loop through the number of clusters you have
    for i in range(n_clusters):

        # Get the list of distances from that particular cluster center
        distances = np.linalg.norm(vectors - kmeans.cluster_centers_[i], axis=1)

        # Find the list position of the closest one (using argmin to find the smallest distance)
        closest_index = np.argmin(distances)

        # Append that position to your closest indices list
        closest_indices.append(closest_index)

    selected_indices = sorted(closest_indices)

    selected_docs = [docs[doc] for doc in selected_indices]

    return selected_docs, selected_indices


def get_summary(selected_docs, summarizer, selected_indices):

    summary_list = []

    # Loop through a range of the lenght of your selected docs

    for i, doc in enumerate(selected_docs):

        # Go get a summary of the chunk
        # chunk_summary = map_chain.run([doc])
        response = summarizer(doc.page_content)
        chunk_summary = response[0]["summary_text"]
        # Append that summary to your list
        summary_list.append(chunk_summary)

        logging.info(
            f"Summary #{i} (chunk #{selected_indices[i]}) - Preview: {chunk_summary[:500]} \n"
        )

    return summary_list


def get_final_summary(
    summaries,
    endpoint,
    chunck: int = 4800,
    min_num_tokens: int = 64,
    max_num_tokens: int = 1024,
):
    """
    get final Summary
    """
    # if document if larger than 4800 chars split in chunks and summarize
    if len(summaries) > chunck:
        docs, _ = split_text(summaries)
        final_summary = ""
        for doc in docs:
            response = endpoint.summarizer(doc.page_content, temperature=0.01)
            final_summary = final_summary + " " + response[0]["summary_text"]

        chunck = final_summary
    else:  # it is not larger than 4800
        length_tokens = endpoint.llm.get_num_tokens(summaries)
        # more than 64 tokens and lest than 1024 the summarize
        if length_tokens > min_num_tokens and length_tokens < max_num_tokens:

            response = endpoint.summarizer(
                summaries, max_length=length_tokens - 10, temperature=0.01
            )

            chunck = response[0]["summary_text"]
        else:
            chunck = summaries

    return chunck


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
                logging.info(f"Pulling Model {ollama_embeddings}")
                model_dict = {"model": ollama_embeddings, "stream": False}
                model_dict = json.dumps(model_dict).encode()
                r = requests.post(ollama_url_get_model, data=model_dict)
                response = r.json()
                if response["status"] != "success":
                    raise AttributeError(f"Error pulling model {ollama_embeddings}")
    else:
        raise AttributeError("OLLama it is not available")

    return "success"
