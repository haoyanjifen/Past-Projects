import socketserver
from util.request import Request
from util.router import Router
from util.hello_path import hello_path
from util.public_path import *
from util.chat_path import *
from util.register_path import register
from util.login_path import login, logout
from util.user_path import *
from util.video_path import *
from util.ws_handlers import *

class MyTCPHandler(socketserver.BaseRequestHandler):

    def __init__(self, request, client_address, server):
        self.router = Router()
        self.router.add_route("GET", "/hello", hello_path, True)
        # TODO: Add your routes here
        
        #render page
        self.router.add_route("GET",    "/public",     serve_static,    False)
        self.router.add_route("GET",    "/",           serve_index,     True)
        self.router.add_route("GET",    "/chat",       serve_chat,      True)
        self.router.add_route("GET",    "/register",   serve_register,      True)
        self.router.add_route("GET",    "/login",      serve_login,      True)
        self.router.add_route("GET",    "/settings",   serve_settings,      True)
        self.router.add_route("GET",    "/search-users",   serve_search_users,      True)


        #chats features - HW1
        self.router.add_route("POST",   "/api/chats",  create_chat_message, True)
        self.router.add_route("GET",    "/api/chats",  get_chat_messages, True)
        self.router.add_route("PATCH",  "/api/chats/", update_chat_message, False)
        self.router.add_route("DELETE", "/api/chats/", delete_chat_message, False)
        self.router.add_route("PATCH",  "/api/reaction/",   add_emoji, False)
        self.router.add_route("DELETE",  "/api/reaction/",   delete_emoji, False)
        self.router.add_route("PATCH",  "/api/nickname",    update_nickname, True)

        #HW2
        self.router.add_route("POST",   "/register",   register, True)
        self.router.add_route("POST",   "/login",      login,    True)
        self.router.add_route("GET", "/logout",         logout, True)
        self.router.add_route("GET", "/api/users/@me", get_at_me, True)
        self.router.add_route("GET", "/api/users/search", search_users, False)
        self.router.add_route("POST", "/api/users/settings", update_settings, True)

        #HW3
        self.router.add_route("GET",    "/change-avatar",   serve_change_avatar, True)
        self.router.add_route("POST", "/api/users/avatar", upload_avatar, True)

        self.router.add_route("GET",    "/videotube",   serve_videotube, True)
        self.router.add_route("GET",    "/videotube/upload",   serve_videotube_upload, True)
        self.router.add_route("GET",    "/videotube/videos/",   serve_view_video, False)

        self.router.add_route("POST", "/api/videos", upload_video, True)
        self.router.add_route("GET", "/api/videos", get_all_videos, True)
        self.router.add_route("GET", "/api/videos/", get_single_video, False)

        #HW4
        self.router.add_route("GET", "/test-websocket", serve_test_websocket, True)
        self.router.add_route("GET", "/drawing-board", serve_drawing_board, True)
        self.router.add_route("GET", "/video-call", serve_video_call, True)
        self.router.add_route("GET", "/video-call/", serve_video_call_ID, False)

        self.router.add_route("GET", "/websocket", websocket_handler, True)



        super().__init__(request, client_address, server)

    def handle(self):
        received_data = self.request.recv(2048)
        print(self.client_address)
        '''
        print("--- received data ---")
        print(received_data)
        print("--- end of data ---\n\n")
        '''

        if not received_data:
            return

        # find the end of headers
        header_end = received_data.find(b'\r\n\r\n')

        # parse Content-Length from the headers
        header_part = received_data[:header_end]
        content_length = 0
        for line in header_part.split(b'\r\n'):
            if line.lower().startswith(b'content-length:'):
                content_length = int(line.split(b':')[1].strip())
                break

        #read the rest
        if content_length > 0:
            body_received = len(received_data) - (header_end + 4)
            while body_received < content_length:
                chunk = self.request.recv(4096)
                if not chunk:
                    break
                received_data += chunk
                body_received += len(chunk)

        request = Request(received_data)
        self.router.route_request(request, self)

def main():
    host = "0.0.0.0"
    port = 8080
    socketserver.ThreadingTCPServer.allow_reuse_address = True

    server = socketserver.ThreadingTCPServer((host, port), MyTCPHandler)

    print("Listening on port " + str(port))
    server.serve_forever()


if __name__ == "__main__":
    main()
