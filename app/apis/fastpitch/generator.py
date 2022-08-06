import argparse
import io
import sys
import warnings
import numpy as np
import torch
import logging
from scipy.io.wavfile import write
from torch.nn.utils.rnn import pad_sequence
from pathlib import Path
from tts.app import settings

# Load packages relative to FastPitch
sys.path.append(settings.FASTPITCH_PATH)
from common.text import cmudict
from inference import (
    MeasureTime,
    build_pitch_transformation,
    load_and_setup_model,
    parse_args,
)
from waveglow import model as glow
from waveglow.denoiser import Denoiser
sys.modules["glow"] = glow

if settings.APP_LANG == "kin":
    from tts.app.apis.fastpitch.common.text.text_processing \
        import KinyarwandaTextProcessing as TextProcessing
else:
    from common.text.text_processing import TextProcessing

logger = logging.getLogger("tts")


class Generator:
    fastpitch = None
    waveglow = None
    denoiser = None
    device = None
    args = ...
    unk_args = ...

    def __init__(self):
        # Initialize arguments
        args = [
            "-i=n/a",
            "--fastpitch=" + settings.FASTPITCH_PATH + "/pretrained_models/fastpitch/" + settings.APP_FASTPITCH_MODEL_FILE,
            "--waveglow=" + settings.FASTPITCH_PATH + "/pretrained_models/waveglow/" + settings.APP_WAVEGLOW_MODEL_FILE,
            "--cmudict-path=" + settings.FASTPITCH_PATH + "/cmudict/cmudict-0.7b",
            "--wn-channels=256",
            "--batch-size=4",
            "--denoising-strength=0.01",
            "--repeats=1",
            "--speaker=0",
            "--n-speakers=1",
            "--energy-conditioning",
        ]
        if settings.APP_LANG == "eng":
            args += ["--p-arpabet=1.0"]
        if settings.APP_LANG == "kin":
            args += ["--p-arpabet=0.0",
                     "--warmup-steps=0",
                     "--symbol-set=kinyarwanda",
                     "--text-cleaners=kinyar_cleaners",
                     "--fade-out=0",
                     "--pace=0.8"]
        for a in args:
            sys.argv.append(a)

        parser = argparse.ArgumentParser(
            description="PyTorch FastPitch Inference", allow_abbrev=False
        )
        parser = parse_args(parser)
        self.args, self.unk_args = parser.parse_known_args()

        # Set gpu/cpu
        self.device = torch.device(settings.APP_DEVICE)

        [logger.debug("PARAMETER | " + str(k) + ":" + str(v)) for k, v in vars(self.args).items()]

        # Load Models
        if self.args.fastpitch != "SKIP":
            self.fastpitch = load_and_setup_model(
                "FastPitch",
                parser,
                self.args.fastpitch,
                self.args.amp,
                self.device,
                unk_args=self.unk_args,
                forward_is_infer=True,
                ema=self.args.ema,
                jitable=self.args.torchscript,
            )
            if self.args.torchscript:
                self.fastpitch = torch.jit.script(self.fastpitch)

        if self.args.waveglow != "SKIP":
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                self.waveglow = load_and_setup_model(
                    "WaveGlow",
                    parser,
                    self.args.waveglow,
                    self.args.amp,
                    self.device,
                    unk_args=self.unk_args,
                    forward_is_infer=True,
                    ema=self.args.ema,
                )
            self.denoiser = Denoiser(self.waveglow).to(self.device)
            self.waveglow = getattr(self.waveglow, "infer", self.waveglow)

        # Cleanup model arguments to prevent them from poisoning docker gunicorn
        for a in args:
            sys.argv.remove(a)

        # Misc initialization
        if self.args.p_arpabet > 0.0:
            cmudict.initialize(self.args.cmudict_path, keep_ambiguous=True)

        torch.backends.cudnn.benchmark = self.args.cudnn_benchmark

    def get_stream(self, text: [str]):
        fields = {"text": text}
        batches = self.prepare_input_sequence(fields=fields)

        gen_measures = MeasureTime(cuda=self.args.cuda)
        waveglow_measures = MeasureTime(cuda=self.args.cuda)

        gen_kw = {
            "pace": self.args.pace,
            "speaker": self.args.speaker,
            "pitch_tgt": None,
            "pitch_transform": build_pitch_transformation(self.args),
        }

        if self.args.torchscript:
            gen_kw.pop("pitch_transform")
            print("NOTE: Pitch transforms are disabled with TorchScript")

        for b in batches:
            if self.fastpitch is None:
                mel, mel_lens = b["mel"], b["mel_lens"]
            else:
                with torch.no_grad(), gen_measures:
                    mel, mel_lens, *_ = self.fastpitch(b["text"], **gen_kw)

            if self.waveglow is not None:
                with torch.no_grad(), waveglow_measures:
                    audios = self.waveglow(mel, sigma=self.args.sigma_infer)
                    audios = self.denoiser(
                        audios.float(), strength=self.args.denoising_strength
                    ).squeeze(1)

                waveglow_infer_perf = (
                    audios.size(0) * audios.size(1) / waveglow_measures[-1]
                )
                print("waveglow_samples/s {:.2f}".format(waveglow_infer_perf))
                print("waveglow_latency {:.2f}".format(waveglow_measures[-1]))

                out = []
                for i, audio in enumerate(audios):
                    audio = audio[: mel_lens[i].item() * self.args.stft_hop_length]

                    if self.args.fade_out:
                        fade_len = self.args.fade_out * self.args.stft_hop_length
                        fade_w = torch.linspace(1.0, 0.0, fade_len)
                        audio[-fade_len:] *= fade_w.to(audio.device)

                    audio = audio / torch.max(torch.abs(audio))
                    audio = audio.cpu().numpy() * 32768.0
                    audio = audio.astype(np.int16)

                    byte_io = io.BytesIO(bytes())
                    write(byte_io, self.args.sampling_rate, audio)
                    out.append(byte_io)
                return out

        raise Exception("Inference failed!")

    def prepare_input_sequence(self, fields):
        batch_size = self.args.batch_size
        dataset = self.args.dataset_path
        load_mels = (self.fastpitch is None)
        load_pitch = False

        tp = TextProcessing(self.args.symbol_set, self.args.text_cleaners, p_arpabet=self.args.p_arpabet)

        fields['text'] = [torch.LongTensor(tp.encode_text(text))
                          for text in fields['text']]
        order = np.argsort([-t.size(0) for t in fields['text']])

        fields['text'] = [fields['text'][i] for i in order]
        fields['text_lens'] = torch.LongTensor([t.size(0) for t in fields['text']])

        for t in fields['text']:
            print(tp.sequence_to_text(t.numpy()))

        if load_mels:
            assert 'mel' in fields
            fields['mel'] = [
                torch.load(Path(dataset, fields['mel'][i])).t() for i in order]
            fields['mel_lens'] = torch.LongTensor([t.size(0) for t in fields['mel']])

        if load_pitch:
            assert 'pitch' in fields
            fields['pitch'] = [
                torch.load(Path(dataset, fields['pitch'][i])) for i in order]
            fields['pitch_lens'] = torch.LongTensor([t.size(0) for t in fields['pitch']])

        if 'output' in fields:
            fields['output'] = [fields['output'][i] for i in order]

        # cut into batches & pad
        batches = []
        for b in range(0, len(order), batch_size):
            batch = {f: values[b:b + batch_size] for f, values in fields.items()}
            for f in batch:
                if f == 'text':
                    batch[f] = pad_sequence(batch[f], batch_first=True)
                elif f == 'mel' and load_mels:
                    batch[f] = pad_sequence(batch[f], batch_first=True).permute(0, 2, 1)
                elif f == 'pitch' and load_pitch:
                    batch[f] = pad_sequence(batch[f], batch_first=True)

                if type(batch[f]) is torch.Tensor:
                    batch[f] = batch[f].to(self.device)
            batches.append(batch)

        return batches
