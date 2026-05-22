from util.request import Request
class Part:
    """Represents a single part of a multipart request."""
    def __init__(self, headers, name, content,filename=None):
        self.headers = headers
        self.name = name
        self.content = content
        self.filename = filename


class MultipartData:
    """Represents a parsed multipart request."""
    def __init__(self, boundary, parts):
        self.boundary = boundary
        self.parts = parts


def parse_multipart(request):
    """
    Parse a multipart request and return a MultipartData object.

    Args:
        request: A Request object (from request.py) with headers and body.

    Returns:
        MultipartData object containing the boundary and parts.
    """
    # Extract Content-Type header
    content_type = request.headers.get("Content-Type", "")
    # Find boundary
    boundary = None
    for part in content_type.split(";"):
        part = part.strip()
        if part.startswith("boundary="):
            boundary = part.split("=", 1)[1]
            break

    if boundary is None:
        # No boundary found – return empty result
        return MultipartData("", [])

    # Prepare byte delimiters
    delim = b"--" + boundary.encode()
    final_delim = delim + b"--"

    body = request.body
    parts_list = []

    pos = 0
    # Find the first boundary
    first_delim_pos = body.find(delim, pos)
    if first_delim_pos == -1:
        # No boundary found
        return MultipartData(boundary, [])

    # Start after the first boundary and its trailing CRLF
    part_start = first_delim_pos + len(delim)
    if body[part_start:part_start+2] == b"\r\n":
        part_start += 2

    while True:
        # Find the next boundary (starts the next part or is the final one)
        next_delim_pos = body.find(delim, part_start)
        if next_delim_pos == -1:
            # Malformed request – break
            break

        # Check if this is the final boundary
        is_final = body[next_delim_pos:next_delim_pos+len(final_delim)] == final_delim

        # Determine where the current part ends (excluding the trailing CRLF before the next boundary)
        part_end = next_delim_pos
        if body[part_end-2:part_end] == b"\r\n":
            part_end -= 2

        # Extract the part bytes (headers + content)
        part_bytes = body[part_start:part_end]

        # Split headers and content at the first CRLFCRLF
        if b"\r\n\r\n" not in part_bytes:
            # Malformed part – skip
            part_start = next_delim_pos + len(delim)
            if body[part_start:part_start+2] == b"\r\n":
                part_start += 2
            if is_final:
                break
            continue

        header_bytes, content = part_bytes.split(b"\r\n\r\n", 1)

        # Parse headers
        headers = {}
        for line in header_bytes.split(b"\r\n"):
            if not line:
                continue
            if b": " in line:
                key, value = line.split(b": ", 1)
                headers[key.decode()] = value.decode()

        # Extract name from Content-Disposition header
        name = ""
        filename = None
        cd = headers.get("Content-Disposition", "")
        #Parse name="..."
        name_start = cd.find('name="')
        if name_start != -1:
            name_start += len('name="')
            name_end = cd.find('"', name_start)
            if name_end != -1:
                name = cd[name_start:name_end]
        # Parse filename
        filename_start = cd.find('filename="')
        if filename_start != -1:
            filename_start += len('filename="')
            filename_end = cd.find('"', filename_start)
            if filename_end != -1:
                filename = cd[filename_start:filename_end]
        

        # Create Part object
        part = Part(headers, name, content, filename)
        parts_list.append(part)

        # Prepare for next iteration
        part_start = next_delim_pos + len(delim)
        if body[part_start:part_start+2] == b"\r\n":
            part_start += 2

        if is_final:
            break

    return MultipartData(boundary, parts_list)