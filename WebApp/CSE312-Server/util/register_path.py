import uuid
import bcrypt
from util.response import Response
from util.request import Request
from util.database import chat_collection, sessions_collection, users_collection
from util.auth import *

def register(request,handler):
    print("The request is run in /register_py.py")
    username, password = extract_credentials(request)
    if not validate_password(password):
        res = Response()
        res.set_status("400", "Not Found")
        res.text("password is not valid")
        handler.request.sendall(res.to_data())
        return
    if users_collection.find_one({"username": username}):
        res = Response()
        res.set_status("400", "not found")
        res.text("Username already exists")
        handler.request.sendall(res.to_data())
        return
    # Hash the password with a salt (bcrypt does this automatically)
    
    s = bcrypt.gensalt()
    password_hash = bcrypt.hashpw(password.encode('utf-8'), s) # Hash password with salt
    user_doc = {
        "username": username,
        "password_hash": password_hash,
        "tokens": []
    }
    users_collection.insert_one(user_doc)
    res = Response()
    res.set_status("200", "OK")
    res.text("Registration successful")
    handler.request.sendall(res.to_data())
    return
