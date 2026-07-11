import httpx
from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from asgi_correlation_id import CorrelationIdMiddleware, correlation_id
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from shiftmaster_common.middleware.setup import unhandled_exception_handler
from shiftmaster_common.logging.structured import get_logger
from shiftmaster_common.security.jwt_utils import verify_token
import jwt
from app.core.config import settings

logger = get_logger(__name__)

app = FastAPI(
    title="ShiftMaster API Gateway",
    version="1.0.0",
    description="Main entry point for ShiftMaster microservices.",
    docs_url=None, # Disable default docs to use custom below
)

from fastapi.responses import HTMLResponse

@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
      <title>ShiftMaster API Gateway - Swagger UI</title>
      <link type="text/css" rel="stylesheet" href="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css">
      <link rel="shortcut icon" href="https://fastapi.tiangolo.com/img/favicon.png">
    </head>
    <body>
      <div id="swagger-ui"></div>
      <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
      <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-standalone-preset.js"></script>
      <script>
        window.onload = function() {
          const ui = SwaggerUIBundle({
            urls: [
                {"url": "/openapi.json", "name": "API Gateway"},
                {"url": "/api/v1/auth/openapi.json", "name": "Auth Service"},
                {"url": "/api/v1/schedule/openapi.json", "name": "Schedule Service"},
                {"url": "/api/v1/notifications/openapi.json", "name": "Notifications Service"},
                {"url": "/api/v1/monolith/openapi.json", "name": "Core Monolith"}
            ],
            "urls.primaryName": "API Gateway",
            dom_id: '#swagger-ui',
            deepLinking: true,
            presets: [
              SwaggerUIBundle.presets.apis,
              SwaggerUIStandalonePreset
            ],
            layout: "StandaloneLayout"
          })
          window.ui = ui
        }
      </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

app.add_exception_handler(Exception, unhandled_exception_handler)
app.add_middleware(CorrelationIdMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Should be configurable in prod
    allow_credentials=False, # Must be False if allow_origins is ["*"]
    allow_methods=["*"],
    allow_headers=["*", "X-Correlation-ID"],
    expose_headers=["X-Correlation-ID"],
)

from fastapi.responses import RedirectResponse

@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/docs")

# Shared httpx client
client = httpx.AsyncClient(timeout=30.0)

# Circuit breaker / retry for inter-service calls
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=5),
    retry=retry_if_exception_type(httpx.RequestError),
    reraise=True
)
async def forward_request(request: Request, target_url: str) -> Response:
    url = f"{target_url}{request.url.path}?{request.url.query}" if request.url.query else f"{target_url}{request.url.path}"
    
    headers = dict(request.headers)
    headers.pop("host", None)
    headers.pop("content-length", None)
    
    # Inject correlation ID
    cid = correlation_id.get()
    if cid:
        headers["X-Correlation-ID"] = cid

    # Verify JWT for non-public routes
    public_paths = [
        "/api/v1/auth/login",
        "/api/v1/auth/swagger-login",
        "/health"
    ]
    
    if request.url.path not in public_paths and not request.url.path.endswith("openapi.json") and not request.url.path.endswith("docs"):
        auth_header = headers.get("authorization", "")
        if not auth_header.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
        token = auth_header.split(" ")[1]
        try:
            payload = verify_token(token, settings.jwt_secret)
            user_id = payload.get("sub")
            if user_id:
                headers["X-User-Id"] = user_id
            
            user_role = payload.get("role")
            if user_role:
                headers["X-User-Role"] = user_role
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token has expired")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Could not validate credentials")

    try:
        logger.info("gateway.proxying", method=request.method, url=url)
        # We must use request.stream() to avoid loading large payloads into memory.
        # However, httpx doesn't accept an async generator for `content` directly in older versions, 
        # so we will use stream() by getting the body asynchronously. Wait, FastAPI request.stream() is an async generator.
        # Let's pass the async generator.
        res = await client.request(
            method=request.method,
            url=url,
            headers=headers,
            content=request.stream(),
        )
        return Response(
            content=res.content,
            status_code=res.status_code,
            headers=dict(res.headers)
        )
    except httpx.RequestError as exc:
        logger.error("gateway.request_failed", exc_info=exc, url=url)
        raise HTTPException(status_code=502, detail="Bad Gateway")

@app.api_route("/api/v1/auth/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"], include_in_schema=False)
@app.api_route("/api/v1/employees/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"], include_in_schema=False)
@app.api_route("/api/v1/departments/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"], include_in_schema=False)
async def proxy_auth(request: Request):
    return await forward_request(request, settings.auth_service_url)

@app.api_route("/api/v1/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"], include_in_schema=False)
async def proxy_monolith(request: Request, path: str):
    if path.startswith("schedules") or path.startswith("shifts") or path.startswith("handovers"):
        return await forward_request(request, settings.schedule_service_url)
    
    if path.startswith("audit") or path.startswith("notifications"):
        return await forward_request(request, settings.notification_service_url)

    # Anything else goes to the remaining monolith
    return await forward_request(request, settings.monolith_url)

@app.get("/api/v1/schedule/openapi.json", include_in_schema=False)
async def proxy_schedule_openapi(request: Request):
    return await forward_request(request, settings.schedule_service_url)

@app.get("/api/v1/notifications/openapi.json", include_in_schema=False)
async def proxy_notifications_openapi(request: Request):
    return await forward_request(request, settings.notification_service_url)

@app.get("/api/v1/monolith/openapi.json", include_in_schema=False)
async def proxy_monolith_openapi(request: Request):
    return await forward_request(request, settings.monolith_url)

@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok", "service": "gateway"}
