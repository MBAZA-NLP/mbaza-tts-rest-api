import sys
from tts.app import settings
from os import path

# Load packages relative to FastPitch
sys.path.append(settings.FASTPITCH_PATH)
from common.text.text_processing import TextProcessing

### AS - Transliteration
filepath = path.abspath(path.join(path.dirname(__file__), "..", "..", "kinyar_transliterations.csv"))
with open(filepath) as fin:
    kinyar_translit = {data.strip().split(',')[0]:data.strip().split(',')[1] for data in fin.readlines()[1:]}


def transliterate(text):
    for k, v in kinyar_translit.items():
        text = text.replace(k, v)

    if text[:2] != '. ':
        text = '. ' + text
    if text[-2:] != ' .':
        text = text + ' .'

    return text


class KinyarwandaTextProcessing(TextProcessing):

    def encode_text(self, text, return_all=False):
        text = transliterate(text)
        return TextProcessing.encode_text(self, text)
