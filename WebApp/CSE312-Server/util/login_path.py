import bcrypt
import secrets
import hashlib
from util.response import Response
from util.database import users_collection
from util.auth import extract_credentials

def login(request, handler):
    username, password = extract_credentials(request)
    
    # Find user by username
    user = users_collection.find_one({"username": username})
    if not user:
        res = Response()
        res.set_status("400", "Not found")
        res.text("No such a username exist, try again or register one")
        handler.request.sendall(res.to_data())
        return
    
    # Verify password
    stored_password = user["password_hash"]
    if not bcrypt.checkpw(password.encode('utf-8'), stored_password):
        res = Response()
        res.set_status("400", "Not Found")
        res.text("Incorrect password, try again")
        handler.request.sendall(res.to_data())
        return
    
    token = secrets.token_urlsafe(32)  # 32 bytes
    # Hash the token (no salt)
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    
    # Store the token hash in the user's tokens list
    users_collection.update_one(
        {"_id": user["_id"]},
        {"$push": {"tokens": token_hash}}
    )
    
    # Set the cookie with HttpOnly and a Max-Age
    cookie_value = f"{token}; HttpOnly; Secure; Max-Age=43200; Path=/"
    
    res = Response()
    res.set_status("200", "OK")
    res.cookies({"auth_token": cookie_value})
    res.text("Login successful")
    handler.request.sendall(res.to_data())

def logout(request, handler):
    # Get the auth_token from cookies
    token = request.cookies.get("auth_token")
    
    if token:
        # Hash the token to get the stored hash
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        
        # Find user that has this token hash in their tokens array
        user = users_collection.find_one({"tokens": token_hash})
        
        if user:
            # Remove this token hash from the user's tokens array
            users_collection.update_one(
                {"_id": user["_id"]},
                {"$pull": {"tokens": token_hash}}
            )
    if not token:
        res = Response()
        res.set_status("400","no good")
        res.text("No such a auth_token in request")
        handler.request.sendall(res.to_data())

        
    # Clear the cookie by setting Max-Age=0
    expired_cookie = "auth_token=; HttpOnly; Secure; Max-Age=0; Path=/"
    
    # Prepare 302 redirect response
    res = Response()
    res.set_status("302", "Found")
    res.headers({"Location": "/"})
    res.cookies({"auth_token": expired_cookie})
    # No body needed for a redirect
    handler.request.sendall(res.to_data())