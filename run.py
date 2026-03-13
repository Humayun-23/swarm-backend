"""
Application Runner
Entry point for running the Event Logistics Swarm application
"""
import uvicorn
from app.config import settings
print(settings.DATABASE_URL)


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
        access_log=True
    )