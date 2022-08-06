import logging
import os
from os.path import dirname

from dotenv import load_dotenv

load_dotenv("../.env")

# Endpoint auth
API_USERNAME = os.getenv("API_USERNAME", "mbaza")
API_PASSWORD = os.getenv("API_PASSWORD", "ttssecret")

# Auth configs
API_SECRET_KEY = os.environ["API_SECRET_KEY"]
API_ALGORITHM = os.environ["API_ALGORITHM"]
API_ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.environ["API_ACCESS_TOKEN_EXPIRE_MINUTES"]
)  # infinity

if os.getenv("APP_LOCAL_RUN") in ["1", "true", "True", "TRUE"]:
    FASTPITCH_PATH = (
        dirname(__file__)
        + "/../../NVIDIADeepLearning/PyTorch/SpeechSynthesis/FastPitch"
    )
else:
    FASTPITCH_PATH = "/code/NVIDIADeepLearning/PyTorch/SpeechSynthesis/FastPitch"
FASTPITCH_PATH = os.getenv("FASTPITCH_PATH", FASTPITCH_PATH)


log_levels = {'error': logging.ERROR, 'debug': logging.DEBUG, 'info': logging.INFO}
APP_LOG_LEVEL = log_levels[os.environ.get('APP_LOG_LEVEL').lower()] \
    if (os.environ.get('APP_LOG_LEVEL') and os.environ.get('APP_LOG_LEVEL').lower() in log_levels) \
    else logging.INFO

APP_DEVICE = os.environ.get("APP_DEVICE") or "cpu"
APP_PORT = os.environ.get('SRV_PORT') or "6969"
APP_LANG = os.environ.get('APP_LANG') or "eng"
APP_SAMPLE_TEXT = os.environ.get('APP_SAMPLE_TEXT') or ". This is a sample input text ."

APP_FASTPITCH_MODEL_FILE = os.getenv("APP_FASTPITCH_MODEL_FILE")
APP_WAVEGLOW_MODEL_FILE = os.getenv("APP_WAVEGLOW_MODEL_FILE", "nvidia_waveglow256pyt_fp16.pt")

# (APP_SENTENCE_MAX_WORDS * APP_SENTENCE_INFER_BATCH_SIZE) = number of words processed at once by trained model
APP_SENTENCE_MAX_WORDS = int(os.getenv("APP_SENTENCE_MAX_WORDS", 40))
APP_SENTENCE_INFER_BATCH_SIZE = int(os.getenv("APP_SENTENCE_INFER_BATCH_SIZE", 10))
