import socketio as st
from logs import ModuleLogger
from app import app
from controllers.chat_controller import server_chat
from http.cookies import SimpleCookie
import jwt  ## change the JWT to jwt that is python pyjwt
import os
import asyncio
import numpy as np
from collections import defaultdict
sid_state = defaultdict(lambda: {"question":None , "answer": ""})
sid_locks = defaultdict(asyncio.Lock) 

origins = os.getenv("BOTAPP_ORIGINS")
if origins != "":
    allow_origins = origins.split(",")
else:
    allow_origins = "*"

logger = ModuleLogger("socket_conversation_route")
session_users = {}
sid_users = {}
sio = st.AsyncServer(async_mode="asgi", cors_allowed_origins="*",cookie=True)
# in the tts float 32 output
# stt can take in put of the nd array
""" 
On front-end side we will connect the socket like this :
const socket = io(proceess.env.BACKEND__BOT_URL, {
  path: "/websocket/conversation.io"
});

const socket = io("http://localhost:7576", {
  path: "/websocket/conversation"   //  must match socketio_path
});

"""
sio_app = st.ASGIApp(
    sio, other_asgi_app=app, socketio_path="/websocket/conversation"
)  # here we set the custome path for the sockets


""" 

Socket connection:

while connection create the session then in the connection take the information of the 
candiate from the resume and give it to the llm. 

--> LLm will generate its first response then after generating the first response it will 
    be passed to the TTS for text to audio conversion 
--> we will emit the Output_audio  of the client side we will have socket open as the 
    output_audio that will take the audio and will run that audio buffer after finishing
    the audio buffer we will record the audio and will transimit that audio in to the emit 
    input_audio 
--> after finishing that input_audio event we will have on the server side that will take the 
    audio and convert it into the text then it will emit the output_audio  

    like this cycle will be going on till my timer or the user will not end the session 


we will stream the audio for the output 

for input audio when speaker will start speaking at that time we will take 

the input for the next 


"""


## import the models in the app.py


@sio.event
async def connect(sid, environ,auth):
    """
    in connect we will take the resume data and then it into the redis resume array

    then we will check that the session_id we have take in the form of the cookie

    we are having an route that will run before the connection of the socket when user will create the
    and after the dissconnect we will have the same thing that it will remove that cookie

    then we will create the session

    after that we will see that if the redis_message_list is empty or not

    if not r.exists(key_name):
        gen_res = generate the first response from the llm and then will be passing it to the
    else:
        gen_res = if not empy last message we will take and we will send that message

    """
    # create the session: access the cookie

    try:
        cookie_header = environ.get("HTTP_COOKIE")
        if not cookie_header:
            logger.ERROR("cannot access the Cookies")
            raise ValueError("there is no http cookie")
        cookies = SimpleCookie()
        cookies.load(cookie_header)
        if "sessionToken" not in cookies:
            logger.error("cannot access the session")
            raise ValueError("cannot access the session")

        sessionToken = cookies["sessionToken"].value

        if not sessionToken:
            logger.ERROR("cannot access the AccessToken")
            raise ValueError("cannot access the accessToken")

        playload = jwt.decode(
            sessionToken,
            key=os.getenv("SESSION_TOKEN"),
            algorithms=os.getenv("ALGORITHMS"),
        )
        session_id = playload.get("session_id")
        user_id = playload.get("user_id")
        session_status = playload.get("status")

        # session_id = "68a8baed80c80cd3d91fd60d"
        # user_id = "68a5eaae47879054cc3b3a6e"
        # session_status = "active"
        if (
            session_id not in session_users
        ):  ## after user is disconnect then also it will work we can use this object in other functions also
            session_users[session_id] = server_chat(app)

        serverobj = session_users.get(session_id)
        # serverobj = server_chat()
        sid_users[sid] = serverobj  ## perticular sid ki server id.
        serverobj.session_id = session_id
        serverobj.session_status = session_status

        resume_data = await serverobj.set_resume_data(
            user_id
        )  ## we will have to use middle ware
        print(sid_users,session_users)
        generated_question = await serverobj.generate_question(resume_data)
        sid_state[sid]["question"] = generated_question
        print(generated_question.question)
        question = generated_question.question
        # generated_question -> tts then in raw form data will be send to the front-end
        generated_audio_array = await serverobj.get_audio_output(question)

        # to find that for how much time we audiolength will be
        # sr :- sample rate
        # array_of tensor
        # ausio in sec = array_of_tensor/sr
        print(generated_audio_array)
        sr = 24000
        for _,_,tensor in generated_audio_array:
            print(tensor)
            bytes_data = tensor.numpy().astype('float32').tobytes()
            audio_length = tensor.size()[0] / sr
            await sio.emit(
                "output_audio",
                {"sr": sr, "audio_array": bytes_data, "text": question, "length":audio_length },
                to=sid,
            )
            print("audio emmited")

    except Exception as e:

        await sio.emit("error", {"message": f"cannot connect due to {e}"})
        raise e

