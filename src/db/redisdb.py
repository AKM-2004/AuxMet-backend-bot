from redis import Redis
from logs import ModuleLogger
import json

logger = ModuleLogger("redis_logs")


def connect_to_db():
    try:
        connection = Redis(host="localhost", port=6379, db=0, decode_responses=True)
        logger.INFO("REDIS DB IS CONNECTED SUCCESSFULLY!")
        return connection
    except Exception as e:
        print("there is error while connecting the redis.")
        logger.ERROR("there is an ERROR WHILE CONNECTING THE REDIS")
        raise e


# r = connect_to_db()
class redis_db:
    def __init__(self):
        self.r = connect_to_db()

    async def addMessageTurnInqueue(self, session_id, messageObj: dict):
        if not session_id:
            raise ValueError("sesionId is required")
        session_ID = "message" + str(session_id)
        try:
            messageObj = str(messageObj)
            self.r.lpush(session_ID, messageObj) ## i 
            self.r.ltrim(session_ID,0, 10)
            logger.INFO("item PUSHED in THE redis")
        except Exception as e:
            logger.ERROR("There is problem occur while inserting the data", e)
            raise e

    async def get_last_message(self, session_id):
        if not session_id:
            raise ValueError("here there should be the session id")
        session_ID = "message" + str(session_id)
        try:
            last_message = self.r.lrange(session_ID, -1)
            return last_message
        except Exception as e:
            raise e
            logger.ERROR("can't fetch the last message")

    async def get_from_messagelist(self, session_id):
        if not session_id:
            raise ValueError("sesionId is required")
        session_ID = "message" + str(session_id)
        try:
            list = self.r.lrange(session_ID, 0, -1)
            return list
        except Exception as e:
            raise e

    async def get_from_Summarylist(self, session_id):
        if not session_id:
            raise ValueError("sesionId is required")
        session_ID = "summary" + str(session_id)
        try:
            list = self.r.lrange(session_ID, 0, -1)
            return list
        except Exception as e:
            raise e

    async def ADDsummary(self, session_id, summary_data):
        if not (session_id and summary_data):
            raise ValueError("sesionId is required")
        session_ID = "summary" + str(session_id)
        try:
            self.r.rpush(session_ID, summary_data)
            self.r.ltrim(session_ID,-2, -1)
            logger.INFO("item PUSHED in THE redis")
        except Exception as e:
            logger.ERROR("There is problem occur while inserting the data", e)
            raise e

    async def session_hash_set(self, session_ID, data):
        if not (session_ID and data):
            raise ValueError("sesionId is required")

        try:
            self.r.hset(session_ID, data)
            logger.INFO("item PUSHED in THE redis")
        except Exception as e:
            logger.ERROR("There is problem occur while inserting the data", e)
            raise e

    async def session_hash_get(self, session_ID):
        if not (session_ID):
            raise ValueError("sesionId is required")

        try:
            item = self.r.hget(session_ID)
            logger.INFO("item get ")
            return item
        except Exception as e:
            logger.ERROR("There is problem occur while get the data", e)
            raise e

    async def add_resume_data(self, session_ID, data: dict):
        if not (session_ID and data):
            raise ValueError("sesionId is required")
        session_ID = "resume" + session_ID
        try:
            self.r.rpush(session_ID, data)
            self.r.ltrim(session_ID,-2, -1)
            logger.INFO("successfully inserted the message turn")
        except Exception as e:
            logger.ERROR("There is error while inserting into the wrong ans")
            raise e

    async def get_resume_data(self, session_ID):
        if not session_ID:
            raise ValueError("session_ID is required.")
        session_ID = "resume" + session_ID
        try:
            resume_data = self.r.lrange(session_ID, 0, -1)
            logger.INFO("sccessfully get the resume data")
            return resume_data
        except Exception as e:
            logger.ERROR("Error while feching the wrong ans")
            raise e

    async def delete_all(self, session_id):
        try:

            for key in self.r.scan_iter(f"*{session_id}*"):
                self.r.delete(key)
                print(key)  # for debugging

        except Exception as e:
            raise e

    async def expire_redis(self, session_id, time_out):
        try:
            self.r.expire(session_id, time_out)
        except Exception as e:
            raise e
