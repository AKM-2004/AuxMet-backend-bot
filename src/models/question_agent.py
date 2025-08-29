from dotenv import load_dotenv  ## type:ignore
from langchain_core.prompts import ChatPromptTemplate  ## type:ignore
from langchain_text_splitters import RecursiveCharacterTextSplitter  ## type:ignore
from langchain_groq import ChatGroq  ## type:ignore
from langchain_huggingface.embeddings import HuggingFaceEmbeddings
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.runnables import RunnableWithMessageHistory
from prompts.prompts_ import question_answer_prompt
from langchain.chains.combine_documents import create_stuff_documents_chain
from logs import ModuleLogger
from dataModels.QAModel import Output_
import os
import asyncio

load_dotenv()
logger = ModuleLogger(app_name="question_answer")
Hugging_face_api = os.getenv("HUGGINGFACE_API")
GroqApi = os.getenv("GROQ_API")
model_name = os.getenv("LLM_MODEL")


class Question_Agent:
    def __init__(self):
        self.__groq_api = GroqApi
        self.__hf_api = Hugging_face_api
        self.__chunk_size = 838
        self.__chunk_overlap = 140
        self.__model = model_name

    # In version 2 we will add here search retrivel for seraching the most asked interview question
    # related to the

    async def load_model(self):
        try:
            model = ChatGroq(api_key=self.__groq_api, model=self.__model)
            prompt = ChatPromptTemplate.from_template(question_answer_prompt)
            model_ = model.with_structured_output(Output_)
            retriver_chain = prompt | model_
            logger.INFO("model loaded")
            return retriver_chain  ## input mai summary, history, resume

        except Exception as e:
            logger.ERROR(f"can load the model: {e}")
            raise e
