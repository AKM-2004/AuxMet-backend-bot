from dotenv import load_dotenv  ## type:ignore
from langchain_core.prompts import ChatPromptTemplate  ## type:ignore
from langchain_groq import ChatGroq  ## type:ignore
from langchain.chains.combine_documents import create_stuff_documents_chain
from logs import ModuleLogger
from dataModels.QAModel import summarize_
import os
from prompts.prompts_ import summary_prompt

load_dotenv()
logger = ModuleLogger(app_name="summary_agent")
Hugging_face_api = os.getenv("HUGGINGFACE_API")
GroqApi = os.getenv("GROQ_API")
model_name = os.getenv("LLM_MODEL")


class summarize_agent:
    def __init__(self):
        self.__groq_api = GroqApi
        self.__hf_api = Hugging_face_api
        self.__model = model_name

    async def load_model(self):
        try:
            model = ChatGroq(api_key=self.__groq_api, model=self.__model)
            prompt = ChatPromptTemplate.from_template(summary_prompt)
            retriver_chain = (
                prompt | model
            )  ## making the basic chain because this type of arch can work in this normal chain
            logger.INFO("model loaded")
            return retriver_chain
        except Exception as e:
            logger.ERROR("can load the model")
            raise e
