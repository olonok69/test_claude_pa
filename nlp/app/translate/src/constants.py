import os
from dotenv import load_dotenv

# load credentials
env_path = os.path.join("keys", ".env")
load_dotenv(env_path)

MINIMUN_CHAR_LENGTH = 15
MINIMUN_WORDS_LENGTH = 4

# Access to ElasticCloud
host = os.getenv("host")
index = "large_control_dataset-doc"  # "sony_demo_1-doc" # enron_data_set_demo_1-doc
action = "_search"
# Number document to post
l_array = 100

port = 8080
timeout = "1d"
pit_url = (
    f"http://localhost:{port}/api/Search/PointInTime?scanId={index}&timeout={timeout}"
)
url_getdocuments = f"http://localhost:{port}/api/Ingest/{index}/GetDocuments"


user = os.getenv("user")
password = os.getenv("password")

filenames_types = ["doc", "docx"]
lfilenames_types = ["doc", "docx", "pdf"]

# move this to class
blacklist = [
    "[document]",
    "style",
    "noscript",
    "header",
    "html",
    "meta",
    "head",
    "input",
    "script",
    "style",
]
