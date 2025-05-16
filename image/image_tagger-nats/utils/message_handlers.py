import os
import json
import asyncio
import datetime
import logging
import signal
import sys
import gc
import copy
import requests
import base64
import psutil
import nats
from nats.js.api import ConsumerConfig, AckPolicy
# Import from our utility modules
from detectaicore import NatsSSLContextBuilder, ensure_stream_exists, setup_version_endpoint, setup_health_check_endpoint, Job
from detectaicore.src.schemas import handle_error_and_acknowledge, Index_Response

async def process_image_from_nats(
    nats_url,
    input_stream,
    input_subject,
    output_stream,
    output_subject,
    local_env,
    mode="tagging",
    models_path=None,
):
    """
    Receives document metadata from NATS, downloads the document, processes it,
    and publishes the result.

    Args:
        nats_url: NATS server URL
        input_stream: Input stream name
        input_subject: Input subject name
        output_stream: Output stream name
        output_subject: Output subject name
        local_env: Local environment flag
        mode: Processing mode ("tagging" or "captioning")
    """
    # Get environment variables
    MODELS_PATH = os.getenv("MODELS_PATH")
    USE_ONNX = os.getenv("USE_ONNX", "NO")
    USE_OPENVINO = os.getenv("USE_OPENVINO", "YES")

    # Import the model only when needed to avoid circular imports
    from src.predictor import get_prediction_model

    # Create an event to handle shutdown
    shutdown_event = asyncio.Event()

    def signal_handler(signum, frame):
        logging.info(f"Received signal {signum}. Starting graceful shutdown...")
        shutdown_event.set()

    # Register signal handlers
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    # Log startup information
    logging.info(f"Starting {mode} service with:")
    logging.info(f"  Input stream: {input_stream}")
    logging.info(f"  Input subject: {input_subject}")
    logging.info(f"  Output stream: {output_stream}")
    logging.info(f"  Output subject: {output_subject}")

    # Set the default prompt based on mode
    default_prompt = "<OD>" if mode == "tagging" else "<MORE_DETAILED_CAPTION>"
    logging.info(f"  Default prompt: {default_prompt}")

    # Save the initial mode for reference
    service_mode = mode

    # Get device
    import torch

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    try:
        # Connect to NATS using certificate if local_env is "0"
        if local_env == "0":
            ssl_builder = NatsSSLContextBuilder()
            ssl_context = ssl_builder.create_ssl_context()
            nc = await nats.connect(nats_url, tls=ssl_context)
        else:
            nc = await nats.connect(nats_url)

        js = nc.jetstream()

        # Ensure both input and output streams exist
        await ensure_stream_exists(js, input_stream, [input_subject])
        await ensure_stream_exists(js, output_stream, [output_subject])

        # Load models here to ensure they're available when processing requests
        try:
            # Here we're setting up for image captioning using OpenVINO with Florence-2
            model_path = os.path.join(models_path, "Florence-2-base-ft")
            logging.info(f"Model Path: {model_path}")

            global model, processor
            model, processor = get_prediction_model(
                model_path=model_path,
                use_onnx=USE_ONNX,
                use_openvino=USE_OPENVINO,
                device=device,
            )
            logging.info("Successfully loaded model and processor")

        except Exception as e:
            ex_type, ex_value, ex_traceback = sys.exc_info()
            logging.error(f"Exception {ex_type} value {str(ex_value)}")
            raise

        async def cb(msg):
            # Use a longer timeout for local environment
            ack_wait_seconds = (
                3600 if local_env == "1" else 600
            )  # 1 hour for local, 10 min for prod
            heartbeat_interval = ack_wait_seconds / 2
            stop_heartbeat = asyncio.Event()
            heartbeat_task = None

            try:
                # More robust heartbeat function
                async def send_heartbeat():
                    heartbeat_count = 0
                    while not stop_heartbeat.is_set():
                        try:
                            await asyncio.sleep(heartbeat_interval)
                            if stop_heartbeat.is_set():
                                break

                            heartbeat_count += 1
                            logging.info(
                                f"Sending working ack #{heartbeat_count} for msg."
                            )
                            await msg.in_progress()

                        except asyncio.CancelledError:
                            logging.info("Heartbeat task cancelled.")
                            break

                        except Exception as e:
                            logging.error(f"Error sending working ack: {e}")
                            # Just sleep a bit and try again rather than breaking
                            await asyncio.sleep(10)

                    logging.info("Heartbeat task exiting")

                # Always start the heartbeat task, with explicit logging
                logging.info(
                    f"Starting heartbeat task in environment LOCAL_ENV={local_env}"
                )
                heartbeat_task = asyncio.create_task(send_heartbeat())
                if heartbeat_task:
                    logging.info("Heartbeat task started successfully")
                else:
                    logging.error("Failed to start heartbeat task!")

                time1 = datetime.datetime.now()

                # Parse the message as JSON
                message_data = json.loads(msg.data.decode("utf-8"))
                logging.info(f"Received message: {message_data}")
                logging.info(f"Message headers: {msg.headers}")

                # Create a new job
                new_task = Job()
                new_task.status = "Job started"

                # Set job type based on service mode
                if service_mode == "tagging":
                    new_task.type_job = "Image Tagging Model Analysis"
                else:
                    new_task.type_job = "Image Captioning Model Analysis"

                # Extract URI from the message
                uri = message_data["source"]["uri"]
                logging.info(f"Processing image from URI: {uri}")
                IS_DOCKER = os.getenv("IS_DOCKER", "0")
                IMAGES_PATH = os.getenv("IMAGES_PATH", "/app/images")
                # Download or read the image file based on the URI scheme
                image_data = None
                if uri.startswith("http://") or uri.startswith("https://"):
                    # Handle HTTP URLs
                    response = requests.get(uri, verify=False)
                    if response.status_code == 200:
                        image_data = response.content
                    else:
                        logging.error(
                            f"Failed to download image from {uri}, status code: {response.status_code}"
                        )
                        # Http download error
                        error_message = f"Failed to download image: HTTP status {response.status_code}"
                        await handle_error_and_acknowledge(
                            js,
                            msg,
                            message_data,
                            error_message,
                            "download-error",
                            output_stream,
                            output_subject,
                            local_env,
                        )
                        return
                # Local file in development environment
                elif uri.startswith("file://") and local_env == "1":
                    if IS_DOCKER == "1":
                        # Handle file paths in Docker environment
                        original_path = uri[7:]  # Remove 'file://' prefix
                        filename = os.path.basename(original_path)
                        file_path = os.path.join(IMAGES_PATH, filename)
                        logging.info(
                            f"Docker file path: {file_path} (original: {original_path})"
                        )
                    else:
                        # Handle local file paths in development environment (non-Docker)
                        file_path = uri[7:]  # Remove 'file://' prefix
                        filename = os.path.basename(file_path)
                        logging.info(f"Local file path: {file_path}")

                    try:
                        with open(file_path, "rb") as file:
                            image_data = file.read()
                    except Exception as e:
                        logging.error(f"Failed to read local file {file_path}: {e}")
                        # Local file read error
                        error_message = (
                            f"Failed to read local file {file_path}: {str(e)}"
                        )
                        await handle_error_and_acknowledge(
                            js,
                            msg,
                            message_data,
                            error_message,
                            "file-read-error",
                            output_stream,
                            output_subject,
                            local_env,
                        )
                        return
                # Local file in production environment
                elif uri.startswith("file://") and local_env == "0":
                    # Handle local file paths in production environment
                    file_path = uri[7:]  # Remove 'file://' prefix
                    logging.info(f"Full local file path: {file_path}")
                    try:
                        with open(file_path, "rb") as file:
                            image_data = file.read()
                    except Exception as e:
                        logging.error(f"Failed to read local file {file_path}: {e}")
                        # File read error response
                        error_message = (
                            f"Failed to read local file {file_path}: {str(e)}"
                        )
                        await handle_error_and_acknowledge(
                            js,
                            msg,
                            message_data,
                            error_message,
                            "file-read-error",
                            output_stream,
                            output_subject,
                            local_env,
                        )
                        return
                else:
                    logging.error(f"Unsupported URI scheme: {uri}")
                    # URI scheme not supported
                    error_message = f"Unsupported URI scheme: {uri}"
                    await handle_error_and_acknowledge(
                        js,
                        msg,
                        message_data,
                        error_message,
                        "unsupported-uri",
                        output_stream,
                        output_subject,
                        local_env,
                    )
                    return

                logging.info(f"Downloaded image data of size: {len(image_data)} bytes")

                # Now define the message processing mode and prompt based on service mode
                # Initialize mode and prompt from the service configuration
                message_mode = service_mode  # Start with the service's default mode
                prompt = default_prompt  # Start with the default prompt for this mode
                num_labels = 5  # Default number of labels for tagging mode

                # Override if the message specifies a prompt
                if (
                    "prompt" in message_data
                    and isinstance(message_data["prompt"], str)
                    and len(message_data["prompt"]) > 0
                ):
                    prompt_value = message_data["prompt"].upper()
                    if prompt_value in ["OD", "OBJECT_DETECTION"]:
                        prompt = "<OD>"
                        message_mode = "tagging"
                    elif prompt_value in [
                        "MORE_DETAILED_CAPTION",
                        "DETAILED",
                        "CAPTION",
                    ]:
                        prompt = "<MORE_DETAILED_CAPTION>"
                        message_mode = "captioning"
                    else:
                        # If not recognized, wrap in < > as required by Florence-2
                        prompt = f"<{message_data['prompt']}>"
                        # Keep the message_mode inherited from service_mode

                logging.info(f"Using prompt: {prompt}, mode: {message_mode}")

                # Extract num_labels parameter (only for tagging mode)
                if message_mode == "tagging" and "num_labels" in message_data:
                    if (
                        isinstance(message_data["num_labels"], str)
                        and len(message_data["num_labels"]) > 0
                    ):
                        num_labels = int(message_data["num_labels"])
                    elif isinstance(message_data["num_labels"], int):
                        num_labels = message_data["num_labels"]

                # Log the processing parameters
                if message_mode == "tagging":
                    logging.info(f"Tagging parameters: num_labels={num_labels}")
                logging.info(f"Using prompt: {prompt}")

                # Override with reply-to if provided
                actual_output_stream = output_stream
                actual_output_subject = output_subject

                if local_env == "0" and msg.headers and "reply-to" in msg.headers:
                    actual_output_subject = msg.headers["reply-to"]
                    logging.info(
                        f"Using reply-to header for output: stream={actual_output_stream}, subject={actual_output_subject}"
                    )
                else:
                    logging.info(
                        f"Using standard output: stream={actual_output_stream}, subject={actual_output_subject}"
                    )

                # Process the image
                try:
                    # Convert image data to a format that can be processed by process_request
                    # It expects base64-encoded content, so we need to encode our binary image data
                    base64_encoded = base64.b64encode(image_data).decode("utf-8")

                    # Create a document structure with base64-encoded image data
                    document = {
                        "id": message_data.get(
                            "id", str(datetime.datetime.now().timestamp())
                        ),
                        "source": {
                            "uri": uri,
                            "file_name": os.path.basename(uri),
                            "file_type": os.path.splitext(uri)[1][
                                1:
                            ].lower(),  # Get extension without the dot
                            "content": base64_encoded,
                        },
                    }

                    # Create a list of documents (just one in this case)
                    list_docs = [document]

                    loop = asyncio.get_running_loop()

                    # Process the image based on the selected mode
                    logging.info(
                        f"Processing image with mode: {message_mode}, prompt: {prompt}"
                    )

                    if message_mode == "tagging":
                        # For tagging mode, use the original process_request for image tagging
                        # Import directly from the module when needed
                        from src.utils_tagging import (
                            process_request as process_request_tagging,
                        )

                        logging.info(f"Tagging with num_labels={num_labels}")
                        data, documents_non_teathred = await asyncio.to_thread(
                            process_request_tagging,
                            list_docs=list_docs,
                            num_labels=num_labels,
                            model=model,
                            processor=processor,
                            jobs={new_task.uid: new_task},
                            new_task=new_task,
                            use_onnx=USE_ONNX,
                            device=device,
                            prompt=prompt,
                            use_openvino=USE_OPENVINO,
                        )
                    else:  # message_mode == "captioning"
                        # For captioning mode, use the captioning process_request
                        # Import directly from the module when needed
                        from src.utils_captioning import (
                            process_request as process_request_captioning,
                        )

                        # Default parameters for captioning
                        max_new_tokens = 100
                        min_new_tokens = 10
                        temperature = 1.0
                        diversity_penalty = 0.0
                        repetition_penalty = 1.0
                        no_repeat_ngram_size = 0
                        num_beams = 2

                        logging.info(
                            f"Captioning with max_tokens={max_new_tokens}, num_beams={num_beams}"
                        )
                        data, documents_non_teathred = await asyncio.to_thread(
                            process_request_captioning,
                            list_docs=list_docs,
                            processor=processor,
                            max_new_tokens=max_new_tokens,
                            min_new_tokens=min_new_tokens,
                            temperature=temperature,
                            diversity_penalty=diversity_penalty,
                            repetition_penalty=repetition_penalty,
                            no_repeat_ngram_size=no_repeat_ngram_size,
                            num_beams=num_beams,
                            model=model,
                            jobs={new_task.uid: new_task},
                            new_task=new_task,
                            device=device,
                            prompt=prompt,
                            use_openvino=USE_OPENVINO,
                        )

                    logging.info("Image processing task completed.")

                    # Create response object with safe data copy
                    out = Index_Response(
                        status={"code": 200, "message": "Success"},
                        data=copy.deepcopy(data),
                        error="",
                        number_documents_treated=len(data),
                        number_documents_non_treated=len(documents_non_teathred),
                        list_id_not_treated=documents_non_teathred,
                        memory_used=str(
                            psutil.virtual_memory()[2]
                        ),  # Memory used in the process
                        ram_used=str(round(psutil.virtual_memory()[3] / 1000000000, 2)),
                    )

                    logging.warning(f"Percentage of memory use: {out.memory_used} %")
                    logging.warning(f"RAM used in GB: {out.ram_used} GB")

                    for doc in documents_non_teathred:
                        key = list(doc.keys())[0]
                        logging.error(f"document with id: {key} reason: {doc.get(key)}")

                    # Convert to JSON for sending with additional error handling
                    try:
                        result_data = out.model_dump()
                        logging.info(
                            f"Model dump successful, result_data type: {type(result_data)}"
                        )
                    except Exception as dump_error:
                        logging.error(f"Error in model_dump: {str(dump_error)}")
                        # Fallback to a manual dictionary
                        result_data = {
                            "status": {"code": 200, "message": "Success"},
                            "error": "",
                            "number_documents_treated": len(data),
                            "number_documents_non_treated": len(documents_non_teathred),
                            "memory_used": str(psutil.virtual_memory()[2]),
                            "ram_used": str(
                                round(psutil.virtual_memory()[3] / 1000000000, 2)
                            ),
                        }

                        # Add a simplified version of the data
                        simplified_data = []
                        try:
                            for item in data:
                                if isinstance(item, dict):
                                    simple_item = {"id": item.get("id", "unknown")}
                                    # Add basic source info if available
                                    if "source" in item and isinstance(
                                        item["source"], dict
                                    ):
                                        simple_item["file_name"] = item["source"].get(
                                            "file_name", ""
                                        )
                                        # Don't include potentially problematic content
                                    simplified_data.append(simple_item)
                            result_data["data"] = simplified_data
                        except Exception as simplify_error:
                            logging.error(
                                f"Error creating simplified data: {str(simplify_error)}"
                            )
                            result_data["data"] = [
                                {"id": "error", "message": "Could not process data"}
                            ]

                    # Send success response
                    await msg.ack()

                    # Ensure output stream exists before publishing
                    stream_exists = await ensure_stream_exists(
                        js, actual_output_stream, [actual_output_subject]
                    )

                    if not stream_exists:
                        logging.error(
                            f"Output stream {actual_output_stream} does not exist and could not be created"
                        )
                        return

                    # Try publishing with more detailed error information
                    try:
                        # Serialize and encode outside the publish call for better error handling
                        json_string = json.dumps(result_data)
                        encoded_data = json_string.encode()

                        logging.info(
                            f"Publishing to {actual_output_subject} in stream {actual_output_stream}"
                        )
                        logging.info(f"Message size: {len(encoded_data)} bytes")

                        # Publish with timeout
                        publish_result = await asyncio.wait_for(
                            js.publish(
                                actual_output_subject,
                                encoded_data,
                                stream=actual_output_stream,
                            ),
                            timeout=10.0,
                        )
                        logging.info(
                            f"Published result to {actual_output_subject}, sequence: {publish_result.seq}"
                        )
                    except asyncio.TimeoutError:
                        logging.error("Timeout publishing result to NATS stream")
                        logging.info(
                            "Message was acknowledged, but publishing to output stream timed out"
                        )
                    except Exception as pub_error:
                        logging.error(f"Error publishing result: {str(pub_error)}")
                        logging.info(
                            "Message was acknowledged, but publishing to output stream failed"
                        )

                    # Clean up
                    new_task.status = f"Job {new_task.uid} Finished code {200}"
                    del data
                    del out
                    gc.collect()

                except Exception as e:
                    logging.error(f"Processing error: {str(e)}")
                    ex_type, ex_value, ex_traceback = sys.exc_info()
                    logging.error(f"Exception {ex_type} value {str(ex_value)}")

                    # Process the error and send an error response
                    error_message = f"Processing error: {str(e)}"
                    out = Index_Response()
                    from detectaicore import print_stack

                    json_compatible_item_data = print_stack(out)

                    # Modified error handling to simplify and make more robust
                    try:
                        # First try to acknowledge the message to prevent redelivery
                        try:
                            await msg.ack()
                            logging.info("Message acknowledged for error case")
                        except Exception as ack_error:
                            logging.error(
                                f"Failed to acknowledge message: {str(ack_error)}"
                            )

                        # Try to publish error response with simplified error data
                        error_response = {
                            "status": {"code": 500, "message": "Error"},
                            "error": error_message,
                            "error_type": "processing-error",
                        }

                        # Ensure output stream exists
                        stream_exists = await ensure_stream_exists(
                            js, output_stream, [output_subject]
                        )

                        if stream_exists:
                            try:
                                await js.publish(
                                    output_subject,
                                    json.dumps(error_response).encode(),
                                    stream=output_stream,
                                )
                                logging.info(f"Published simplified error response")
                            except Exception as pub_error:
                                logging.error(
                                    f"Failed to publish error response: {str(pub_error)}"
                                )
                    except Exception as error_handling_error:
                        logging.error(
                            f"Error in error handling: {str(error_handling_error)}"
                        )

                time2 = datetime.datetime.now()
                time_diff = time2 - time1
                tf = time_diff.total_seconds()
                logging.info(f"Processing time: {tf} seconds")

            except json.JSONDecodeError as e:
                logging.error(f"Error decoding JSON message: {e}")
                # Create empty message_data for JSON decode errors
                empty_message = {"batchId": "unknown", "source": {}, "state": {}}

                # Simplified error handling for JSON decode errors
                try:
                    await msg.ack()
                    logging.info("Message acknowledged for JSON decode error")
                except Exception as ack_error:
                    logging.error(f"Failed to acknowledge message: {str(ack_error)}")

                # Try to send a simplified error message
                try:
                    error_response = {
                        "status": {"code": 400, "message": "Bad Request"},
                        "error": f"Error parsing message: {str(e)}",
                        "error_type": "json-decode-error",
                    }

                    await ensure_stream_exists(js, output_stream, [output_subject])

                    await js.publish(
                        output_subject,
                        json.dumps(error_response).encode(),
                        stream=output_stream,
                    )
                    logging.info("Published JSON decode error response")
                except Exception as pub_error:
                    logging.error(
                        f"Failed to publish JSON decode error: {str(pub_error)}"
                    )

            except Exception as e:
                logging.error(f"Error processing message: {e}")

                # Simplified error handling for general errors
                try:
                    await msg.ack()
                    logging.info("Message acknowledged for general error")
                except Exception as ack_error:
                    logging.error(f"Failed to acknowledge message: {str(ack_error)}")

                # Try to send a simplified error message
                try:
                    error_response = {
                        "status": {"code": 500, "message": "Internal Server Error"},
                        "error": f"Error processing message: {str(e)}",
                        "error_type": "general-error",
                    }

                    await ensure_stream_exists(js, output_stream, [output_subject])

                    await js.publish(
                        output_subject,
                        json.dumps(error_response).encode(),
                        stream=output_stream,
                    )
                    logging.info("Published general error response")
                except Exception as pub_error:
                    logging.error(f"Failed to publish general error: {str(pub_error)}")
            finally:
                if heartbeat_task:
                    logging.info("Stopping heartbeat task")
                    stop_heartbeat.set()
                    try:
                        heartbeat_task.cancel()
                        await asyncio.wait_for(
                            asyncio.shield(heartbeat_task), timeout=2.0
                        )
                        logging.info("Heartbeat task cancelled successfully")
                    except asyncio.TimeoutError:
                        logging.warning(
                            "Timeout while waiting for heartbeat task to cancel"
                        )
                    except Exception as e:
                        logging.error(f"Error cancelling heartbeat task: {e}")

        # Configure consumer with environment-specific timeout
        ack_wait_seconds = (
            3600 if local_env == "1" else 600
        )  # 1 hour for local, 10 min for prod

        # Use a unique consumer name that doesn't depend on prompt
        consumer_config = ConsumerConfig(
            durable_name=f"image-processor-{datetime.datetime.now().strftime('%Y%m%d')}",
            deliver_group="image-processing-group",
            ack_wait=ack_wait_seconds,  # Environment-specific timeout
            max_deliver=3,  # Limit redeliveries
            ack_policy=AckPolicy.EXPLICIT,  # Explicit ack policy
        )

        # Setup version endpoint
        await setup_version_endpoint(nc)

        # Setup health check endpoint
        await setup_health_check_endpoint(nc)

        # Pull messages from the stream
        sub = await js.pull_subscribe(
            input_subject,
            stream=input_stream,
            durable=consumer_config.durable_name,
            config=consumer_config,
        )

        logging.info(f"Subscribed to {input_subject} in stream {input_stream}")
        logging.info(
            f"Using ack_wait of {ack_wait_seconds} seconds in environment LOCAL_ENV={local_env}"
        )

        while nc.is_connected and not shutdown_event.is_set():
            try:
                messages = await sub.fetch(batch=1)
                for msg in messages:
                    if shutdown_event.is_set():
                        logging.info("Shutdown requested, stopping message processing")
                        break
                    await cb(msg)
            except nats.errors.TimeoutError:
                pass  # Silently ignore timeout errors
            except Exception as e:
                logging.error(f"Error fetching messages: {e}")
                # Brief pause to avoid fast retries if there's an issue
                await asyncio.sleep(1)

        logging.info("Exiting message processing loop")

    except Exception as e:
        logging.error(f"Error in NATS subscription: {e}")
    finally:
        logging.info("Closing NATS connection...")
        await nc.close()
        logging.info("NATS connection closed")
