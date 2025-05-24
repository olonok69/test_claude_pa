from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional, Union
from pydantic_settings import BaseSettings
import json
import logging


class Index_Response(BaseModel):
    """
    this class contains the response from the OCR process
    """

    status: Dict = {}  # status code and message
    data: Optional[Union[dict, List]] = None  # Data extracted from the OCR process
    error: str = ""  # Error message
    number_documents_treated: int = 0  # Number of documents treated
    number_documents_non_treated: int = 0  # Number of documents not treated
    list_id_not_treated: List = []  # List of documents not treated
    memory_used: Optional[str] = ""  # Memory used in the process
    ram_used: Optional[str] = ""  # RAM used in the process
    processing_time: Optional[str] = ""  # Processing time


class Elastic_Data(BaseModel):
    id: str
    index: str
    source: Dict[str, Union[str, Dict[str, Dict[str, Union[float, str]]]]]


class PII_Request(BaseModel):
    """
    this class contains all information related to a document read from a ElasticSearch query
    """

    documents: Optional[List[Dict]]  # List of Dictionaries from Elastic
    cypher: Optional[int]  # If the content it is encripted or not
    req: Optional[Dict]  # OCR Request
    documents_non_teathred: Optional[List]  # List of documents not treated

    data: Optional[Union[dict, List]]  # Data extracted from the OCR process
    list_docs: Optional[List]  # List of documents to be treated


class Settings(BaseSettings):
    """
    this class contains the settings for the PII/GDPR  process
    """

    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Sensitivity PII/GDPR API"


from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional, Union


class SuccessOutcome(BaseModel):
    """Outcome model for successful OCR processing"""

    type: str = Field("success", description="Indicates successful processing")
    extractedText: str = Field(
        ..., description="The extracted text from OCR processing"
    )
    language: str = Field(..., description="The language used for OCR processing")


class ErrorOutcome(BaseModel):
    """Outcome model for failed OCR processing"""

    type: str = Field("error", description="Indicates error processing")
    message: str = Field(
        ..., description="Error message describing the processing failure"
    )


class Source(BaseModel):
    """Source information for the document"""

    uri: str = Field(..., description="URI of the document to process")
    # Add other source fields if needed


class NatResponseMessage(BaseModel):
    """
    Response message structure for NAT output
    This is the complete message that will be sent back via NATS
    """

    version: str = Field("1.0", description="API version")
    batchId: str = Field(..., description="Batch identifier from the original message")
    source: Dict[str, Any] = Field(
        ..., description="Source information from the original message"
    )
    outcome: Union[SuccessOutcome, ErrorOutcome] = Field(
        ..., description="Processing outcome - either success or error"
    )
    state: Dict[str, Any] = Field(
        default_factory=dict, description="State information from the original message"
    )


# Example of how to use these models in your processing function:
def create_success_response(
    message_data: Dict[str, Any], extracted_text: str, language: str
) -> Dict[str, Any]:
    """Create a success response using the Pydantic models"""
    response = NatResponseMessage(
        batchId=message_data.get("batchId"),
        source=message_data.get("source", {}),
        outcome=SuccessOutcome(extractedText=extracted_text, language=language),
        state=message_data.get("state", {}),
    )
    return response.model_dump()


