from fastapi import FastAPI
from routes import games, analysis
from contextlib import asynccontextmanager
from jobs import scheduler

@asynccontextmanager
async def lifespan(app):
    print("Schedular starting...")
    scheduler.start()
    yield    
    scheduler.shutdown()   

app = FastAPI(lifespan=lifespan)
app.include_router(games.router)
app.include_router(analysis.router)