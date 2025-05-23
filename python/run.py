import warnings
from pathlib import Path

warnings.filterwarnings("ignore")
with warnings.catch_warnings():

    warnings.filterwarnings("ignore", category=DeprecationWarning)

from optimum.intel.openvino import OVModelForSpeechSeq2Seq
import os

with warnings.catch_warnings():
    warnings.filterwarnings(
        "ignore",
        message="The attention mask is not set and cannot be inferred from input because pad token is same as eos token.",
    )

    from transformers import AutoProcessor

    from transformers.pipelines.audio_utils import ffmpeg_read

    from transformers import pipeline


from datasets import load_dataset, load_from_disk
import torch
import time
import datetime
import pprint

warnings.filterwarnings(
    "ignore",
    category=UserWarning,
    message="The attention mask is not set and cannot be inferred from input because pad token is same as eos token.",
)

warnings.filterwarnings(
    "ignore", category=DeprecationWarning, module="openvino.runtime"
)

with warnings.catch_warnings():

    warnings.filterwarnings("ignore", message="The attention mask is not set...")

ov_config = {"CACHE_DIR": ""}
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

model_id = "distil-whisper/distil-small.en"

processor = AutoProcessor.from_pretrained(model_id)


def extract_input_features(sample):

    input_features = processor(
        sample,
        sampling_rate=16000,
        return_tensors="pt",
    )
    return input_features


model_path = os.path.join(ROOT_DIR, "distil-whisper_distil-small.en")
ov_model = OVModelForSpeechSeq2Seq.from_pretrained(
    model_path, ov_config=ov_config, compile=False
)
ov_model.to("AUTO")
ov_model.compile()


file_path = Path("/mnt/d/repos/whispher/dataset/data-00000-of-00001.arrow")

if file_path.exists():

    dataset = load_from_disk(os.path.join(ROOT_DIR, "dataset"))
else:

    dataset = load_dataset(
        "hf-internal-testing/librispeech_asr_dummy",
        "clean",
        split="validation",
        trust_remote_code=True,
    )

sample = "male.wav"

with open(sample, "rb") as f:
    inputs = f.read()

inputs = ffmpeg_read(inputs, 16000)
input_features = extract_input_features(inputs)

BATCH_SIZE = 16
MAX_AUDIO_MINS = 30  # maximum audio input in minutes

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

ov_pipe_forward = ov_pipe._forward


def _forward_ov_time(*args, **kwargs):

    global ov_time
    start_time = time.time()
    result = pipe_forward(*args, **kwargs)
    ov_time = time.time() - start_time
    ov_time = round(ov_time, 2)
    return result


time1 = datetime.datetime.now()
quantized = False
pipe = None if quantized else ov_pipe
pipe_forward = None if quantized else ov_pipe_forward
audio_length_mins = len(inputs) / pipe.feature_extractor.sampling_rate / 60

inputs = {"array": inputs, "sampling_rate": pipe.feature_extractor.sampling_rate}
pipe._forward = _forward_ov_time
ov_text = pipe(inputs.copy(), batch_size=BATCH_SIZE)["text"]

time2 = datetime.datetime.now()
("#### TEXT ####")
print("+" * 100)
print("\n")
pprint.pprint(ov_text)
print("\n")
print("#### TEXT ####")
print(f"Processing Time {(time2-time1).seconds} Seconds")
