from fastapi import APIRouter
from utils.safeExecution import safeExecution
from fastapi.requests import Request
from fastapi.responses import Response
import jwt
import os
from bson import ObjectId
from datetime import datetime, timedelta
from dotenv import load_dotenv
from fastapi.responses import JSONResponse
from startupFunctions import get_mongo

import logging

logger = logging.getLogger("user_routes")
logging.basicConfig(level=logging.INFO)

load_dotenv()

router = APIRouter()



@router.get("/user/userInfo")
@safeExecution
async def getUserInfo(request: Request, response: Response):

    user_id = getattr(request.state, "user_id", None)

    logger.info(f"Fetching user info | user_id={user_id}")

    if hasattr(request.app.state, "zensky_db"):
        db = get_mongo(request.app)
    else:
        logger.error("MongoDB not initialized (zensky_db missing)")
        return {"success": False, "message": "cant get user Info at the moment"}

    user_col = db["Users"]

    if user_col is None:
        logger.error("Users collection not found")
        return {"success": False, "message": "cant get user info at the moment"}

    if user_id is not None:
        try:
            user_info = user_col.find_one({"_id": ObjectId(user_id)})

            if user_info:
                user_info["_id"] = str(user_info["_id"])
                logger.info("User found")
            else:
                logger.warning("User not found in DB")

            return {"success": True, "info": user_info}

        except Exception as e:
            logger.exception(f"Error fetching user info: {str(e)}")
            return {"success": False, "info": None}

    logger.warning("No user_id in request.state")
    return {"success": False, "info": None}


@router.post("/user/login")
@safeExecution
async def login(request: Request, response: Response):

    body = await request.json()
    email = body["email"]
    name = body["name"]

    logger.info(f"Login attempt | email={email}")

    if hasattr(request.app.state, "zensky_db"):
        db = get_mongo(request.app)
    else:
        logger.error("MongoDB not initialized")
        return {"success": False, "message": "cant login at the moment"}

    user_col = db["Users"]

    if user_col is None:
        logger.error("Users collection not found")
        return {"success": False, "message": "cant login at the moment"}

    user_info = user_col.find_one({"email": email})

    if not user_info:
        logger.info("Creating new user")

        new_user = {"name": name, "email": email}
        result = user_col.insert_one(new_user)
        user_info = user_col.find_one({"_id": result.inserted_id})
    else:
        logger.info("Existing user found")

    payload = {
        "user_id": str(user_info["_id"]),
        "username": name,
        "exp": datetime.utcnow() + timedelta(days=7),
    }

    jwtToken = jwt.encode(payload, os.environ["JWT_SECRET"], algorithm="HS256")

    current_chat_id = getattr(request.state, "current_chat_id", None)

    logger.info(f"Login success | user_id={user_info['_id']}")

    response = JSONResponse(
        {
            "success": True,
            "user": {
                "id": str(user_info["_id"]),
                "name": user_info["name"],
                "email": user_info["email"],
            },
            "new_chat_id": current_chat_id,
        }
    )

    logger.info("Setting JWT cookie & deleting session cookie")

    response.set_cookie(
        key="zensky-jwt-token",
        value=jwtToken,
        httponly=True,
        sameSite="none",
        secure=True,
        max_age=60 * 60 * 24 * 7,
        path="/",
    )

    response.delete_cookie(
        key="session_id",
        path="/",
        sameSite="none",
        secure=True,
        httponly=True,
    )

    return response

@router.post("/user/logout")
@safeExecution
async def logout(request: Request, response: Response):

    logger.info("User logout")

    response.delete_cookie(
        key="zensky-jwt-token",
        path="/",
        sameSite="none",
        secure=True,
        httponly=True,
    )

    response.delete_cookie(
        key="session_id",
        path="/",
        sameSite="none",
        secure=True,
        httponly=True,
    )

    return {"success": True}