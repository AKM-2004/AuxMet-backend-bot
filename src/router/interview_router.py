from fastapi import APIRouter, Request, Response, Depends, UploadFile, File
from fastapi.responses import JSONResponse
from fastapi import HTTPException
from logs import ModuleLogger
from db.mongodbconnection import get_mongodb_client
from bson import ObjectId
from middleware.auth_middleware import verifyJWThttp
from middleware.verify_session import verifySession
import jwt
from datetime import datetime,timezone
import os
from db.redisdb import redis_db

logger = ModuleLogger("chat_route")
router = APIRouter(prefix="/api/v1/interview")
rdb = redis_db()

# handle the pdf file and store that pdf data into the mongodb.


@router.post("/interview-session")
async def interview_session(
    req: Request, res: Response, _: None = Depends(verifyJWThttp)
):
    try:
        user = req.state.user
        body = await req.json()

        interview_name = body.get("interviewName")
        print(user)
        if not user:
            raise HTTPException(401, "cannot get the data ")
        
        user_id = user.get("_id")
        print(user_id)
        client = get_mongodb_client()
        db = client["auxmet_db"]
        session = db["sessions"]
        session_status = "active"
        resume_collec = db["resumes"]
        resume_data =  await resume_collec.find_one({"user_id": ObjectId(user_id)})

        if not resume_data:
            raise HTTPException(401, "Resume not found of the user")

        resume_id = resume_data.get("_id")
        
        data = {
    "user_id": ObjectId(user_id),
    "interviewName": interview_name,
    "resume": ObjectId(resume_id),
    "status": session_status,
    "createdAt": datetime.now(tz=timezone.utc),
    "updatedAt": datetime.now(tz=timezone.utc)
        }


        session_data = await session.insert_one(data)  # inserted the new session

        print(session_data.inserted_id)
        playload = {
            "session_id": str(session_data.inserted_id),
            "user_id": str(user_id),
            "status": session_status,  # Token will expire in 2 hrs
        }
        token = jwt.encode(
            payload=playload,
            key=os.getenv("SESSION_TOKEN"),
            algorithm=os.getenv("ALGORITHMS"),
        )
        
        res =  JSONResponse({
            "session_id": str(session_data.inserted_id),
                "user_id": str(user_id),
                "Status": "active",
                "interviewName": interview_name,
           
        }, 201)

        res.set_cookie(key="sessionToken", value=token, secure=True, httponly=True,max_age=7200) 
        # set cookies set the cookie in the response header so it need to

        return res # if you want to pass the cookie you will need to return the response then only it will be actually send 
    
    except Exception as e:
        raise HTTPException(500, f"cannot create the Inverview session : {e}")


# when to run the upload file
from utils.tools import load_resume_data


@router.post("/upload-file")
async def upload_file(
    req: Request, _: None = Depends(verifyJWThttp), PdfFile: UploadFile = File(...)
):
    try:
        user = req.state.user
        user_id = user.get("_id")

        if not user_id:
            raise HTTPException(404, "User not found")
        # temporary file path that is handle by the fast api here we need not to use the middle ware like multer that we do in the Express
        # files are handle internally by the fast api
        # this temp file is here till this request is getting executed
        temp_file_bytes =  await PdfFile.read()

        resume_data = await load_resume_data(temp_file_bytes)
        print(resume_data)

        if not resume_data:
            raise HTTPException(401, "resume data is empty")
        client = get_mongodb_client()
        db = client["auxmet_db"]
        resume = db["resumes"]
        resume_data = await resume.update_one(
            {"user_id": ObjectId(user_id)
            },
            {
                "$set": {"resume_summary": resume_data},
        
            },
            upsert=True,
        )
        return JSONResponse("resume uploaded.",201)

    except Exception as e:
        logger.ERROR(f"error occur in the api/upload-file {e}")
        raise HTTPException(401, f"Cannot able to upload file due to {e} ")


