# A quick warning
!! Classy is not finised yet so be careful using it !!


# classy
- Webserver (https://, http://)
- Json (WIP)
- Error handling (WIP)
- ***database intergation & mysql, postgres:***
	- *Async*
	- **AMRQ** *(Async Multiple Request Query)*
- Rate limiter
- Authentication
- Schema for JSON (Java Script Object Notation)
- XSS/CSP

## SSL Support
- Yes there is ssl support to use ssl you have to do this:
```python
from classy import server

start(use_ssl=True, keyfile="keyfile.pem", certfile="certfile.pem")
```
- You will need to generate 2 pem files using openssl.

## Create your own server!
- start a server:
```python
import os
import json
import asyncio
from aiohttp import web
import classy.server
import classy.database

config = {
    "host": "localhost",
    "port": 9880,
    "user": "root",
    "password": os.getenv("SQLpassword"),
    "database": "user"
}

Database = classy.database.Db(etype="mysql", config=config)

await Database.connect()

@classy.server.endpoint_GET("/api/user/{AnimalModelNumber:int}")
async def getuser_animalmodel(request: web.Request, AnimalModelNumber):
	query_string = "SELECT * FROM users WHERE ip_address = %s AND animal_number = %s"
    query_params = (request.remote, AnimalModelNumber)
    user_animal = await Database.query(query_string, params=query_params)
    return web.json_response(user_animal)


@classy.server.endpoint_POST("/api/user")
async def userget(request):
    headers = {
        "X-User": "User"
    }
    
    user_data = await Database.query(
        "SELECT * FROM users WHERE ip_address = %s;", 
        params=(request.remote,)
    )
    
    return web.Response(
        text=json.dumps(user_data),
        headers=headers,
        content_type="application/json"
    )

async def main():
    await Database.connect()
    classy.server.start(default_folder="public")

if __name__ == "__main__":
    asyncio.run(main())
```

## Server && Microservice communication with HTTP(S)
* use webresource function in classy.client:
```python
import classy.client

status, text = await classy.client.webresource("GET", "http://transcat.stripe-middle_end-server.local/current")

# ... Execute your business logic ...

# end
classy.client.close_webresource_pool()
```

## Authentication
```python
import classy

def auth_func(request):
	# ... code ...
	if authkeyValidated:
		return True # Let user pass
	return False # Block user

@server.endpoint_POST("/api/v3/user-authed")
@auth.require_auth(auth_func)
def userauthed(request):
	return web.Response(
		text="You shall pass!"
	)
``` 

## Input sanitization
```python
import classy
from aiohttp import web

def auth_func(request):
	# ... code ...
	if authkeyValidated:
		return True # Let user pass
	return False # Block user

@server.endpoint_POST("/api/v3/user-authed")
@auth.require_auth(auth_func)
@xss.preventv() # Sanatizes the body into request['sanitized_data'], adds XSS,CSP Headers automatically
def userauthed(request):
	return web.Response(
		text="You shall pass!"
	)
```

* the preventv decorator prevents any XSS injection attempts

## Database
* Example: Delete Alice user from MyApp_Db Database:
	```python
	import asyncio
	from classy.database import Db

	config = {
		"host": "localhost",
		"port": 9880,
		"user": "root",
		"password": "1234567890",
		"database": "MyApp_Db"
	}

	async def run():
		try:
			db = Db(etype="mysql", config=config)
			await db.connect()

			sql = "DELETE FROM users WHERE name = %s"
			target_user = ("Alice",)

			await db.query(sql, target_user, autocommit=True)
			print("User Alice successfully deleted.")

		except Exception as error:
			print(f"Framework Database Error during execution: {error}")
		finally:
			if 'db' in locals():
				await db.close()

	asyncio.run(run())
	```
	* Async code
	* Autocommiting and rollbacks
* Example: Use AMRQ:
	```python
	results = await db.query_amrq({
    	"users": "SELECT * FROM users",
    	"target_post": ("SELECT * FROM posts WHERE id = $1", (1,)),
    	"comments": ["SELECT * FROM comments"]
	})
	```
	* Get multiple results in one function!
	* result:
		```result
  		{
      		"users": [
				(1, "Alice"), 
				(2, "Bob")
			],
      		
			"target_post": [
				(1, "Hello World")
			],
      		
			"comments": [
				(1, "Nice post")
			]
  		}
		```

## Rate limiter

* The ratelimiter uses 'Cost Based Token Bucket RateLimiter' Method
* Use it via decorators:
```python
from classy.rate import rate_limit
from aiohttp import web
import asyncio

MAX_TOKENS = 150
MAX_REFILL_PERIOD = 10

@endpoint_GET("/api/make-system-status-report")
@rate_limit(MAX_TOKENS, MAX_REFILL_PERIOD, minus_token_amount=60)
async def make_system_report(request):
	# Do the report thing

	return web.Response(
		text=jsontext,
		content_type="application/json"
	)


asyncio.run(start())
```

## Schema
* Implementation for Schema:
```python
from classy.schema import Schema, validate_schema
from classy.server import endpoint_POST, start
from aiohttp import web

class Body(Schema):
	# ...

class Head(Schema):
	# ...

class Tail(Schema):
	# ...

class Hair(Schema):
	# ...

class Legs(Schema):
	# ...

class Model(Schema):
	Hasbody: bool
	Hashead: bool
	Hastail: bool
	Hashair: bool
	Haslegs: bool
	body: Body
	head: Head
	tail: Tail
	hair: Hair
	Legs: Legs

@endpoint_POST("/api/v2/save-animal-to-profile")
@validate_schema(Model)
def save_animal_to_profile(request: web.Request, model: Model):
	# Save to Database
	# ... code ...

	if success:
		return web.json_response({ "success": True })

	return web.json_response({ "success": False })
```

* Malformed JSON Requests can crash your server. So, you always need a Schema in the behind the scenes

# Questions

* 1. What is AMRQ?
	* => It is a feature in the database module of classy used to get multiple results at the same time

* 2. Why use classes for Db?
	* => We use classes for Db because instead of passing in multiple varibles for it to work, you dont even need to pass in the conn or cursor varibles. You just pass in the query!

* 3. Why do REST and Static file serving?
	* => We integrate REST and Static file serving because instead of choosing two Static file serving, and REST Frameworks and having to intertwine them you can just do them both

# Contributing
- Any contributions to this project are warmly welcomed
- Requirements:
	* No malware, trojans, ransomware etc... if we find malware in your code we will report your user.
	* No vulnerabilities, if we have found a vulnerability then we will deny the request immediatly!
	* Code quality: you must follow:
		- the DRY rule (Dont repeat youself)
	* Ai vibe code: ZERO, if we find vibe coded slop we will ****PERMENENTLY STOP TAKING REQUESTS FROM YOU****
	* If you pass all the above you can start forking and pull-requesting by next Week.

# Security
- WE TAKE SECURITY SEROUSLY HERE!!!!!!
- as mentioned before you must have not malware, vulnerabilities and ai coded vibe slop!!!