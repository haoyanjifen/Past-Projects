import os
import uuid
import datetime
import hashlib
from bson.objectid import ObjectId
from util.response import Response
from util.database import users_collection, videos_collection
from util.multipart import parse_multipart

#Helper to get authenticated user from auth_token cookie
def get_authenticated_user(request):
    token = request.cookies.get("auth_token")
    if not token:
        return None
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    return users_collection.find_one({"tokens": token_hash})

def upload_video(request, handler):
    user = get_authenticated_user(request)
    if not user:
        res = Response()
        res.set_status("401", "Unauthorized")
        res.text("Not logged in")
        handler.request.sendall(res.to_data())
        return

    # p arse multipart request
    mp = parse_multipart(request)
    if not mp.parts:
        res = Response()
        res.set_status("400", "Bad Request")
        res.text("No parts found")
        handler.request.sendall(res.to_data())
        return

    # Extract title, description, video file
    title = ""
    description = ""
    video_content = None
    video_filename = None

    for part in mp.parts:
        if part.name == "title":
            title = part.content.decode('utf-8')
        elif part.name == "description":
            description = part.content.decode('utf-8')
        elif part.filename:  #video file part
            video_content = part.content
            video_filename = part.filename

    # validate required fields
    if not title or not description or not video_content:
        res = Response()
        res.set_status("400", "Bad Request")
        res.text("missing title, description, or video file")
        handler.request.sendall(res.to_data())
        return

    # only .mp4
    ext = os.path.splitext(video_filename)[1].lower()
    if ext != '.mp4':
        res = Response()
        res.set_status("400", "Bad Request")
        res.text("Only .mp4 videos are allowed")
        handler.request.sendall(res.to_data())
        return

    # Create  directory 
    upload_dir = "public/videos"
    os.makedirs(upload_dir, exist_ok=True)

    # make unique filename
    unique_name = uuid.uuid4().hex + ext
    file_path = os.path.join(upload_dir, unique_name)

    # save video file
    with open(file_path, "wb") as f:
        f.write(video_content)

    # build video url path
    video_url = f"/public/videos/{unique_name}"

    created_at = datetime.datetime.now().isoformat()

    video_doc = {
        "author_id": user["username"],
        "title": title,
        "description": description,
        "video_path": video_url,
        "created_at": created_at,
        "user_id": str(user["_id"])  
    }
    result = videos_collection.insert_one(video_doc)
    video_id = str(result.inserted_id)

    res = Response()
    res.set_status("200", "OK")
    res.json({"id": video_id})
    handler.request.sendall(res.to_data())

def get_all_videos(request, handler):
    cursor = videos_collection.find().sort("created_at", -1)
    videos_list = []
    for v in cursor:
        videos_list.append({
            "id": str(v["_id"]),
            "author_id": v["author_id"],
            "title": v["title"],
            "description": v["description"],
            "video_path": v["video_path"],
            "created_at": v["created_at"]
        })
    res = Response()
    res.set_status("200", "OK")
    res.json({"videos": videos_list})
    handler.request.sendall(res.to_data())

def get_single_video(request, handler):
    # Extract video_id from path
    # reminder the path is /api/videos/{video_id}
    path_parts = request.path.split('/')
    if len(path_parts) < 4:
        res = Response()
        res.set_status("404", "Not Found")
        res.text("Invalid video ID")
        handler.request.sendall(res.to_data())
        return
    video_id = path_parts[3]  # after /api/videos/?

    try:
        obj_id = ObjectId(video_id)
    except:
        res = Response()
        res.set_status("404", "Not Found")
        res.text("Invalid video ID")
        handler.request.sendall(res.to_data())
        return

    video = videos_collection.find_one({"_id": obj_id})
    if not video:
        res = Response()
        res.set_status("404", "Not Found")
        res.text("Video not found")
        handler.request.sendall(res.to_data())
        return

    video_data = {
        "id": str(video["_id"]),
        "author_id": video["author_id"],
        "title": video["title"],
        "description": video["description"],
        "video_path": video["video_path"],
        "created_at": video["created_at"]
    }
    res = Response()
    res.set_status("200", "OK")
    res.json({"video": video_data})
    handler.request.sendall(res.to_data())