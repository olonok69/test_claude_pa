import os
from langchain_community.llms import HuggingFacePipeline

# Loaders
from langchain.schema import Document
import transformers
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter

# Summarizer we'll use for Map Reduce
from langchain.chains.summarize import load_summarize_chain
import torch

# Data Science
import numpy as np
from sklearn.cluster import KMeans
import requests

from dotenv import load_dotenv
import platform
import warnings
import datetime

warnings.filterwarnings("ignore")

# load credentials
env_path = os.path.join("keys", ".env")
load_dotenv(env_path)
# env variables
MODEL_PATH = os.getenv("MODEL_PATH")
LOCAL_ENV = os.getenv("LOCAL_ENV")
MODEL_NAME = os.getenv("SENTENCE_TRANSFORMER")
EMBEDDINGS = os.getenv("EMBEDDINGS")
BFLOAT16 = int(os.getenv("BFLOAT16"))

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))


time1 = datetime.datetime.now()
if platform.system() == "Windows":
    MODELS_PATH = os.path.join(ROOT_DIR, "models")
    MODEL_NAME = os.path.join(MODELS_PATH, MODEL_NAME.split("/")[-1])

# load transformers models
device = "cuda" if torch.cuda.is_available() else "cpu"

langchain_use = False
response = requests.get("https://www.gutenberg.org/cache/epub/64317/pg64317.txt")


book_complete_text = response.text

book_complete_text = book_complete_text[5:]

print(len(book_complete_text))


file_path = "output/book.txt"
with open(file_path, "w", encoding="utf-8") as f:
    f.write(book_complete_text)

with open(file_path, "r", encoding="utf-8") as f:
    text = f.read()


text = text.replace("\t", " ")

print(len(text))
text_splitter = RecursiveCharacterTextSplitter(
    separators=["\n\n", "\n", "\t"], chunk_size=5000, chunk_overlap=300
)

docs = text_splitter.create_documents([text])
num_documents = len(docs)

print(f"Now our book is split up into {num_documents} documents")


model_kwargs = {"device": f"{device}"}
encode_kwargs = {"normalize_embeddings": False}
embeddings = HuggingFaceEmbeddings(
    model_name=MODEL_NAME, model_kwargs=model_kwargs, encode_kwargs=encode_kwargs
)


vectors = embeddings.embed_documents([x.page_content for x in docs])
print(len(vectors[0]))

num_clusters = int(len(vectors) // 8)
print(num_clusters)


# Assuming 'embeddings' is a list or array of 768-dimensional embeddings

# Choose the number of clusters, this can be adjusted based on the book's content.
# I played around and found ~10 was the best.
# Usually if you have 10 passages from a book you can tell what it's about
num_clusters = 5 if num_clusters <= 5 else num_clusters

# Perform K-means clustering
kmeans = KMeans(n_clusters=num_clusters, random_state=42).fit(vectors)


# Find the closest embeddings to the centroids

# Create an empty list that will hold your closest points
closest_indices = []

# Loop through the number of clusters you have
for i in range(num_clusters):

    # Get the list of distances from that particular cluster center
    distances = np.linalg.norm(vectors - kmeans.cluster_centers_[i], axis=1)

    # Find the list position of the closest one (using argmin to find the smallest distance)
    closest_index = np.argmin(distances)

    # Append that position to your closest indices list
    closest_indices.append(closest_index)


selected_indices = sorted(closest_indices)
print(selected_indices)

# select the most representative documents for each cluster

selected_docs = [docs[doc] for doc in selected_indices]

text_summarization_pipeline = transformers.pipeline(
    "summarization", model="google/flan-t5-base"
)
llm = HuggingFacePipeline(pipeline=text_summarization_pipeline)
if langchain_use:

    num_docs = len(selected_docs)

    num_tokens_first_doc = llm.get_num_tokens(selected_docs[0].page_content)

    print(
        f"Now we have {num_docs} documents and the first one has {num_tokens_first_doc} tokens"
    )

    summary_chain = load_summarize_chain(llm=llm, chain_type="map_reduce", verbose=True)

    output = summary_chain.run(docs)

    print(output.strip())
else:

    # Make an empty list to hold your summaries
    summary_list = []

    # Loop through a range of the lenght of your selected docs
    for i, doc in enumerate(selected_docs):

        # Go get a summary of the chunk
        # chunk_summary = map_chain.run([doc])
        response = text_summarization_pipeline(doc.page_content)
        chunk_summary = response[0]["summary_text"]
        # Append that summary to your list
        summary_list.append(chunk_summary)

        print(
            f"Summary #{i} (chunk #{selected_indices[i]}) - Preview: {chunk_summary[:500]} \n"
        )

    summaries = "\n".join(summary_list)

    # Convert it back to a document
    summaries = Document(page_content=summaries)

    print(f"Your total summary has {llm.get_num_tokens(summaries.page_content)} tokens")
    print(len(summaries.page_content))
    print(summaries.page_content)

time2 = datetime.datetime.now()


print(f"Time taken: {time2 - time1}")
