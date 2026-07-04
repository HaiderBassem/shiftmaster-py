import os
from dotenv import load_dotenv

with open("test_env.env", "w", encoding="utf-8") as f:
    f.write('CORS_ALLOWED_ORIGINS=["http://localhost:3000","http://localhost:5173"]\n')

load_dotenv("test_env.env", override=True)

try:
    from app.core.config import Settings
    s = Settings()
    print("SUCCESS")
    print(s.cors.allowed_origins)
except Exception as e:
    import traceback
    traceback.print_exc()
