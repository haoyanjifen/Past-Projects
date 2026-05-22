from util.response import Response
import os

def serve_static(request, handler):
    file_path = "." + request.path   # e.g. ./public/imgs/dog.jpg

    # Determine MIME type from file extension
    ext = os.path.splitext(file_path)[1].lower()
    mime_types = {
        ".jpg":  "image/jpeg",
        ".ico":  "image/x-icon",
        ".gif":  "image/gif",
        ".webp": "image/webp",
        ".js":   "application/javascript; charset=utf-8",
        ".html": "text/html; charset=utf-8",
        ".mp4":  "video/mp4",
        ".png":  "image/png",
    }
    content_type = mime_types.get(ext)

    try:
        with open(file_path, "rb") as f:
            file_bytes = f.read()
    except FileNotFoundError:
        res = Response()
        res.set_status("404", "Not Found")
        res.text("404 Not Found")
        handler.request.sendall(res.to_data())
        return

    res = Response()
    res.set_status("200", "OK")
    res.headers({"Content-Type": content_type})
    res.bytes(file_bytes)
    handler.request.sendall(res.to_data())

def serve_index(request, handler):
    render_page("index.html", handler)

def serve_chat(request, handler):
    render_page("chat.html", handler)

def serve_register(request,handler):
    render_page("register.html",handler)

def serve_login(request,handler):
    render_page("login.html",handler)

def serve_settings(request,handler):
    render_page("settings.html",handler)

def serve_search_users(request,handler):
    render_page("search-users.html",handler)

def serve_change_avatar(request, handler):
    render_page("change-avatar.html",handler)

def serve_videotube(request, handler):
    render_page("videotube.html",handler)

def serve_videotube_upload(request, handler):
    render_page("upload.html",handler)

def serve_view_video(request, handler):
    render_page("view-video.html",handler)

'''
With your 3 helper methods ready, you will now add WebSocket features to your app. First, add the following HTML paths to your server:

"/test-websocket" - Render test-websocket.html
"/drawing-board" - Render drawing-board.html
"/video-call" - Render video-call.html (AO2)
"/video-call/{roomID}" - Render video-call-room.html (AO2)
'''

def serve_test_websocket(request, handler):
    render_page("test-websocket.html", handler)

def serve_drawing_board(request, handler):
    render_page("drawing-board.html", handler)

def serve_video_call(request,handler):
    render_page("video-call.html",handler)

def serve_video_call_ID(request,handler):
    render_page("video-call-room.html", handler)



def render_page(page_filename, handler):
    layout_path = "./public/layout/layout.html"
    page_path = f"./public/{page_filename}"

    try:
        with open(layout_path, "r", encoding="utf-8") as f:
            layout = f.read()
        with open(page_path, "r", encoding="utf-8") as f:
            page_content = f.read()
    except FileNotFoundError:
        res = Response()
        res.set_status("404", "Not Found")
        res.text("Page not found")
        handler.request.sendall(res.to_data())
        return

    full_html = layout.replace("{{content}}", page_content)

    res = Response()
    res.set_status("200", "OK")
    res.headers({"Content-Type": "text/html; charset=utf-8"})
    res.text(full_html)
    handler.request.sendall(res.to_data())