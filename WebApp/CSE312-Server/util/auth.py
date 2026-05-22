import json
import uuid
import random
import html
from bson.objectid import ObjectId
from util.request import Request
from util.database import chat_collection, sessions_collection

'''
def decode_percent(encoded_str):
    result = []
    i = 0
    strLen = len(encoded_str)
    while i < strLen:
        ch = encoded_str[i]
        if ch == '%' and i + 2 < strLen:
            hex_part = encoded_str[i+1:i+3]
            code = int(hex_part, 16)
            result.append(chr(code))
            i += 3
            continue
        # Normal character or unrecognized percent pattern
        result.append(ch)
        i += 1
    return ''.join(result)
'''
def decode_percent(encoded_str):
    result = ""
    i = 0
    strLen = len(encoded_str)
    while i < strLen:
        ch = encoded_str[i]
        if ch == '%' and i + 2 < strLen:
            hex_part = encoded_str[i+1:i+3]
            code = int(hex_part, 16)
            result += chr(code)
            i += 3
            continue
        # Normal character or unrecognized percent pattern
        result += ch
        i += 1
    return result

def extract_credentials(request):
    body = request.body.decode()
    bodys = body.split("&")

    username = bodys[0].split("=")[1]

    p = bodys[1].split("=")[1]
    password = decode_percent(p)

    return [username,password]


def validate_password(password):
    allowed_special = {'!', '@', '#', '$', '%', '^', '&', '(', ')', '-', '_', '='}
    lencheck = True
    lowcheck = False
    upcheck = False
    numcheck = False
    specialcheck = False
    if len(password) < 8:
        lencheck = False
    
    for c in password:
        if c.islower():
            lowcheck = True
        if c.isupper():
            upcheck = True
        if c.isdigit():
            numcheck = True
        if c in allowed_special:
            specialcheck = True
        if not (('a' <= c <= 'z') or ('A' <= c <= 'Z') or ('0' <= c <= '9') or c in allowed_special):
            print("The password contain a non-allowed character")
            return False
        
    return lencheck and lowcheck and upcheck and numcheck and specialcheck




'''
def test1():
    request = Request(b'POST /register HTTP/1.1\r\nHost: localhost:8080\r\nConnection: keep-alive\r\nContent-Length: 38\r\nsec-ch-ua-platform: "macOS"\r\nUser-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36\r\nsec-ch-ua: "Not(A:Brand";v="8", "Chromium";v="144", "Google Chrome";v="144"\r\nContent-Type: application/x-www-form-urlencoded\r\nsec-ch-ua-mobile: ?0\r\nAccept: */*\r\nOrigin: http://localhost:8080\r\nSec-Fetch-Site: same-origin\r\nSec-Fetch-Mode: cors\r\nSec-Fetch-Dest: empty\r\nReferer: http://localhost:8080/register\r\nAccept-Encoding: gzip, deflate, br, zstd\r\nAccept-Language: en-US,en;q=0.9\r\nCookie: session=c19ca317d98d4389ac66883b3f8acab5\r\n\r\nusername=yan12345&password=Yan12345%21')
    result = extract_credentials(request)
    assert ["yan12345","Yan12345!"]

def test2():
    #correct format
    assert validate_password("Yan12345!") == True
    #lack length
    assert validate_password("Yan") == False
    #lack symbol
    assert validate_password("Yan12345") == False
    #lack lower
    assert validate_password("YAN12345!") == False
    #lake upper
    assert validate_password("yan12345!") == False
    #lack number
    assert validate_password("Yananana!") == False
    #not in range
    assert validate_password("错误密码12345!Yan") == False

if __name__ == '__main__':
    test1()
    test2()
'''