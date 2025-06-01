from moviepy import VideoFileClip
import os
from google.cloud import storage


def convert_video_to_audio_moviepy(video_file, output_ext="mp3"):
    """Converts video to audio using MoviePy library
    that uses `ffmpeg` under the hood
    Args:
        video_file (str): Path to the video file
        output_ext (str): Desired audio format (default: mp3)
        Returns:
        str: Path to the converted audio file
    """
    filename, ext = os.path.splitext(video_file)
    print(filename)
    clip = VideoFileClip(os.path.join("data", video_file))
    clip.audio.write_audiofile(os.path.join("data", f"{filename}.{output_ext}"))
    clip.close()
    return f"{filename}.{output_ext}"


def upload_blob(bucket_name, source_file_name, destination_blob_name, credentials_path):
    """Uploads a file to a Cloud Storage bucket using a credentials file.
    Args:
        bucket_name (str): Name of the bucket to upload to
        source_file_name (str): Path to the file to upload
        destination_blob_name (str): Destination path in the bucket
        credentials_path (str): Path to the service account key file
    """
    # Initialize a storage client with the service account credentials
    # using the credentials file

    storage_client = storage.Client.from_service_account_json(credentials_path)
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)
    # Upload the file to the bucket
    # The timeout is set to 300 seconds (5 minutes)
    blob.upload_from_filename(source_file_name, timeout=300)

    print(f"File {source_file_name} uploaded to {destination_blob_name}.")
