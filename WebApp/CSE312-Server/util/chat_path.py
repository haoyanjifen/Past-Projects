import json
import uuid
import random
import html
import hashlib
from bson.objectid import ObjectId
from util.response import Response
from util.database import chat_collection, sessions_collection, users_collection

# For random author names
adjectives = ["Happy", "Clever", "Brave", "Calm", "Eager", "Gentle", "Kind", "Witty", "Bright", "Bold"]
nouns = ["Panda", "Tiger", "Eagle", "Dolphin", "Fox", "Wolf", "Lion", "Falcon", "Shark", "Otter"]

def get_random_author():
    return f"{random.choice(adjectives)}{random.choice(nouns)}"

def extract_id_from_path(path, prefix):
    """Extract the ID part after prefix, stripping any query string."""
    if not path.startswith(prefix):
        return None
    remaining = path[len(prefix):]
    # Remove query string if present
    '''
    if '?' in remaining:
        remaining = remaining.split('?', 1)[0]
    print("PATH!!!\r\n")
    print(path)
    '''
    return remaining

def get_authenticated_user(request):
    """Return user dict if auth_token is valid, else None."""
    token = request.cookies.get("auth_token")
    if not token:
        return None
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    return users_collection.find_one({"tokens": token_hash})

def get_anonymous_session(request):
    session_id = request.cookies.get("session")
    if not session_id:
        session_id = uuid.uuid4().hex
        author = get_random_author()
        sessions_collection.insert_one({
            "session_id": session_id,
            "author_name": "Guest-" + author
        })
    return session_id

def create_chat_message(request, handler):

    # Parse JSON body
    body_str = request.body.decode('utf-8')
    data = json.loads(body_str)
    content = data.get("content")

    user = get_authenticated_user(request)

    message_doc = {
        "content": content,
        "reactions": {},
        "updated": False
    }

    if user:
        # Authenticated user: store username
        message_doc["author"] = user["username"]
        message_doc["user"] = user["username"]   # for ownership checks
        if "imageURL" in user:
            message_doc["imageURL"] = user["imageURL"]
    else:
        session_id = get_anonymous_session(request)
        session = sessions_collection.find_one({"session_id": session_id})
        author = session["author_name"]
        nickname = session.get("nickname")
        message_doc["author"] = author
        message_doc["session_id"] = session_id   # keep for legacy reactions/nickname
        if nickname:
            message_doc["nickname"] = nickname


    chat_collection.insert_one(message_doc)
    res = Response()
    res.set_status("200", "OK")

    if not user:
        cookie_value = f"{session_id}; HttpOnly; Path=/"
        res.cookies({"session": cookie_value})
    res.text("message sent")
    handler.request.sendall(res.to_data())
    '''
    # Handle session cookie
    session_id = request.cookies.get("session")
    author = None
    nickname = None
    if session_id:
        session = sessions_collection.find_one({"session_id": session_id})
        if session:
            author = session["author_name"]
            nickname = session.get("nickname")

    if not author:  # new user or invalid session
        session_id = uuid.uuid4().hex
        author = get_random_author()
        sessions_collection.insert_one({
            "session_id": session_id,
            "author_name": author
        })
    
    message_doc = {
        "content": content,
        "author": author,
        "updated": False,
        #HW1AO1
        "reactions": {},
        #HW1AO2,store session ID for future updates
        "session_id": session_id
    }
    
    if nickname:
        message_doc["nickname"] = nickname

    chat_collection.insert_one(message_doc)

    # Send success response with the session cookie
    res = Response()
    res.set_status("200", "OK")
    cookie_value = f"{session_id}; HttpOnly; Path=/"
    res.cookies({"session": cookie_value})
    res.text("message sent")
    handler.request.sendall(res.to_data())
    '''

def get_chat_messages(request, handler):
    messages = chat_collection.find({})
    message_list = []
    for message in messages:
        message_Dict = {
            "id": str(message["_id"]),
            "author": message["author"],
            "content": html.escape(message["content"]),
            "updated": message.get("updated", False),
            "reactions": message.get("reactions", {})
        }
        if "imageURL" in message:
            message_Dict["imageURL"] = message["imageURL"]
        if "nickname" in message:
            message_Dict["nickname"] = message["nickname"]
        message_list.append(message_Dict)

    res = Response()
    res.set_status("200", "OK")
    res.json({"messages": message_list})
    handler.request.sendall(res.to_data())
    
def update_chat_message(request, handler):
    prefix = "/api/chats/"
    message_id = extract_id_from_path(request.path, prefix)

    # Validate session
    #session_id = request.cookies.get("session")
    user = get_authenticated_user(request)
    if not user:
        res = Response()
        res.set_status("403", "Forbidden")
        res.text("Authentication required")
        handler.request.sendall(res.to_data())
        return
    '''
    session = sessions_collection.find_one({"session_id": session_id})
    if not session:
        res = Response()
        res.set_status("403", "Forbidden")
        res.text("Invalid session")
        handler.request.sendall(res.to_data())
        return
    author = session["author_name"]
    '''
    # Find the message
    obj_id = ObjectId(message_id)

    message = chat_collection.find_one({"_id": obj_id})

    # Check ownership
    if message.get("user") != user["username"]:
        res = Response()
        res.set_status("403", "Forbidden")
        res.text("You can only update your own messages")
        handler.request.sendall(res.to_data())
        return

    # Parse new content
    body_str = request.body.decode('utf-8')
    data = json.loads(body_str)
    new_content = data.get("content")

    # Update the message
    chat_collection.update_one(
        {"_id": obj_id},
        {"$set": {"content": new_content, "updated": True}}
    )

    res = Response()
    res.set_status("200", "OK")
    res.text("message updated")
    handler.request.sendall(res.to_data())

