from vertexai.generative_models import GenerativeModel, Part
import vertexai.generative_models as generative_models


def init_model(model: str = "gemini-2.0-flash-001"):
    """Initializes the generative model with the specified model name.
    Args:
        model (str): The name of the model to use
        Returns:
        GenerativeModel: The initialized generative model
    """
    return GenerativeModel(
        model_name=model,
        system_instruction=[
            """You a helpful agent spezialized in tasks with audio files."""
        ],
        safety_settings={
            generative_models.HarmCategory.HARM_CATEGORY_HATE_SPEECH: generative_models.HarmBlockThreshold.BLOCK_ONLY_HIGH,
            generative_models.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: generative_models.HarmBlockThreshold.BLOCK_ONLY_HIGH,
            generative_models.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: generative_models.HarmBlockThreshold.BLOCK_ONLY_HIGH,
            generative_models.HarmCategory.HARM_CATEGORY_HARASSMENT: generative_models.HarmBlockThreshold.BLOCK_ONLY_HIGH,
        },
        generation_config={
            "max_output_tokens": 8192,
            "temperature": 1,
            "top_p": 0.95,
        },
    )


def generate_generative_model(model, filename, bucket, prompt):
    """Generates text based on the audio file and prompt
    Args:
        model (GenerativeModel): The model to use for the generation
        filename (str): The name of the audio file
        bucket (str): The name of the bucket where the audio file is stored
        prompt (str): The prompt to use for the generation
        model (str): The model to use for the generation
        Returns:
        str: The generated text"""

    audio1 = Part.from_uri(
        f"gs://{bucket}/{filename}",
        mime_type="audio/mpeg",
    )
    text1 = Part.from_text(prompt)

    try:
        response = model.generate_content([audio1, text1])
        summary = response.text
    except Exception as e:
        print(f"Error during summarization: {e}")
        return None

    return summary
