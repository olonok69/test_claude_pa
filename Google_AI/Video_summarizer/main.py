import os
import sys
from google.oauth2 import service_account
import vertexai
from dotenv import dotenv_values
import json
from model import init_model, generate_generative_model
from prompts import summary, full_transcription
from IPython import embed
from utils import convert_video_to_audio_moviepy, upload_blob


if __name__ == "__main__":

    ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
    vf = sys.argv[1]
    # Load the configuration and Initialize the Vertex AI client
    config = dotenv_values(os.path.join(ROOT_DIR, "keys", ".env"))
    credentials_path = os.path.join(
        ROOT_DIR, "keys", "complete-tube-421007-208a4862c992.json"
    )
    with open(credentials_path) as source:
        info = json.load(source)
    # Create a service account credentials object
    vertex_credentials = service_account.Credentials.from_service_account_info(info)
    vertexai.init(
        project=config["PROJECT"],
        location=config["REGION"],
        credentials=vertex_credentials,
    )

    if "GEMINI_API_KEY" not in os.environ:
        os.environ["GEMINI_API_KEY"] = config.get("GEMINI-API-KEY")
    if "GOOGLE_API_KEY" not in os.environ:
        os.environ["GOOGLE_API_KEY"] = config.get("GEMINI-API-KEY")
    # create the model
    model = init_model()
    # get the video file name
    source_file_name = convert_video_to_audio_moviepy(vf)  # extract audio from video
    # convert the video file to audio
    bucket_name = "audio_ml_examples_trancription"  # Replace with your bucket name
    destination_blob_name = f"input/{source_file_name}"  # Replace with the desired name in the bucket (can include folders)
    # upload the audio file to the bucket
    upload_blob(
        bucket_name,
        os.path.join(ROOT_DIR, "data", source_file_name),
        destination_blob_name,
        credentials_path,
    )
    # generate the text summary
    text_summary = generate_generative_model(
        model, source_file_name, bucket_name, summary
    )
    print(text_summary)
    embed()
    # generate the full transcription
    text_full = generate_generative_model(
        model, source_file_name, bucket_name, full_transcription
    )

    print(text_full)
