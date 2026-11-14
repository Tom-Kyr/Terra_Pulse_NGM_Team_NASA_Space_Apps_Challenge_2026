from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.water import router as water_router
from routes.soil import router as soil_router
from routes.rotation import router as rotation_router
from routes.fire import router as fire_router

app = FastAPI(title="TerraPulse Intelligence API (Modular 4-Network Suite)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(water_router)
app.include_router(soil_router)
app.include_router(rotation_router)
app.include_router(fire_router)


@app.get("/")
def health_check():
    return {"status": "TerraPulse Backend Online", "networks": ["water", "soil", "rotation", "fire"]}