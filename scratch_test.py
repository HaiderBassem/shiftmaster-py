import bcrypt
import sys

hashed = b"$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW"
plain = b"password"

try:
    if bcrypt.checkpw(plain, hashed):
        print("MATCH")
    else:
        print("NO MATCH")
        new_hash = bcrypt.hashpw(plain, bcrypt.gensalt())
        print(new_hash.decode('utf-8'))
except Exception as e:
    print(f"ERROR: {e}")