def delete_chat_message(request, handler):
    prefix = "/api/chats/"
    message_id = extract_id_from_path(request.path, prefix)

    # Validate session
    #session_id = request.cookies.get("session")
    user = get_authenticated_user(request)
    
    if not user:
        res = Response()
        res.set_status("403", "Forbidden")
        res.text("Authentication required")
        handler.request.sendall(res.to_data())
        return
    '''
    session = sessions_collection.find_one({"session_id": session_id})
    if not session:
        res = Response()
        res.set_status("403", "Forbidden")
        res.text("Invalid session")
        handler.request.sendall(res.to_data())
        return
    author = session["author_name"]
    '''
    # Find the message
    obj_id = ObjectId(message_id)

    message = chat_collection.find_one({"_id": obj_id})

    # Check ownership
    if message.get("user") != user["username"]:
        res = Response()
        res.set_status("403", "Forbidden")
        res.text("You can only delete your own messages")
        handler.request.sendall(res.to_data())
        return

    # Delete the message
    chat_collection.delete_one({"_id": obj_id})

    res = Response()
    res.set_status("200", "OK")
    res.text("message deleted")
    handler.request.sendall(res.to_data())

def add_emoji(request, handler):
    prefix = "/api/reaction/"
    message_id = extract_id_from_path(request.path, prefix)

    session_id = request.cookies.get("session")
    if not session_id:
        res = Response()
        res.set_status("403", "Forbidden")
        res.text("no session id")
        handler.request.sendall(res.to_data())
        return
    session = sessions_collection.find_one({"session_id": session_id})
    if not session:
        res = Response()
        res.set_status("403", "Forbidden")
        res.text("Invalid session")
        handler.request.sendall(res.to_data())
        return
    

    body_str = request.body.decode('utf-8')
    data = json.loads(body_str)
    emoji = data.get("emoji")

    obj_id = ObjectId(message_id)
    message = chat_collection.find_one({"_id": obj_id})
    
    reactions = message.get("reactions", {})
    if emoji in reactions and session_id in reactions[emoji]:
        res = Response()
        res.set_status("403", "Forbidden")
        res.text("You can't reacted with the same emoji")
        handler.request.sendall(res.to_data())
        return
    
    chat_collection.update_one(
        {"_id": obj_id},
        {"$addToSet": {f"reactions.{emoji}": session_id}}
    )

    res = Response()
    res.set_status("200", "OK")
    res.text("Reaction add successful")
    handler.request.sendall(res.to_data())
    

def delete_emoji(request,handler):
    prefix = "/api/reaction/"
    message_id = extract_id_from_path(request.path, prefix)

    session_id = request.cookies.get("session")
    if not session_id:
        res = Response()
        res.set_status("403", "Forbidden")
        res.text("no session id")
        handler.request.sendall(res.to_data())
        return
    session = sessions_collection.find_one({"session_id": session_id})
    if not session:
        res = Response()
        res.set_status("403", "Forbidden")
        res.text("Invalid session")
        handler.request.sendall(res.to_data())
        return


    body_str = request.body.decode('utf-8')
    data = json.loads(body_str)
    emoji = data.get("emoji")
    obj_id = ObjectId(message_id)
    message = chat_collection.find_one({"_id": obj_id})

    reactions = message.get("reactions", {})
    if emoji not in reactions:
        print("Error Report: emoji not in reaction")

    if session_id not in reactions[emoji]:
        print("Error Report: session-id not in database")

    if session_id  in reactions[emoji]:
        print("Correct Report: session-id  in database")

    if emoji  in reactions:
        print("Correct Report: emoji in reaction")

    if emoji not in reactions or session_id not in reactions[emoji]:
        res = Response()
        res.set_status("403", "Forbidden")
        res.text("No such a reaction in this message")
        handler.request.sendall(res.to_data())
        return
    
 
    chat_collection.update_one(
        {"_id": obj_id},
        {"$pull": {f"reactions.{emoji}": session_id}}
    )

    update_message = chat_collection.find_one({"_id": obj_id})
    update_reactions = update_message.get("reactions",{})
    if not update_reactions.get(emoji,[]):
        chat_collection.update_one(
            {"_id":obj_id},
            {"$unset": {f"reactions.{emoji}":""}}
        )


    print("REMOVE!!!!!!!!!!!!!")
    res = Response()
    res.set_status("200", "OK")
    res.text("Reaction delete successful")
    handler.request.sendall(res.to_data())

def update_nickname(request,handler):
    session_id = request.cookies.get("session")
    session = sessions_collection.find_one({"session_id": session_id})
    body_str = request.body.decode('utf-8')
    data = json.loads(body_str)
    nickname = data.get("nickname")
    sessions_collection.update_one(
        {"session_id": session_id},
        {"$set": {"nickname": nickname}}
    )
    chat_collection.update_many(
        {"session_id": session_id},
        {"$set": {"nickname": nickname}}
    )
    res = Response()
    res.set_status("200", "OK")
    res.text("Nickname change successfully")
    handler.request.sendall(res.to_data())