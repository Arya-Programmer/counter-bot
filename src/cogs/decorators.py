import os
import sqlite3
from functools import wraps

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_DIR = os.path.join(BASE_DIR, "../info.db")


def connectToDB(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        db = sqlite3.connect(DB_DIR, timeout=3)
        cursor = db.cursor()
        kwargs = {**kwargs, "cursor": cursor}

        res = await func(*args, **kwargs)

        db.commit()
        cursor.close()
        db.close()
        return res

    return wrapper
