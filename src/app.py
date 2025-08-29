from fastapi import FastAPI
from contextlib import asynccontextmanager
from db.mongodbconnection import connectDB
from db.mongodbconnection import disconnect_mongodb
from models.audioText import SpeechToText
from models.question_agent import Question_Agent
from models.textSpeech import TextToSpeech_
from models.summary_agent import summarize_agent
from fastapi.middleware.cors import CORSMiddleware
from router.interview_router import router as interview_router
from dotenv import load_dotenv
import os
from logs import ModuleLogger
load_dotenv()
logger = ModuleLogger("startup")
## here in the origin we will need the
# server_front_end and backend_server 2
origins = os.getenv("BOTAPP_ORIGINS")
if origins != "":
    allow_origins = origins.split(",")
else:
    allow_origins = "*"



@asynccontextmanager
async def lifespan(
    app: FastAPI,
):  ## cant use on_envent("startup") because it is deprecated for more lifespan examples follow fastapi docs.

    logger.INFO("Loading models at startup...")

    validation = await connectDB() 

    if not validation:
        raise ConnectionRefusedError("Database connection failed!")

    app.state.question_agent = await Question_Agent().load_model()

    app.state.stt = SpeechToText()
    await app.state.stt.load_model_initialize_pipeline()  # text model

    app.state.tts = TextToSpeech_()
    await app.state.tts.load_model()  # speechmodel

    app.state.summarizer = await summarize_agent().load_model()  #

    print(" All models loaded successfully!")

    yield  # from here it will handle by app

    await disconnect_mongodb()
    print("Disconnecting the DB ending ... ")  # this will run the at shutdown of server


app = FastAPI(lifespan=lifespan,debug=True)

app.add_middleware(  ## CROS ORIGIN
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(interview_router)

# make the Socket structure and then build an audio input and output wala thing with it
# app.mount('/api/auxmet/interview-session',app=sio_app)
