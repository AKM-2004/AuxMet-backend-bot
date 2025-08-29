# from app import app
from db.mongodbconnection import get_mongodb_client
from bson import ObjectId
from fastapi import Request, HTTPException
from utils.tools import load_resume_data
import jwt
from dotenv import load_dotenv
from db.redisdb import redis_db
from logs import ModuleLogger
from pymongo import ReturnDocument
import numpy as np


logger = ModuleLogger("chat.controller")
load_dotenv()
import os

## load the models in the fast api pre connection

# this serve_chat contains all functions that are required in server
"""

This server_Chat contains all the function that are requred to do 


"""


class server_chat:
    def __init__(self, app):
        self.model = app.state.question_agent
        self.text_model = app.state.stt
        self.speech_model = app.state.tts
        self.summary_model = app.state.summarizer
        self.sessionTimeout = 30 * 60 * 1000
        self.cleanupInterval = 5 * 60 * 1000
        self.session_id = None
        self.session_status = None
        self.user_id = None
        self.rd = redis_db()
        client = get_mongodb_client()
        self.client = client["auxmet_db"]
        self.count_message = 0
        self.currnet_message = {}

    # async def create_session(self,sid,environ): # here user_id we will get from the cookie
    # if not sid:
    #     raise ValueError("sid is not given")

    # # here in sockets.io we can't use the the fastapi app middleweare that are build in like for cookieparsing here we need to make one cookie parser

    # cookie_header = environ.get('HTTP_COOKIE')
    # if not cookie_header:
    #     raise ValueError("can able to get HTTP_COOKIE")

    # try:
    #     cookie = SimpleCookie()
    #     cookie_dict = cookie.load(cookie_header)
    #     access_token = cookie_dict["access_token"].value

    #     playload = await JWT.decode(access_token,key = os.getenv("ACCESS_TOKEN_SECRET"),algorithms=os.getenv("ALGORITHMS"))
    #     self.user_id = playload.get("_id")

    #     self.session_status = "active"
    #     collection = self.client["Session"]
    #     resume_collec = self.client["Resume"]
    #     resume_data = resume_collec.find_one({"user_id":self.user_id})
    #     resume = resume_data["_id"]
    #     data = {
    #         "user_id": self.user_id,
    #         "resume": resume,
    #         "status": self.session_status
    #     }
    #     session_data = collection.insert_one(data)
    #     self.session_id = session_data["_id"]
    #     self.rd.session_hash_set(self.session_id,data)
    # except Exception as e:
    #     raise e

    async def end_session(self):
        # clear the cache memory
        # session_status to deactivate
        session_data = self.client["sessions"]
        self.session_status = "Deactivate"
        await session_data.find_one_and_update(
            {"_id": ObjectId(self.session_id)},
            {"$set": {"status": self.session_status}},
            return_document=ReturnDocument.AFTER,
        )

    async def get_text_input(self, input_audio_buffer):
        print("inside wala",input_audio_buffer)
        if  input_audio_buffer.size == 0:
            raise ValueError("there is not input audio")
        try:
            segments= await self.text_model.genererate_text(input_audio_buffer)
            print(segments)
            text = "".join([seg.text for seg in segments])
            return text
        except Exception as e:
            logger.ERROR("Error while generating the text from audio")
            raise e

    async def store_message_to_mongodb(self, output, answer):
        """give output from the"""
        try:
            msg_collection = self.client["message_turns"]
            subject = output.technical_subject + " " + output.technical_topic
            difficuilty = output.difficulty
            question = output.question

            data = {
                "session_id": ObjectId(self.session_id),
                "subject": subject,
                "difficulty": difficuilty,
                "Question": question,
                "Answer": answer,
            }
            session_data = await msg_collection.insert_one(data)
        except Exception as e:
            raise e

    async def get_list_of_messages(self):
        """Returns all the messages that are there for that perticular id."""
        try:
            msg_collection = self.client["message_turns"]
            list_messages = await msg_collection.find(
                {"session_id": self.session_id},
                {"session_id": 0, "timestamp": 0, "_id": 0},
            ).to_list()
            return list_messages
        except Exception as e:
            raise e

    async def get_audio_output(self, text):
        return await self.speech_model.generate_to_tensor(text)

    async def set_pdf_data_(
        self, req: Request, call_next, file_path: str
    ):  ## this will be one of the route.
        token = req.cookies.get("access_token")

        if not token:
            raise ValueError(401, "access token not found!")
        try:
            resume_data = await load_resume_data(file_path)
            if not resume_data:
                raise ValueError("problem to load data from the pdf")
            resume = self.client["resumes"]
            playload = jwt.decode(
                token,
                key=os.getenv("ACCESS_TOKEN_SECRET"),
                algorithms=os.getenv("ALGORITHMS"),
            )
            user_id = playload.get("_id")
            await resume.update_one(
                {"user_id": user_id},
                {
                    "$set": {"resume_summary": resume_data},
                },
                upsert=True,
            )  ## it will update if present if not present it will insert it.

        except Exception as e:
            logger.ERROR(f"error occured in the get pdf data {e}")
            raise HTTPException(501, "error to load pdf")

    async def set_resume_data(
        self, user_id
    ):  ## this be run inside the controller connection one.
        try:
            resume =  self.client["resumes"]
            resume_data = await resume.find_one({"user_id": ObjectId(user_id)})
            await self.rd.add_resume_data(
                self.session_id, resume_data["resume_summary"]
            )
            return resume_data["resume_summary"]
        except Exception as e:
            logger.ERROR("cannot able to puush the data")
            raise e

    async def get_resume_data(self):
        try:
            resume_data = await self.rd.get_resume_data(self.session_id)
            return resume_data

        except Exception as e:
            raise e

    async def get_question_list(self):
        return await self.rd.get_from_messagelist()

    async def add_to_summary(self, summary):
        return await self.rd.ADDsummary(
            session_id=self.session_id, summary_data=summary
        )

    async def get_summary(self):
        return await self.rd.get_from_Summarylist(self.session_id)

    async def add_question_list(self, message_turn):
        return await self.rd.addMessageTurnInqueue(
            session_id=self.session_id, messageObj=message_turn
        )

    async def generate_question(self, resume_data):
        try:
            if not resume_data:
                raise ValueError(f"cant be to get the resume data ")
            history_data = await self.rd.get_from_messagelist(
                session_id=self.session_id
            )
            summary = await self.rd.get_from_Summarylist(session_id=self.session_id)
            
            output =  self.model.invoke(
                {
                    "resume": resume_data,
                    "chat_history": history_data,
                    "summary": summary,
                }
            )
            self.count_message += 1
            return output
        except Exception as e:
            logger.ERROR(f"error occured during generating the question {e}")
            raise e

    async def generate_summry(self, list_):
        try:
            if not list_:
                raise ValueError("there is not data in the list")
            generated_summary = self.summary_model.invoke({"input": list_})
            return generated_summary
        except Exception as e:
            raise e

    async def remove_all_redis_data(self, session_id):
        if not session_id:
            raise ValueError("there is no session-id provided to expire the data")
        await self.rd.delete_all(session_id)
