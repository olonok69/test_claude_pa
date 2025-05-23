import os
import json
import datetime
import logging
import socket
import psutil
import asyncio
import nats
from detectaicore.src.ssl_utils import NatsSSLContextBuilder
from nats.js.api import (
    ConsumerConfig,
    RetentionPolicy,
    DiscardPolicy,
    StreamConfig,
)


async def setup_version_endpoint(nc, version_subject: str, queue_group: str):
    """
    Sets up a NATS endpoint that responds with the application version.
    """

    async def version_handler(msg):
        try:
            app_version = os.getenv("APPLICATIONVERSION", "unknown")
            response = {
                "version": app_version,
                "hostname": socket.gethostname(),
                "timestamp": datetime.datetime.now().isoformat(),
            }
            await msg.respond(json.dumps(response).encode())
            logging.debug(f"Version request handled: {app_version}")
        except Exception as e:
            logging.error(f"Error handling version request: {e}")
            error_response = {
                "error": "Failed to get version information",
                "timestamp": datetime.datetime.now().isoformat(),
            }
            await msg.respond(json.dumps(error_response).encode())

    # Subscribe to the version subject with queue group
    await nc.subscribe(version_subject, queue=queue_group, cb=version_handler)
    logging.debug(
        f"Version endpoint setup complete. Subject: {version_subject}, Queue: {queue_group}"
    )


async def setup_health_check_endpoint(nc, health_subject: str):
    """
    Sets up NATS endpoints that respond to health check requests.
    """
    hostname = socket.gethostname()
    instance_subject = f"{health_subject}.{hostname}"
    broadcast_subject = f"{health_subject}.>"

    async def health_check_handler(msg):
        try:
            response = {
                "status": "OK",
                "hostname": hostname,
                "timestamp": datetime.datetime.now().isoformat(),
                "uptime": psutil.boot_time(),
                "memory_usage": psutil.virtual_memory().percent,
                "cpu_usage": psutil.cpu_percent(),
            }
            await msg.respond(json.dumps(response).encode())
            logging.debug(f"Health check handled for subject: {msg.subject}")
        except Exception as e:
            logging.error(f"Health check failed: {e}")
            error_response = {
                "status": "ERROR",
                "hostname": hostname,
                "error": str(e),
                "timestamp": datetime.datetime.now().isoformat(),
            }
            await msg.respond(json.dumps(error_response).encode())

    await nc.subscribe(instance_subject, cb=health_check_handler)
    logging.debug(f"Health check endpoint setup on subject: {instance_subject}")

    await nc.subscribe(broadcast_subject, cb=health_check_handler)
    logging.debug(
        f"Health check endpoint setup on broadcast subject: {broadcast_subject}"
    )


async def ensure_stream_exists(js, stream_name, subjects):
    """
    Ensures that a stream exists, creating it if necessary.
    """
    try:
        # Check if stream exists
        stream_info = await js.stream_info(stream_name)
        logging.info(f"Stream '{stream_name}' already exists.")

        # Log stream configuration for debugging
        config = stream_info.config
        logging.info(f"Stream config: name={config.name}, subjects={config.subjects}")
        logging.info(
            f"Stream limits: max_msgs={config.max_msgs}, max_bytes={config.max_bytes}, max_age={config.max_age}s"
        )
        logging.info(
            f"Stream stats: messages={stream_info.state.messages}, bytes={stream_info.state.bytes}"
        )

        # Check if the subjects match and update if needed
        current_subjects = set(config.subjects)
        requested_subjects = set(subjects)

        if not requested_subjects.issubset(current_subjects):
            logging.warning(
                f"Stream '{stream_name}' exists but doesn't include all requested subjects."
            )
            missing_subjects = requested_subjects - current_subjects
            logging.warning(f"Missing subjects: {missing_subjects}")

            # Update the stream with the new subjects
            try:
                new_subjects = list(current_subjects.union(requested_subjects))
                updated_config = StreamConfig(
                    name=stream_name,
                    subjects=new_subjects,
                    retention=config.retention,
                    max_age=config.max_age,
                    duplicate_window=config.duplicate_window,
                    discard=config.discard,
                    max_msgs=config.max_msgs,
                    max_bytes=config.max_bytes,
                    max_msg_size=config.max_msg_size
                    or 1048576,  # Default to 1MB if not set
                )
                await js.update_stream(config=updated_config)
                logging.info(
                    f"Updated stream '{stream_name}' with subjects: {new_subjects}"
                )
            except Exception as update_error:
                logging.error(f"Failed to update stream subjects: {str(update_error)}")

        return True
    except Exception as e:
        logging.warning(f"Stream '{stream_name}' not found, creating it: {str(e)}")
        try:
            # Create the stream with more generous limits
            stream_config = StreamConfig(
                name=stream_name,
                subjects=subjects,
                retention=RetentionPolicy.WORK_QUEUE,
                max_age=30 * 24 * 60 * 60,  # 30 days
                duplicate_window=6 * 60,  # 6 minutes
                discard=DiscardPolicy.NEW,
                max_msgs=100000,  # Allow up to 100k messages
                max_bytes=1073741824,  # 1GB limit
                max_msg_size=10485760,  # 10MB per message
            )
            await js.add_stream(config=stream_config)
            logging.info(f"Stream '{stream_name}' created with subjects: {subjects}")
            return True
        except Exception as create_error:
            logging.error(f"Failed to create stream: {str(create_error)}")
            # Try one more time with minimal configuration
            try:
                simple_config = StreamConfig(
                    name=stream_name,
                    subjects=subjects,
                )
                await js.add_stream(config=simple_config)
                logging.info(f"Stream '{stream_name}' created with minimal config")
                return True
            except Exception as simple_error:
                logging.error(
                    f"Failed to create stream with minimal config: {str(simple_error)}"
                )
                return False


async def setup_stream(nats_url, local_env, stream_name, subjects):
    """
    Set up a NATS stream with the specified name and subjects.
    """

    nc = None
    try:
        # Connect to NATS using certificate if local_env is "0"
        if local_env == "0":
            ssl_builder = NatsSSLContextBuilder()
            ssl_context = ssl_builder.create_ssl_context()
            nc = await nats.connect(nats_url, tls=ssl_context)
        else:
            nc = await nats.connect(nats_url)

        js = nc.jetstream()
        try:
            await js.stream_info(stream_name)
            logging.warning(f"Stream '{stream_name}' already exists.")
        except Exception as e:
            stream_config = StreamConfig(
                name=stream_name,
                subjects=subjects,
                retention=RetentionPolicy.WORK_QUEUE,
                max_age=30 * 24 * 60 * 60,  # 30 days
                duplicate_window=6 * 60,  # 6 minutes
                discard=DiscardPolicy.NEW,  # Discard new messages if the stream is full
            )
            await js.add_stream(config=stream_config)
            logging.info(f"Stream '{stream_name}' created with subjects: {subjects}")

        # Return the connection so it can be closed later
        return nc
    except Exception as e:
        logging.error(f"Error setting up stream: {e}")
        if nc:
            await nc.close()
        raise
