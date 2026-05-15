import sqlite3 as sqlite
import os

def db_init(sqltype="sqlite", dbpath="./database.db"):
    if not os.path.isfile(dbpath) and sqltype == "sqlite":
       raise FileNotFoundError(f"Database file: {dbpath} not found.")
    
    if sqltype == "sqlite":
        connection = sqlite.connect(dbpath)
        cursor = connection.cursor()
        
        sqlobject = {
            "type": sqltype,
            "db-path": dbpath,
            "local": 
            {
                "connection": connection,
                "cursor": cursor
            }
        }
        
        return sqlobject
    else:
        return { "error": True } 
        
def db_execute(sqlobj, execstring, params=None, force=0):
    if sqlobj.get('type') == "sqlite":
        if params is not None:
            data = sqlobj['local']['cursor'].execute(execstring, params).fetchall()
        else:
            data = sqlobj['local']['cursor'].execute(execstring).fetchall()
            
        if force == 1: 
            sqlobj['local']['connection'].commit()
        return data
    
    return { "error": True }

def db_commit(sqlobj, name="test", commitname="Update Database"):
    print(f"{name} has commited to {sqlobj['type']} with commit being: {commitname}")
    if sqlobj['type'] == "sqlite":
        sqlobj['local']['connection'].commit()

def db_close(sqlobj):
    if sqlobj['type'] == "sqlite":
        sqlobj['local']['connection'].commit()
        sqlobj['local']['connection'].close()
        sqlobj.clear()
    return { "error": True }