from dotenv import load_dotenv  ## type:ignore
from langchain_core.prompts import ChatPromptTemplate  ## type:ignore
from langchain_groq import ChatGroq  ## type:ignore
from langchain.chains.combine_documents import create_stuff_documents_chain
from logs import ModuleLogger
from dataModels.QAModel import validation_output, OutputParse
from langchain.agents import create_tool_calling_agent, AgentExecutor
import os
import asyncio
from prompts.prompts_ import validate_prompt, wrong_validate_prompt


load_dotenv()
logger = ModuleLogger(app_name="Validate_agent")
Hugging_face_api = os.getenv("HUGGINGFACE_API")
GroqApi = os.getenv("GROQ_API")
model_name = os.getenv("LLM_MODEL")


class validation_agent:
    def __init__(self):
        self.__groq_api = GroqApi
        self.__hf_api = Hugging_face_api
        self.__model = "meta-llama/llama-4-maverick-17b-128e-instruct"

    async def load_model(self):
        try:
            model = ChatGroq(api_key=self.__groq_api, model=self.__model)
            prompt = ChatPromptTemplate.from_template(validate_prompt)
            model_ = model.with_structured_output(validation_output)
            chain = (
                prompt | model_
            )  ## we will use simple chain not need of any fancy thing
            logger.INFO("model loaded")
            return chain

        except:
            logger.ERROR("can load the model")
            raise


# not using any agent or fancy chain because for this process till now
# this both the simple agents are working good and i think i not need any custome agent still now
# until an unless i required a tool call
#
# in future version we will use feedback tool and then we will using the langgraph agent
class Wrong_validate:
    def __init__(self):
        self.__groq_api = GroqApi
        self.__hf_api = Hugging_face_api
        self.__model = "meta-llama/llama-4-maverick-17b-128e-instruct"  # this is different specific model

    async def load_model(self):
        try:
            model = ChatGroq(api_key=self.__groq_api, model=self.__model)
            prompt = ChatPromptTemplate.from_template(wrong_validate_prompt)
            model_ = model.with_structured_output(OutputParse)
            chain = prompt | model_  ## this chain will save the inference time
            logger.INFO("model loaded")
            return chain

        except Exception as e:
            logger.ERROR(f"can load the model : {e}")
            raise e
