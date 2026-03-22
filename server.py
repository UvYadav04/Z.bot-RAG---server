from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uuid
from contextlib import asynccontextmanager
from routes.user import router as user_router
from routes.chat import router as chat_router
from routes.document import router as document_router
from MongoDB.db import connect_db
import uuid
from fastapi import Request
from fastapi.middleware.cors import CORSMiddleware
import os
import jwt
from dotenv import load_dotenv
from starlette.middleware.sessions import SessionMiddleware
import uuid
from mangum import Mangum
load_dotenv()

# sessions = {}


# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     from Model.load_model import get_model
#     app.state.sessions = {}
#     # model, tokenizer = get_model()
#     # app.state.model = model
#     # app.state.tokenizer = tokenizer
#     # client = get_model()
#     # app.state.client = client

#     # client = connect_db()
#     # if client is not None:
#     #     app.state.mongo_client = client
#         # app.state.zensky_db = client["ZenskyDatabase"]

#     # from Qdrant.db import instantiate_chroma

#     # qdrant_client = instantiate_chroma()
#     # app.state.qdrant_client = qdrant_client


#     yield
#     print("Server shutting down...")
@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.sessions = {}
    yield
    print("Server shutting down...")


origins_allowed = ["http://16.170.228.133/"]

# if type(origins_allowed) == list:
#     origins = origins_allowed.split(',')
# else:
origins = origins_allowed

app = FastAPI(title="Basic FastAPI Server", version="1.0", lifespan=lifespan)

handler = Mangum(app)

app.add_middleware(SessionMiddleware, secret_key=os.environ.get("SESSION_SECRET"))

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # allowed origins
    allow_credentials=True,  # allow cookies, auth headers
    allow_methods=["*"],  # allow all HTTP methods
    allow_headers=["*"],  # allow all headers
)

@app.middleware("http")
async def authenticate(request: Request, call_next):
    try:
        print("cookies : ",request.cookies)
        auth_token = request.cookies.get("zensky-jwt-token")
        session_id = request.cookies.get("session_id")
        session = app.state.sessions.get(session_id)
        user_id = None
        if auth_token:
            try:
                payload = jwt.decode(auth_token, os.environ["JWT_SECRET"],algorithms=["HS256"])
                user_id = payload.get("user_id")
            except jwt.InvalidTokenError as e:
                print(e)
                pass

        if not session:
            session_id = str(uuid.uuid4())
            new_chat_id = str(uuid.uuid4())
            session = {
                "session_id": session_id,
                "messages": [],
                "request_count": 1,
                "user_id": user_id,
                "current_chat_id":new_chat_id
            }
            app.state.sessions[session_id] = session
            request.state.session_id = session_id
            request.state.session = session
            request.state.user_id = user_id
            response = await call_next(request)
            response.set_cookie(
                key="session_id",
                value=session_id,
                httponly=True,
                samesite="none",
                expires=60 * 60 * 24,
                secure=True,
                path='/'
            )
        else:
            session["request_count"] += 1
            if "user_id" not in session and user_id is not None:
                session["user_id"] = user_id
            if "current_chat_id" not in session:
                session["current_chat_id"] = str(uuid.uuid4())
            request.state.session_id = session_id
            request.state.user_id = user_id
            request.state.session = session
            response = await call_next(request)

        return response
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": f"An error occurred during authentication: {str(e)}",
            },
        )


@app.get("/debug")
async def debug(request: Request):
    return request.cookies


app.include_router(chat_router)
app.include_router(document_router)
app.include_router(user_router)


@app.get("/{full_path:path}")
async def catch_all(full_path: str):
    return {"message": "Route not found", "path": full_path}
