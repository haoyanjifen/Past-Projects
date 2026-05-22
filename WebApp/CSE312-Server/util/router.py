from util.request import Request
from util.response import Response
class Router:

    def __init__(self):
        self.allRoutes = []
        pass

    def add_route(self, method, path, action, exact_path=False):
        self.allRoutes.append({'method': method,'path': path,'action': action,'exact_path': exact_path})
        pass

    def route_request(self, request, handler):
        '''
        print("\r\n")
        print("Here is the request:\r\n")
        print(request.decode())
        print("\r\n")
        '''
        for route in self.allRoutes:
            if route["method"] != request.method:
                continue
            if route["exact_path"]:
                if route["path"] == request.path:
                    route["action"](request,handler)
                    return
            else:
                if request.path.startswith(route['path']):
                    route['action'](request, handler)
                    return
        res = Response()
        res.set_status("404", "Error in Router Class, No such a Route stored")
        res.headers({"Content-Type": "text/html; charset=utf-8"}) 
        res.text("Error in Router Class, No such a Route stored")
        handler.request.sendall(res.to_data())
