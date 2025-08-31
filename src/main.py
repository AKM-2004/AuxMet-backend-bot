import uvicorn
from router.conversation_socket import sio_app
from dotenv import load_dotenv
from logs import ModuleLogger
import asyncio
# import warnings
# warnings.filterwarnings("ignore", category=UserWarning)
# warnings.filterwarnings("ignore", category=FutureWarning)


logger = ModuleLogger("mongoDbConnection")
load_dotenv()



if __name__ == "__main__":
    uvicorn.run("router.conversation_socket:sio_app",host="0.0.0.0" ,port=7576,reload=True)
    print("Server is started at 7576")
    logger.INFO("Connected successfully")

