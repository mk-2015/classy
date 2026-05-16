# A quick warning
!! Classy is not finised yet so be careful using it !!


# classy
- Webserver (https://, http://)
- Json (WIP)
- Error handling (WIP)
- database intergation & mysql, postgres:
	* Async
	* AMRQ (Async Multiple Request Query)
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
from aiohttp import web
import classy 

config = {
    "host": "localhost",
    "port": 9880,
    "user": "root",
    "password": os.getenv("SQLpassword"),
    "database": "user"
}

Database = classy.Db(etype="mysql", config=config)

async def init_app():
    await Database.connect()
    app = web.Application()
    return app

@server.endpoint_POST("/api/user")
async def userget(request):
    headers = {
        "X-User": "User"
    }
    
    user_data = await Database.query(
        "SELECT * FROM users WHERE ip_address = ?;", 
        params=(request.remote,)
    )
    
    return web.Response(
        text=json.dumps(user_data),
        headers=headers,
        content_type="application/json"
    )

if __name__ == "__main__":
    start(default_folder="public")
```

## client && Microservice communication with HTTP(S)
* use webresource function in classy.client:
```python
import classy

status, text = classy.client.webresource("GET", "http://transcat.stripe-middle_end-server.local/current")

# ... Code ...

# at the end
classy.client.close_webresource_pool()
Db.close()
```

## Database
* Example: Delete Alice user from MyApp_Db Database:
	```python
	from classy.database import Db

	config = {
		"host": "localhost",
		"port": 9880,
		"user": "root",
		"password": "1234567890",
		"database": "MyApp_Db"
	}

	try:
		db = Db(
			etype="mysql",
			config=config
		)

		await db.connect()

		sql = "DELETE FROM users WHERE name = %s"

		target_user = ("Alice",)

		await db.query(
			sql,
			target_user,
			autocommit=True
		)
		print("User Alice successfully deleted.")

	except Exception as error:
		print(f"Framework Database Error, during execution: {error}")
	finally:
		if 'db' in locals():
			await db.close()
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