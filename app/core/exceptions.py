from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.status import HTTP_422_UNPROCESSABLE_ENTITY
import traceback
from app.core.config import settings


def register_exception_handlers(app):
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        origin = request.headers.get("origin")
        allow = origin if origin and (settings.DEBUG or origin in settings.cors_origins_list) else (
            "*" if settings.DEBUG else (settings.cors_origins_list[0] if settings.cors_origins_list else "*")
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "detail": exc.detail,
                "status_code": exc.status_code,
                "path": request.url.path,
            },
            headers={"Access-Control-Allow-Origin": allow, "Access-Control-Allow-Credentials": "true"},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        origin = request.headers.get("origin")
        allow = origin if origin and (settings.DEBUG or origin in settings.cors_origins_list) else (
            "*" if settings.DEBUG else (settings.cors_origins_list[0] if settings.cors_origins_list else "*")
        )
        return JSONResponse(
            status_code=HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "detail": exc.errors(),
                "body": exc.body,
                "path": request.url.path,
            },
            headers={"Access-Control-Allow-Origin": allow, "Access-Control-Allow-Credentials": "true"},
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        print("=== EXCEPTION ===")
        print(traceback.format_exc())
        print("=== END EXCEPTION ===")
        origin = request.headers.get("origin")
        allow = origin if origin and (settings.DEBUG or origin in settings.cors_origins_list) else (
            "*" if settings.DEBUG else (settings.cors_origins_list[0] if settings.cors_origins_list else "*")
        )
        return JSONResponse(
            status_code=500,
            content={
                "detail": "Internal server error",
                "error": str(exc),
                "path": request.url.path,
            },
            headers={"Access-Control-Allow-Origin": allow, "Access-Control-Allow-Credentials": "true"},
        )
