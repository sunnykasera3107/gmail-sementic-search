import base64

def decode_base64(data):
    return base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
