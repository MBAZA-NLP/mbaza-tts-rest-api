from __future__ import annotations

import io
import uuid
import wave

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from tts.app.core.auth import get_current_user
from tts.app.core.text import get_sentences
from tts.app import settings

router = APIRouter()


class RequestData(BaseModel):
    text: str = settings.APP_SAMPLE_TEXT


@router.post("/speak", response_class=StreamingResponse)
async def speak(
    request: Request, data: RequestData, auth: Depends = Depends(get_current_user)
):
    sentences = get_sentences(data.text)
    # generate audio streams for the list of texts and read them to a list of wave objects
    wavs = []
    chunk_size = settings.APP_SENTENCE_INFER_BATCH_SIZE
    if len(sentences) > chunk_size:
        for chunk in [sentences[x:x+chunk_size] for x in range(0, len(sentences), chunk_size)]:
            wavs += read_into_wave(request, chunk)
    else:
        wavs += read_into_wave(request, sentences)

    # join wavs into a single bytestream
    out = io.BytesIO(bytes())
    if wavs:
        wo = wave.Wave_write(out)
        wo.setparams(wavs[0][0])
        for i in range(len(wavs)):
            wo.writeframes(wavs[i][1])
        wo.close()
    out.seek(0)

    headers = {
        "Content-Disposition": "attachment; filename=" + str(uuid.uuid4()) + ".wav"
    }
    return StreamingResponse(
        out, media_type="application/octet-stream", headers=headers
    )


def read_into_wave(request, sentences=[]):
    wavs = []
    for srm in request.app.generator.get_stream(sentences):
        wi = wave.Wave_read(srm)
        wavs.append([wi.getparams(), wi.readframes(wi.getnframes())])
        wi.close()
    return wavs
