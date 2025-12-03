from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router
from app.utils.logger import get_logger
from contextlib import asynccontextmanager
from app.core.database import create_db_and_tables
logger = get_logger("API_Main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up: Initializing Database...")
    create_db_and_tables()
    logger.info("Database ready.")
    yield
    logger.info("Shutting server down")

app = FastAPI(
    title="AI Integration Agent API",
    lifespan=lifespan
)

# origins = {}
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routes
app.include_router(router, prefix="/api")


@app.get("/")
def health_check():
    return {"status": "running", "service": "Integration Agent"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
