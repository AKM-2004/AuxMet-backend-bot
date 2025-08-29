import asyncio
from logs import ModuleLogger
from faster_whisper import WhisperModel, BatchedInferencePipeline
import torch
from logs import ModuleLogger
from fastapi import HTTPException

logger = ModuleLogger("Audio_to_text")


class SpeechToText:
    def __init__(self):
        self.__initialize = False
        self.__model = "large-v3"
        self.__compute_type = "int8"  # quantizezd model
        self.__device = "cuda" if torch.cuda.is_available() else "cpu"
        self.__pipeline = None
        self.__language = "en"
        self.__batch_size = 4
        self.vad_filter = (True,)
        self.vad_parameters = {
            "threshold": 0.3,  # it will be ok for low noises
            "min_speech_duration_ms": 150,
            "min_silence_duration_ms": 1000,
        }

    async def load_model_initialize_pipeline(self):
        if self.__initialize:
            return
        try:
            model = WhisperModel(
                model_size_or_path=self.__model,
                device=self.__device,
                compute_type=self.__compute_type,
            )
            self.__pipeline = BatchedInferencePipeline(model=model)
            self.__initialize = True
            logger.INFO("Model initialize")
        except Exception as e:
            logger.ERROR(f"Fail to load : {e}")
            raise e

    async def genererate_text(self, input):
        if not self.__initialize:
            logger.ERROR("there is problem in ASR Model check that.")
            raise ValueError("Model is not initialize")
        try:
            segments, _ = self.__pipeline.transcribe(
                input,
                language=self.__language,
                batch_size=8,
                vad_filter=self.vad_filter,
                vad_parameters=self.vad_parameters,
                word_timestamps = True
            )
            logger.INFO("Model initialize")
            return segments
        except Exception as e:
            logger.ERROR(f"there is problem in transcribeing : {e}")
            raise e