async def handle_success_and_acknowledge(
    js,
    msg,
    message_data: Dict[str, Any],
    extracted_text: str,
    language: str,
    output_stream: str,
    output_subject: str,
    local_env: str = "0",
) -> None:
    """
    Create and send a success response message and acknowledge the original message.

    Args:
        js: JetStream context
        msg: NATS message object
        message_data: The parsed message data
        extracted_text: The text extracted from OCR processing
        language: The language used for processing
        output_stream: Default output stream
        output_subject: Default output subject
        local_env: Local environment flag
    """
    try:
        # Create success response
        response = NatResponseMessage(
            batchId=message_data.get("batchId"),
            source=message_data.get("source", {}),
            outcome=SuccessOutcome(extractedText=extracted_text, language=language),
            state=message_data.get("state", {}),
        )

        # Convert to dict
        result_data = response.model_dump()

        # Determine output stream and subject
        actual_output_stream = output_stream
        actual_output_subject = output_subject

        # Check for reply-to header in non-local environment
        if local_env == "0" and msg.headers and "reply-to" in msg.headers:
            actual_output_subject = msg.headers["reply-to"]
            logging.info(
                f"Using reply-to header for output: stream={actual_output_stream}, subject={actual_output_subject}"
            )

        # Publish the success message
        await js.publish(
            actual_output_subject,
            json.dumps(result_data).encode(),
            stream=actual_output_stream,
            headers={
                "batch-id": message_data.get("batchId"),
            },
        )

        logging.info(
            f"Published processing result in: {actual_output_subject} of stream {actual_output_stream}"
        )

    except Exception as e:
        # If we fail to send the success response, log it
        logging.error(f"Failed to send success response: {str(e)}")

        # Try to send an error response instead
        try:
            error_message = f"Failed to publish success response: {str(e)}"
            await handle_error_and_acknowledge(
                js,
                msg,
                message_data,
                error_message,
                "success-publish-error",
                output_stream,
                output_subject,
                local_env,
            )
            return  # Skip acknowledge as it's handled in error method
        except Exception as err_ex:
            logging.error(f"Failed to send error after success failure: {str(err_ex)}")

    # Acknowledge the message if we haven't done so through the error handler
    try:
        await msg.ack()
        logging.info("Successfully acknowledge message")
    except Exception as e:
        logging.error(f"Failed to acknowledge message: {str(e)}")


def create_error_response(
    message_data: Dict[str, Any], error: Exception
) -> Dict[str, Any]:
    """Create an error response using the Pydantic models"""
    response = NatResponseMessage(
        batchId=message_data.get("batchId"),
        source=message_data.get("source", {}),
        outcome=ErrorOutcome(message=f"Processing error: {str(error)}"),
        state=message_data.get("state", {}),
    )
    return response.model_dump()


async def handle_error_and_acknowledge(
    js,
    msg,
    message_data: Dict[str, Any],
    error_message: str,
    error_type: str,
    output_stream: str,
    output_subject: str,
    local_env: str = "0",
) -> None:
    """
    Create and send an error response message and acknowledge the original message.

    Args:
        js: JetStream context
        msg: NATS message object
        message_data: The parsed message data (or empty dict if not available)
        error_message: The error message to include
        error_type: Type of error for the headers
        output_stream: Default output stream
        output_subject: Default output subject
        local_env: Local environment flag
    """
    try:
        # Use provided message_data or create a minimal version
        batch_id = message_data.get("batchId", "unknown")

        # Create an error response
        error_response = NatResponseMessage(
            batchId=batch_id,
            source=message_data.get("source", {}),
            outcome=ErrorOutcome(message=error_message),
            state=message_data.get("state", {}),
        )

        # Determine output stream and subject
        actual_output_stream = output_stream
        actual_output_subject = output_subject

        # Check for reply-to header in non-local environment
        if local_env == "0" and msg.headers and "reply-to" in msg.headers:
            actual_output_subject = msg.headers["reply-to"]
            logging.info(
                f"Using reply-to header for error output: subject={actual_output_subject}"
            )

        # Publish the error message
        await js.publish(
            actual_output_subject,
            json.dumps(error_response.model_dump()).encode(),
            stream=actual_output_stream,
            headers={"batch-id": batch_id, "error-type": error_type},
        )

        logging.warning(f"Published error response of type '{error_type}'")

    except Exception as e:
        # If we fail to send the error response, log it but don't throw
        logging.error(f"Failed to send error response: {str(e)}")

    # Always acknowledge the message
    try:
        await msg.ack()
    except Exception as e:
        logging.error(f"Failed to acknowledge message: {str(e)}")
