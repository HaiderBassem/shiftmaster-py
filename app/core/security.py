from datetime import datetime, timedelta
import jwt
import bcrypt

from app.core.config import settings

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception:
        return False

def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def create_access_token(subject: str | int, role: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=settings.jwt.access_expire_min)
    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "role": role
    }
    encoded_jwt = jwt.encode(to_encode, settings.jwt.secret, algorithm="HS256")
    return encoded_jwt

def verify_token(token: str) -> dict:
    return jwt.decode(token, settings.jwt.secret, algorithms=["HS256"])


