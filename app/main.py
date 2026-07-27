from fastapi import FastAPI, Depends
from fastapi.openapi.docs import get_redoc_html, get_swagger_ui_html
from fastapi.openapi.utils import get_openapi

from app.users.router import router as users_router
from app.users.schemas import UserGroup
from app.core.security import require_group

app = FastAPI(
    title="Cinema API",
    version="1.0.0",
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)

app.include_router(users_router)

# only admins
docs_guard = require_group(UserGroup.ADMIN.value)


@app.get("/openapi.json", include_in_schema=False)
def openapi(_: object = Depends(docs_guard)) -> dict:
    return get_openapi(
        title=app.title,
        version=app.version,
        routes=app.routes,
    )


@app.get("/docs", include_in_schema=False)
def swagger_ui(_: object = Depends(docs_guard)):
    return get_swagger_ui_html(
        openapi_url="/openapi.json",
        title=f"{app.title} - Swagger UI",
    )


@app.get("/redoc", include_in_schema=False)
def redoc(_: object = Depends(docs_guard)):
    return get_redoc_html(
        openapi_url="/openapi.json",
        title=f"{app.title} - ReDoc",
    )
