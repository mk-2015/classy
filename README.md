# A quick warning
!! Classy is not finised yet so be careful using it !!


# classy
- Webserver (https://, http://)
- Json (WIP)
- Error handling (WIP)
- database intergation & mysql, postgres
- ... And more features that are coming sooner or later ...

## SSL Support
- Yes there is ssl support to use ssl you have to do this:
```python
from classy import server

start(use_ssl=True, keyfile="keyfile.pem", certfile="certfile.pem")
```
- You will need to generate 2 pem files using openssl.

## Database
```python
from classy import database

config = {
    "host": "localhost",
    "user": "root",
    "password": "your_secure_password",
    "database": "your_application_db"
}

try:
    db = Db(etype="mysql", config=config)
    sql = "DELETE FROM USERS WHERE name = %s"
    target_user = ("Alice",)
    db.query(sql, target_user)
    db.commit()
    print("User Alice successfully deleted.")
except Exception as error:
    print(f"Framework Database Error during execution: {error}")
finally:
    if 'db' in locals():
        db.close()

```

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