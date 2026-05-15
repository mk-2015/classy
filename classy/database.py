import os

class Db:
    def __init__(self, etype="sqlite", connection_string=None, config=None):
        self.etype = etype.lower()
        self.conn = None
        self.cursor = None
        
        if self.etype == "sqlite":
            import sqlite3
            if connection_string and not os.path.isfile(connection_string):
                raise FileNotFoundError(f"SQLite file not found: {connection_string}")
            self.conn = sqlite3.connect(connection_string or ":memory:")
            
        elif self.etype == "postgres":
            import psycopg2
            self.conn = psycopg2.connect(**config)
            
        elif self.etype == "mysql":
            import mysql.connector
            self.conn = mysql.connector.connect(**config)
            
        self.cursor = self.conn.cursor()

    def query(self, sql_string, params=None, fetch_all=True):
        if self.etype == "postgres":
            sql_string = sql_string.replace("?", "%s")
            
        self.cursor.execute(sql_string, params or ())
        
        if self.cursor.description:
            return self.cursor.fetchall() if fetch_all else self.cursor.fetchone()
        return None

    def commit(self):
        if self.conn:
            self.conn.commit()

    def close(self):
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
