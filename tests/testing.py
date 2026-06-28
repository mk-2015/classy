from aiohttp import web
from classy import server, schema, database, auth, rate
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict
from random import SystemRandom

ROOT = Path("./root").resolve()
db = database.Db(
    connection_string="./database.db"
)
db.connect()

randobj = SystemRandom() 

tokens: List[Dict[str, str]] = []

@server.endpoint_POST("/v1/api/useradd/{name:str}/{password:str}")
async def useradd(request: web.Request, *args, **kwargs):
    name = kwargs["name"]
    password = kwargs["password"]

    if len(name) < 4:
        return web.Response(
            status=400,
            text="400 Bad Request: Username too short."
        )
    elif len(password) < 7:
        return web.Response(
            status=400,
            text="400 Bad Request: Password too short."
        )
    
    table_schema = """
    CREATE TABLE IF NOT EXISTS accounts (
        user VARCHAR(255) PRIMARY KEY,
        password VARCHAR(255) NOT NULL
    );
    """
    await db.query(table_schema) 

    insert_sql = "INSERT INTO accounts (user, password) VALUES (%s, %s)"
    params = (name, password)

    await db.query(insert_sql, params, autocommit=True)

    return web.Response(
        status=201,
        text=f"201 Created: Added user {name}."
    )

@server.endpoint_POST("/v1/api/login/{user:str}")
async def login(request: web.Request, *args, **kwargs): 
    passw = request.headers.get("Password")

    if not passw or not user:
        return web.Response(
            status=401,
            text="401 Unauthorized: No password or no entered user"
        )
    
    if len(passw) < 7 or len(user) < 4:
        return web.Response(
            status=400,
            text="400 Invalid Inputs: Username or password is too short"
        )

    user_record = await db.query(
        "SELECT password FROM accounts WHERE user = %s", 
        (user,), 
        fetch_all=False
    )

    if not user_record:
        return web.Response(status=401, text="401 Unauthorized: User does not exist")

    stored_password = user_record.get("password")
    
    if passw != stored_password:
        return web.Response(status=401, text="401 Unauthorized: Invalid password")

    for token in tokens:
        if user in token:
            return web.json_response(
                status=200,
                data={
                    "status": "Logged in (Existing Session)",
                    "key": token[user]
                }
            )

    rj_bytes = randobj.randbytes(16)
    rj_hex = rj_bytes.hex()  

    tokens.append({
        user: rj_hex
    })

    return web.json_response(
        status=200,
        data={
            "status": "Logged in",
            "key": rj_hex
        }
    )