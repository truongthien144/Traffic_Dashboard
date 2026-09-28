# auth.py
from pydantic import BaseModel
import jwt
from datetime import datetime, timedelta
from fastapi import HTTPException

SECRET_KEY = "its_core_secret_key_super_safe"
ALGORITHM = "HS256"

USERS = {
    "admin@gmail.com": "admin123",
    "root@gmail.com": "root123"
}

class LoginRequest(BaseModel):
    email: str
    password: str

def verify_login(request: LoginRequest):
    if request.email in USERS and USERS[request.email] == request.password:
        expire = datetime.utcnow() + timedelta(hours=24)
        payload = {"sub": request.email, "exp": expire, "role": "admin"}
        token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
        return {"access_token": token, "token_type": "bearer", "message": "Đăng nhập thành công"}
    raise HTTPException(status_code=401, detail="Tài khoản hoặc mật khẩu không chính xác")