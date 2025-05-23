from pathlib import Path
import warnings
import time

warnings.filterwarnings("ignore")
with warnings.catch_warnings():
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    from optimum.intel.openvino import OVModelForSpeechSeq2Seq
import os
import torch

with warnings.catch_warnings():
    warnings.filterwarnings(
        "ignore",
        message="The attention mask is not set and cannot be inferred from input because pad token is same as eos token.",
    )
    from transformers import AutoProcessor
    from transformers.pipelines.audio_utils import ffmpeg_read
    from transformers import pipeline


BATCH_SIZE = 16
MAX_AUDIO_MINS = 30  # maximum audio input in minutes


def create_processor(model_id):
    return AutoProcessor.from_pretrained(model_id)


def create_ov_model(model_path: str, ov_config: dict):

    ov_model = OVModelForSpeechSeq2Seq.from_pretrained(
        model_path, ov_config=ov_config, compile=False
    )
    ov_model.to("AUTO")
    ov_model.compile()
    return ov_model


def create_ov_pipeline(ov_model, processor, model_id: str):
    """
    Create Pipeline Transformers with OV_Model
    """
    generate_kwargs = (
        {"language": "en", "task": "transcribe"} if not model_id.endswith(".en") else {}
    )

    ov_pipe = pipeline(
        "automatic-speech-recognition",
        model=ov_model,
        tokenizer=processor.tokenizer,
        feature_extractor=processor.feature_extractor,
        max_new_tokens=128,
        chunk_length_s=15,
        generate_kwargs=generate_kwargs,
        device=torch.device("cpu"),
    )
    return ov_pipe


def forward_ov_time(pipe_forward, *args, **kwargs):

    start_time = time.time()
    result = pipe_forward(*args, **kwargs)
    ov_time = time.time() - start_time
    ov_time = round(ov_time, 2)
    return result


def extract_input_features(sample, processor):

    input_features = processor(
        sample,
        sampling_rate=16000,
        return_tensors="pt",
    )
    return input_features
