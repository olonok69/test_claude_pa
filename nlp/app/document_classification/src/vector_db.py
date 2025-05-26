import os
from typing import List
from langchain_community.vectorstores import Chroma
from langchain_community.document_loaders import CSVLoader
import logging


def create_vector_db(class_file, db_path, embeddings, metadata_columns):
    """

    Args:
        class_file (_type_): _description_
        chroma_path (_type_): _description_
        embeddings (_type_): _description_
        metadata_columns (_type_): _description_

    Returns:
        _type_: _description_
    """
    loader = CSVLoader(class_file, metadata_columns=metadata_columns)
    documents = loader.load()
    os.makedirs(db_path, exist_ok=True)
    # delete collection if this exists
    db = Chroma.from_documents(
        documents=documents,
        # Chose the embedding you want to use
        embedding=embeddings,
        collection_metadata={"hnsw:space": "cosine"},
    )

    return db


def get_or_create_vector_db(
    class_file: str,
    db_path: str,
    embeddings,
    metadata_columns: List = ["classifier"],
):
    """
    Create Vector Database or read it from persistance location
    """

    logging.info(f"DB VectorStore Path: {db_path}")
    db = create_vector_db(class_file, db_path, embeddings, metadata_columns)

    return db
