# A quick warning
!! Classy is not finised yet so be careful using it !!


# classy
- Webserver (https://, http://)
- Json (WIP)
- Error handling (WIP)
- ***database intergation & mysql, postgres:***
	- *Async*
	- **AMRQ** *(Async Multiple Request Query)*
- ... And more features that are coming sooner or later ...

## SSL Support
- Yes there is ssl support to use ssl you have to do this:
```python
from classy import server

start(use_ssl=True, keyfile="keyfile.pem", certfile="certfile.pem")
```
- You will need to generate 2 pem files using openssl.

## Use
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

## client && Microservice communication with HTTP(S)
* use webresource function in classy.client:
```python
import classy.client

status, text = await classy.client.webresource("GET", "http://transcat.stripe-middle_end-server.local/current")

# ... Execute your business logic ...

# end
classy.client.close_webresource_pool()
```

## Auth
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

## Input sanatiazation
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
@xss.preventv() # Sanatizes the body into request['sanitized_data']
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
	results = await db.query_amrq([
		[
			"SELECT * FROM users"
		],

		[
			"SELECT * FROM posts WHERE id = $1",
			(1,)
		],

		[
			"SELECT * FROM comments"
		]
	])
	```
	* Get multiple results in one function!
	* result:
		```result
		[
			[
				(1, "Alice"),
				(2, "Bob")
			],

			[
				(1, "Hello"),
				(2, "World")
			],

			[
				(1, "Nice post")
			]
		]
		```

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