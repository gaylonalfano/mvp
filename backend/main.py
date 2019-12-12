from fastapi import FastAPI

from core.routes import core_router
from pets.routes import pets_router
from config import config

api_path = f"/api/{config.API_VERSION}"

app = FastAPI(
    title="Rescaty",
    description="""
    App resemble a social network where a user can adopt
    a pet and follow pets stories, and receive updates about it.
    """,
    version="0.1",
    openapi_url=f"{api_path}/openapi.json",
    docs_url=f"{api_path}/docs",
    redoc_url=None
)

app.include_router(
    pets_router,
    prefix=f"{api_path}/pets",
    tags=["pets"],
    responses={404: {"description": "Not found"}},
)

app.include_router(
    core_router,
    tags=["core"],
    responses={404: {"description": "Not found"}},
)


@app.on_event("startup")
async def app_startup():
    """
    Do tasks related to app initialization.
    """
    # This if fact does nothing its just an example.
    config.load_config()


@app.on_event("shutdown")
async def app_shutdown():
    """
    Do tasks related to app termination.
    """
    # This does finish the DB driver connection.
    config.close_db_client()
