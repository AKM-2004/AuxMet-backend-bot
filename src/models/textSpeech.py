from kokoro import KModel, KPipeline
import torch
from IPython.display import display, Audio
import soundfile as sf
from logs import ModuleLogger
import asyncio

logger = ModuleLogger("TexttoSpeech")


class TextToSpeech_:
    def __init__(self):
        self.__langauge_code = "a"
        self.__device = "cuda" if torch.cuda.is_available() else "cpu"
        self.__voice = "af_heart"
        self.__speed = 0.9
        self._initlalized = False
        self.pipeline = None

    async def load_model(self):
        if self._initlalized:
            return True
        try:
            self.pipeline = KPipeline(repo_id="hexgrad/Kokoro-82M",
                lang_code=self.__langauge_code, device=self.__device
            )
            self._initlalized = True
            return self._initlalized
        except Exception as e:
            logger.ERROR(f"there is Problem in Text To speech:{e}")
            raise e

        # return pipeline ## we will stream this using the socket and will stream

    async def generate_to_tensor(self, text: str):
        if not self._initlalized:
            logger.ERROR("PipeLine is not initialized ")
            ValueError("No pipeline is initialized.")

        try:
            generator = self.pipeline(text, voice=self.__voice, speed=self.__speed)
            # for _, _, audio in generator:
            #     yield audio
            return generator
            logger.INFO("Generated the text")
        except Exception as e:
            logger.ERROR(f"There is some problem with the generator: {e} ")
            raise e
        # make this when you will write the fast api socket routes
