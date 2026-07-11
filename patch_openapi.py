import os
import re

files = [
    "services/auth/app/main.py",
    "services/schedule/app/main.py",
    "services/notifications/app/main.py",
    "app/main.py"
]

patch = """
from fastapi.openapi.utils import get_openapi

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
        tags=app.openapi_tags,
    )
    openapi_schema["components"]["securitySchemes"] = {
        "OAuth2PasswordBearer": {
            "type": "oauth2",
            "flows": {
                "password": {
                    "tokenUrl": "/api/v1/auth/swagger-login",
                    "scopes": {}
                }
            }
        }
    }
    for path in openapi_schema.get("paths", {}):
        for method in openapi_schema["paths"][path]:
            if "health" not in path and "swagger-login" not in path and "login" not in path:
                openapi_schema["paths"][path][method]["security"] = [{"OAuth2PasswordBearer": []}]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi
"""

for fpath in files:
    if os.path.exists(fpath):
        with open(fpath, "r") as f:
            content = f.read()
        
        if "custom_openapi" not in content:
            content += "\n" + patch
            with open(fpath, "w") as f:
                f.write(content)
            print(f"Patched {fpath}")