from collections import deque
audio_buffer = deque

async def convert_audio(audio_buffer):
    arr = await asyncio.to_thread(
        lambda: np.array(audio_buffer, dtype=np.int16).astype(np.float32) / 32768.0
    )
    return arr

@sio.event
async def input_audio(sid, data):
    try:
        serverobj = sid_users[sid]
        # serverobj = server_chat() for debug
        if not serverobj:
            raise ValueError("There is serverobj not there in the server")
        audio_buffer = data.get("audio_buffer")
        arr = await convert_audio(audio_buffer)
        # print ("this is the ",audio_buffer)
        if not data.get(
            "isFinal"
        ):  # isfinal = false we will loop till we will get the audio
    
            text_output = await serverobj.get_text_input(arr)
            print(text_output)
            if not sid_state[sid]["answer"]:
                sid_state[sid]["answer"] = ""
            sid_state[sid]["answer"] += text_output
            print(sid_state[sid]["answer"])
            

        else:
            # now we have to store the value inside the redis
            if  not sid_state[sid]["question"] and not sid_state[sid]["answer"]:
                raise ValueError("there not proper current_message")
            await serverobj.add_question_list(message_turn=sid_state[sid])
            print(sid_state[sid])
            storage_task = asyncio.create_task( serverobj.store_message_to_mongodb( # this will run in the background will not interupt to the socket 
                sid_state[sid]["question"],
                sid_state[sid]["answer"],
            ) )
            sid_state[sid] = {"question":None,"answer":""}

            if serverobj.count_message % 10 == 0:
                list_of_questions = serverobj.get_list_of_messages()
                summaray_ouput = await serverobj.generate_summry(list_of_questions)
                print(summaray_ouput)
                serverobj.add_to_summary(summaray_ouput)

            resume_data = await serverobj.get_resume_data()

            if not resume_data:
                raise ValueError("not able to fetch the resume data..")
            
            generated_question = await serverobj.generate_question(resume_data)
            sid_state[sid]["question"] =  generated_question
            question = generated_question.question
            # generated_question -> tts then in raw form data will be send to the front-end
            generated_audio_array = await serverobj.get_audio_output(question)

            # to find that for how much time we audiolength will be
            # sr :- sample rate
            # array_of tensor
            # ausio in sec = array_of_tensor/sr
            sr = 24000
            for i,(_,_,tensor) in enumerate(generated_audio_array):
                print(tensor)
                bytes_data = tensor.numpy().astype('float32').tobytes()
                audio_length = len(bytes_data)/sr
                await sio.emit(
                "output_audio",
                {"sr": sr, "audio_array": bytes_data, "text": question, "length":audio_length },
                to=sid,
            )
                print("audio emmited")

                await asyncio.sleep(0.01)
            # redis and after every 10 count generate the summary
            #  put in the redis and also give the ouput/generate the text
            # and make ouput and then make a route for dissconnect and of both
    except Exception as e:
        await sio.emit(
            "error",
            {"message": f"there is an error while sending the output error is; {e}"},
        )
        raise e 


@sio.event
async def disconnect(sid, environ):
    # remove thesid from the sid_users
    if sid in sid_users:
        sid_users.pop(sid)
        
    print(f"client dissconnected: {sid} and {sid_users}")

    #  from front end at every 5 sec till the user is taking that data will stream
    # but if at every 5 second we will get the data then it will run the whole thing
    # what to do about that then
    # need to rewrite the whole session let's see it will work we will do some modify
    # in create session

    """ 
    before writing the any function plese re write the routes like we are fetching the session and other things 
    every time when we are generating the question that is not good sign so replace it      
    """
