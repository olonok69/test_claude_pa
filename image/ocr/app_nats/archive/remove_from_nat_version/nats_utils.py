import asyncio
import nats
from nats.errors import ConnectionClosedError, TimeoutError, NoServersError
import os
import glob


async def publish_file_with_metadata(nats_url, stream_name, subject, file_path):
    """
    Publishes a file to NATS JetStream with the filename as metadata.

    Args:
        nats_url (str): The NATS server URL (e.g., "nats://localhost:4222").
        stream_name (str): The JetStream stream name.
        subject (str): The subject to publish to.
        file_path (str): The path to the file to publish.
    """
    try:
        nc = await nats.connect(nats_url)
        js = nc.jetstream()

        filename = os.path.basename(file_path)

        with open(file_path, "rb") as file:
            file_content = file.read()

        await js.publish(
            subject,
            file_content,
            stream=stream_name,
            headers={"file-name": filename},  # Add filename as a header
        )

        print(f"Published file '{filename}' to {subject} in stream {stream_name}")

    except Exception as e:
        print(f"Error publishing file: {e}")
    finally:
        await nc.close()


async def setup_stream(nats_url, stream_name, subjects):
    """
    Creates a stream if it doesn't already exist.

    Args:
        nats_url (str): The NATS server URL.
        stream_name (str): The name of the stream to create.
        subjects (list): A list of subjects to associate with the stream.
    """
    try:
        nc = await nats.connect(nats_url)
        js = nc.jetstream()

        try:
            await js.stream_info(stream_name)
            print(f"Stream '{stream_name}' already exists.")
        except:
            await js.add_stream(name=stream_name, subjects=subjects)
            print(f"Stream '{stream_name}' created with subjects: {subjects}")

    except Exception as e:
        print(f"Error setting up stream: {e}")
    finally:
        await nc.close()


async def subscribe_and_receive_file(nats_url, stream_name, subject, output_dir):
    """
    Subscribes to a JetStream subject and receives files, saving them to a directory.

    Args:
        nats_url (str): The NATS server URL.
        stream_name (str): The JetStream stream name.
        subject (str): The subject to subscribe to.
        output_dir (str): The directory to save received files.
    """
    try:
        nc = await nats.connect(nats_url)
        js = nc.jetstream()

        async def cb(msg):
            try:
                filename = msg.headers.get(
                    "file-name", ["unknown"]
                )  # Get filename from headers, default "unknown"
                file_path = os.path.join(output_dir, filename)

                with open(file_path, "wb") as file:
                    file.write(msg.data)

                print(f"Received and saved file '{filename}'")
                await msg.ack()

            except Exception as e:
                print(f"Error processing message: {e}")
                await msg.nak()  # Or await msg.term() depending on your retry policy.

        sub = await js.subscribe(subject, stream=stream_name, cb=cb)
        print(f"Subscribed to {subject} in stream {stream_name}")
        await asyncio.Future()  # Keep the subscriber running

    except Exception as e:
        print(f"Error subscribing: {e}")
    finally:
        await nc.close()


async def publish_files_from_folder(nats_url, stream_name, subject, input_folder):
    """
    Publishes all files from a folder to NATS JetStream with filenames as metadata.

    Args:
        nats_url (str): The NATS server URL.
        stream_name (str): The JetStream stream name.
        subject (str): The subject to publish to.
        input_folder (str): The path to the folder containing files to publish.
    """
    try:
        nc = await nats.connect(nats_url)
        js = nc.jetstream()

        for file_path in glob.glob(
            os.path.join(input_folder, "*")
        ):  # Get all files in the folder
            if os.path.isfile(file_path):  # Ensure we are only processing files.
                filename = os.path.basename(file_path)

                with open(file_path, "rb") as file:
                    file_content = file.read()

                await js.publish(
                    subject,
                    file_content,
                    stream=stream_name,
                    headers={"file-name": filename},
                )
                print(
                    f"Published file '{filename}' to {subject} in stream {stream_name}"
                )

    except Exception as e:
        print(f"Error publishing files: {e}")
    finally:
        await nc.close()


async def subscribe_and_receive_files_to_folder(
    nats_url, stream_name, subject, output_folder
):
    """
    Subscribes to a JetStream subject and receives files, saving them to a folder.

    Args:
        nats_url (str): The NATS server URL.
        stream_name (str): The JetStream stream name.
        subject (str): The subject to subscribe to.
        output_folder (str): The directory to save received files.
    """
    try:
        nc = await nats.connect(nats_url)
        js = nc.jetstream()

        async def cb(msg):
            try:
                filename = msg.headers.get("file-name", ["unknown"])
                file_path = os.path.join(output_folder, filename)

                with open(file_path, "wb") as file:
                    file.write(msg.data)

                print(f"Received and saved file '{filename}'")
                await msg.ack()

            except Exception as e:
                print(f"Error processing message: {e}")
                await msg.nak()

        sub = await js.subscribe(subject, stream=stream_name, cb=cb)
        print(f"Subscribed to {subject} in stream {stream_name}")
        await asyncio.Future()  # Keep the subscriber running

    except Exception as e:
        print(f"Error subscribing: {e}")
    finally:
        await nc.close()


async def build_response_message(
    message_data, success, ocr_result=None, error_info=None
):
    """
    Builds a standardized response message for OCR processing results.

    Args:
        message_data (dict): The original message data received
        success (bool): Whether the OCR processing was successful
        ocr_result (str, optional): The OCR result text if successful
        error_info (dict, optional): Dictionary with error details if failed
            - code (str): Error code
            - message (str): Error message

    Returns:
        dict: Standardized response message
    """
    response = {
        "version": "1.0",
        "batchId": message_data.get("batchId"),
        "source": message_data.get("source", {}),
        "outcome": {"success": success},
        "state": {
            "fileId": message_data.get("state", {}).get("fileId"),
            "scanId": message_data.get("state", {}).get("scanId", ""),
        },
    }

    if success and ocr_result:
        languages = message_data.get("ocrOptions", {}).get("languages", ["en"])
        response["outcome"]["texts"] = [
            {"language": languages[0] if languages else "en", "text": ocr_result}
        ]
    elif not success and error_info:
        response["outcome"]["error"] = {
            "code": error_info.get("code", "UNKNOWN_ERROR"),
            "message": error_info.get("message", "An unknown error occurred"),
        }

    return response