#  route for the deleteing the session_id,deleteing the redis db all data
@router.post("/end_session")
async def endSession(req: Request, res: Response, _: None = Depends(verifySession)):
    try:
        from router.conversation_socket import session_users

        session_data = req.state.session_data
        print(session_users)
        print(session_data)
        if not session_data:
            raise HTTPException(401, "session_data is empty in the route.")
        session_id = session_data.get("_id")  # from here we will get the session_id.
        #  delete all the redis data.
        print(session_data)
        await rdb.delete_all(session_id=str(session_id))

        # now change the state an in the db and remove the id from the session users dict
        client = get_mongodb_client()
        db = client["auxmet_db"]
        session_ = db["sessions"]
        session_status = "Deactivate"
        ers = await session_.find_one_and_update(
            {"_id": ObjectId(session_id)},
            {"$set": {"status": session_status}},
        )
            
        
        if session_id in session_users:
            session_users.pop(session_id)

        res = JSONResponse(
            content={"message": "Session ended successfully", "session_id": str(session_id)}, 
            status_code=200  # Changed from 201 to 200
        )

        res.delete_cookie(
            "sessionToken",           
            secure=True,        
            httponly=True,            
        )
        return res
    except Exception as e:
        raise HTTPException(401, f"Not able to disconnect the session: {e}")


# route for the result generation generating it and storing it into the mongodb
# route for link generation string


@router.post("/result/generation")
async def result_generation(
    req: Request, res: Response, _: None = Depends(verifySession)
):  
    client = get_mongodb_client()
    try:
        from models.validate_agent import validation_agent
        validate_model = await validation_agent().load_model()
        
        session_data = req.state.session_data 
        if not session_data:
            raise HTTPException(401, "cannot get the value ")
        session_id = session_data.get("_id")
        print(session_id)
        db = client["auxmet_db"]
        messages_db = db["message_turns"]
        conversation_list = await messages_db.find({"session_id": ObjectId(session_id)},{"_id":0,"session_id":0,"subject":0,"difficulty":0}).to_list()
        print(conversation_list)
        if not conversation_list:
            raise HTTPException(401, f"Conversation data not found!, {conversation_list}")
        
        generated_results = await validate_model.ainvoke({"context": conversation_list})
        print(generated_results)
        db = client["auxmet_db"]
        result_db = db["results"]

        Result = await result_db.insert_one(
            {
                "session_id": ObjectId(session_id),
                "user_id": session_data.get("user_id"),
                "technical_skill_score": generated_results.average_technical_skills_score,
                "domain_specific_score": generated_results.domain_specific_technical_knowledge_score,
                "communication_skills_score": generated_results.communication_skills_score,
                "questions_understanding_score": generated_results.question_understanding_score,
                "problem_solving_score": generated_results.problem_solving_approach_score,
                "DepthOfKnowlege_score": generated_results.depth_of_knowledge_score,
                "createdAt": datetime.now(tz=timezone.utc),
                "updatedAt": datetime.now(tz=timezone.utc)
            }
        )

        return JSONResponse({"message":"successful" }, 201)

    except Exception as e:
        raise HTTPException(501, f"cannot generate the result {e}")

from models.validate_agent import Wrong_validate
from utils.tools import give_links

@router.post("/result/generate_refrences")
async def generate_wrong_questions_referenceses(
    req: Request, res: Response, _: None = Depends(verifySession)
):

    try:
        topics_model = await Wrong_validate().load_model()

        session_data = req.state.session_data

        if not session_data:
            raise ValueError("can't fetch the session_data")

        session_id = session_data.get("_id")
        user_id = session_data.get("user_id")
        client = get_mongodb_client()

        db = client["auxmet_db"]
        messages_db = db["message_turns"]
        conversation_list = await messages_db.find({"session_id": ObjectId(session_id)}).to_list(length=None)
          ## from here we will get al the messages
        if not conversation_list:
            raise HTTPException(404, "Conversation data not found!")

        response = topics_model.invoke({"input": conversation_list})
        print(response)
        qa = response.wrong_qa
        links_data = await give_links(qa)

        # store it

        wqa_db = db["refrencelinks"]
        refrence_links = await wqa_db.insert_one(
            {"session_id": ObjectId(session_id), "user_id": ObjectId(user_id), "refrenceLinks": links_data}
        )

        return JSONResponse(
    content={"message": "Reference links generated successfully", "session_id": str(session_id)}, 
    status_code=201)

    except Exception as e:
        raise HTTPException(501, f"Cannot generate the Links! {e}")
