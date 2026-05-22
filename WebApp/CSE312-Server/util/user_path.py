import hashlib
from bson.objectid import ObjectId
from util.response import Response
from util.database import users_collection
from util.auth import decode_percent, validate_password, extract_credentials
import bcrypt
import os
from util.multipart import parse_multipart
import uuid


def get_at_me(request, handler):
    print("get at me is called at some point")
    # Extract auth_token from cookies
    token = request.cookies.get("auth_token")
    if not token:
        # Not logged in
        res = Response()
        res.set_status("401", "Unauthorized")
        res.json({})
        handler.request.sendall(res.to_data())
        return

    # Hash the token to find the user
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    user = users_collection.find_one({"tokens": token_hash})
    if not user:
        # Invalid token
        res = Response()
        res.set_status("401", "Unauthorized")
        res.json({})

        handler.request.sendall(res.to_data())
        return

    # response json
    profile = {
        "username": user["username"],
        "id": str(user["_id"])
    }
    if "imageURL" in user:
        profile["imageURL"] = user["imageURL"]
    else:
        print("didn't add imageurl to user")

    # Add any other fields
    for key, value in user.items():
         #except their [hashed and salted] password and [hashed] auth token
        if key not in ("_id", "password_hash", "tokens"):
            profile[key] = value

    res = Response()
    res.set_status("200", "OK")
    res.json(profile)
    handler.request.sendall(res.to_data())

def search_users(request, handler):
    # Parse query string from request.path
    print("search_users method is called!!!!!!!!!!")
    query_params = {}
    if '?' in request.path:
        query_string = request.path.split('?', 1)[1]
        print(f"the query_string is {query_string}")

        query_params["user"] = query_string.split("=",1)[1]
        print(f"the params is {query_params}")

    
    search_term = query_params.get('user', [''])  # get first value or empty string
    print(f"Searchterm for search is: {search_term}")
    users_list = []
    if search_term:
        # Case-sensitive prefix search
        cursor = users_collection.find(
            
            {"username": {"$regex": "^" + search_term}},
            {"_id": 1, "username": 1}
        )
        for user in cursor:
            users_list.append({
                "id": str(user["_id"]),
                "username": user["username"]
            })
    print(f"user list the method found is: {users_list}")
    res = Response()
    res.set_status("200", "OK")
    res.json({"users": users_list})
    handler.request.sendall(res.to_data())

def update_settings(request, handler):
    
    token = request.cookies.get("auth_token")
    if not token:
        res = Response()
        res.set_status("401", "Unauthorized")
        res.text("you need to log in first")
        handler.request.sendall(res.to_data())
        return

    token_hash = hashlib.sha256(token.encode()).hexdigest()
    user = users_collection.find_one({"tokens": token_hash})

    # Parse form-urlencoded body
    new_username, new_password = extract_credentials(request)

    # Validate: at least one field must be provided
    if not new_username and not new_password:
        res = Response()
        res.set_status("400", "Bad Request")
        res.text("Something is missing for username and password")
        handler.request.sendall(res.to_data())
        return

    # Prepare update document
    update_fields = {}

    # Handle username change
    if new_username and new_username != user['username']:
        # Check uniqueness (case‑sensitive)
        existing = users_collection.find_one({"username": new_username})
        if existing:
            res = Response()
            res.set_status("400", "Bad Request")
            res.text("Username already exitst")
            handler.request.sendall(res.to_data())
            return
        update_fields['username'] = new_username

    # Handle password change (if provided and not empty)
    if new_password:
        if not validate_password(new_password):
            res = Response()
            res.set_status("400", "Bad Request")
            res.text("Password did not meet complexity requirements, try again")
            handler.request.sendall(res.to_data())
            return
        # Hash new password
        new_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
        update_fields['password_hash'] = new_hash

    # Apply updates
    if update_fields:
        users_collection.update_one(
            {"_id": user["_id"]},
            {"$set": update_fields}
        )

    res = Response()
    res.set_status("200", "OK")
    res.text("Setting updated")
    handler.request.sendall(res.to_data())


def upload_avatar(request, handler):
    # Authenticate user
    token = request.cookies.get("auth_token")
    if not token:
        res = Response()
        res.set_status("401", "Unauthorized")
        res.text("Not logged in")
        handler.request.sendall(res.to_data())
        return

    token_hash = hashlib.sha256(token.encode()).hexdigest()
    user = users_collection.find_one({"tokens": token_hash})
    if not user:
        res = Response()
        res.set_status("401", "Unauthorized")
        res.text("Invalid session")
        handler.request.sendall(res.to_data())
        return

    # Parse multipart request
    mp = parse_multipart(request)
    if not mp.parts:
        res = Response()
        res.set_status("400", "Bad Request")
        res.text("No parts found or exist")
        handler.request.sendall(res.to_data())
        return

    # look for a part with filename
    file_part = None
    for part in mp.parts:
        if part.filename:
            file_part = part
            break

    if not file_part:
        res = Response()
        res.set_status("400", "Bad Request")
        res.text("No such a file uploaded")
        handler.request.sendall(res.to_data())
        return

    # Get file extension and validate
    filename = file_part.filename
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ('.jpg', '.jpeg', '.png', '.gif'):
        res = Response()
        res.set_status("400", "Bad Request")
        res.text("Only .jpg, .png, .gif files are served")
        handler.request.sendall(res.to_data())
        return

    if ext == '.jpeg':
        ext = '.jpg'

    # Create directory if it doesn't exist
    upload_dir = "public/imgs/profile-pics"
    os.makedirs(upload_dir, exist_ok=True)

    # Generate unique filename
    unique_name = uuid.uuid4().hex + ext
    file_path = os.path.join(upload_dir, unique_name)

    # Save the file
    with open(file_path, "wb") as f:
        f.write(file_part.content)

    # Build the URL path
    image_url = f"/public/imgs/profile-pics/{unique_name}"

    # Update user's imageURL in database
    users_collection.update_one(
        {"_id": user["_id"]},
        {"$set": {"imageURL": image_url}}
    )

    # (Optional) Delete old file if you want to clean up
    # But spec does not require, so we skip.
    
    res = Response()
    res.set_status("200", "OK")
    res.text("Avatar uploaded")
    handler.request.sendall(res.to_data())