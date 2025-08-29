from db.mongodbconnection import get_mongodb_client
from bson import ObjectId
import jwt
from fastapi import HTTPException, Request
from dotenv import load_dotenv
import os

load_dotenv()


async def verifyJWThttp(req: Request):
    token = req.cookies.get("accessToken")
    client = get_mongodb_client()
    Client = client["auxmet_db"]
    if not token:
        raise HTTPException(401, "no verification token")

    try:

        decode_token = jwt.decode(
            token,
            key=os.getenv("ACCESS_TOKEN_SECRET"),
            algorithms=os.getenv("ALGORITHMS"),
        )
        if not decode_token:
            raise HTTPException(401, "cannot find the cookie")
        print(decode_token.get("_id"))
        User = Client["users"]
        user = await User.find_one(
            {"_id": ObjectId(decode_token.get("_id"))}, {"password": 0, "RefreshToken": 0}
        )
        print(user)
        if not user:
            raise HTTPException(401, "Usernot found in the db")

        req.state.user = user
    except Exception as e:
        raise HTTPException(401, f"User not found:{e}")
