from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

def setup_custom_openapi(app: FastAPI, security_url: str = "/api/v1/auth/swagger-login") -> None:
    def custom_openapi():
        if app.openapi_schema:
            return app.openapi_schema
        openapi_schema = get_openapi(
            title=app.title,
            version=app.version,
            description=app.description,
            routes=app.routes,
            tags=app.openapi_tags if hasattr(app, "openapi_tags") else None,
        )
        openapi_schema["components"]["securitySchemes"] = {
            "OAuth2PasswordBearer": {
                "type": "oauth2",
                "flows": {
                    "password": {
                        "tokenUrl": security_url,
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
