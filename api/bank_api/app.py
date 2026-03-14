from fastapi import FastAPI, HTTPException
from typing import Optional

from fastapi.middleware.cors import CORSMiddleware
import httpx
from datetime import datetime as dt
import json



app = FastAPI()



app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
