class Request:

    def __init__(self, request: bytes):
        # TODO: parse the bytes of the request and populate the following instance variables
        
        self.body = b""
        self.method = ""
        self.path = ""
        self.http_version = ""
        self.headers = {}
        self.cookies = {}

        # Split headers and body
        parts = request.split(b"\r\n\r\n", 1)
        header_data = parts[0].decode('utf-8', errors='replace')
        if len(parts) > 1:
            self.body = parts[1]

        lines = header_data.split("\r\n")
        if not lines:
            return

        # Parse request line
        request_line = lines[0].split()
        if len(request_line) >= 3:
            self.method = request_line[0]
            self.path = request_line[1]
            self.http_version = request_line[2]

        # Parse headers
        for line in lines[1:]:
            if not line:
                continue
            if ": " in line:
                key, value = line.split(": ", 1)
                self.headers[key] = value.strip()
            else:
                # Handle malformed headers (ignore)
                continue

        # Parse cookies from Cookie header
        if "Cookie" in self.headers:
            cookie_str = self.headers["Cookie"]
            for pair in cookie_str.split(";"):
                pair = pair.strip()
                if "=" in pair:
                    name, value = pair.split("=", 1)
                    self.cookies[name.strip()] = value.strip()




def test1():
    request = Request(b'GET / HTTP/1.1\r\nHost: localhost:8080\r\nConnection: keep-alive\r\n\r\n')
    assert request.method == "GET"
    assert "Host" in request.headers
    assert request.headers["Host"] == "localhost:8080"  # note: The leading space in the header value must be removed
    assert request.body == b""  # There is no body for this request.
    # When parsing POST requests, the body must be in bytes, not str

    # This is the start of a simple way (ie. no external libraries) to test your code.
    # It's recommended that you complete this test and add others, including at least one
    # test using a POST request. Also, ensure that the types of all values are correct


def test2():
    request = Request(b'POST / HTTP/1.1\r\nHost: localhost:8080\r\nCookie: a=1;b=2;c=3\r\nConnection: keep-alive\r\n\r\nthis is the body')
    assert request.method == "POST"
    assert "Host" in request.headers
    assert request.headers["Host"] == "localhost:8080"  # note: The leading space in the header value must be removed
    assert request.body == b"this is the body"  # There is no body for this request.
    # When parsing POST requests, the body must be in bytes, not str
    assert request.http_version == "HTTP/1.1"
    assert request.path == "/"
    assert "Cookie" in request.headers
    assert request.headers["Cookie"] == "a=1;b=2;c=3"
    assert "a" in request.cookies
    assert "b" in request.cookies
    assert "c" in request.cookies
    assert request.cookies["a"] == "1"
    assert request.cookies["b"] == "2"
    assert request.cookies["c"] == "3"
    print(request.cookies)
    print(request.headers)




if __name__ == '__main__':
    test1()
    test2()
