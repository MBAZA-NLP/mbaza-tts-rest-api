import logging
import os

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from tts.app import settings
from tts.app.apis.fastpitch.generator import Generator
from tts.app.core import auth
from tts.app.routes import views

# set logging
logging.getLogger("uvicorn.error").disabled = True
logger = logging.getLogger("tts")
logger.setLevel(settings.APP_LOG_LEVEL)
if not logger.hasHandlers():
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('[%(asctime)s] [%(process)d-%(thread)d] [%(levelname)s] %(message)s'))
    logger.addHandler(handler)

# create app object
app = FastAPI(
    title="Mbaza TTS [" + settings.APP_LANG + "] - " + settings.APP_DEVICE,
    description="TTS [" + settings.APP_LANG + "] component for Mbaza Chatbot, running on" + settings.APP_DEVICE,
    version="1.0.0",
    debug=settings.APP_LOG_LEVEL is logging.DEBUG,
    openapi_url="/openapi.json",
    docs_url="/",
    redoc_url="/redoc",
)

# set all CORS enabled origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# initialize and load models
app.generator = Generator()

# add endpoints
app.include_router(auth.router)
app.include_router(views.router)

logger.info("Visit http://localhost:" + settings.APP_PORT + " for a list of possible operations.")
logger.info('Ready!')

# start server locally for development
if os.getenv("APP_LOCAL_RUN") in ["1", "true", "True", "TRUE"]:
    import uvicorn
    uvicorn.run(
        app, proxy_headers=True, forwarded_allow_ips="*", host="localhost", port=settings.APP_PORT
    )
