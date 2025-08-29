from db.mongodbconnection import get_mongodb_client
from bson import ObjectId
import jwt
from fastapi import HTTPException, Request
import os


async def verifySession(req: Request):
    client = get_mongodb_client()
    db_ = client["auxmet_db"]
    session = db_["sessions"]
    try:
        session_token = req.cookies.get("sessionToken")

        if not session_token:
            raise HTTPException(401, "no sessionToken Found!")

        playload = jwt.decode(
            session_token, os.getenv("SESSION_TOKEN"), os.getenv("ALGORITHMS")
        )

        if not playload:
            raise HTTPException(401, "There is no data store in the session playload")

        session_id = playload.get("session_id")

        session_data = await session.find_one({"_id": ObjectId(session_id)})
        # print(session_data)
        req.state.session_data = session_data
    except Exception as e :
        raise HTTPException(401, f"There is no data store in the session playload {e}")
    # after this
