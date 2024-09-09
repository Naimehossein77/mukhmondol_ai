from fastapi import FastAPI
from app.user_routes import router as user_router
from app.photographer_routes import router as photographer_router
from app.firebase import initialize_firebase

app = FastAPI()

# Initialize Firebase
initialize_firebase()

# Include routers
app.include_router(user_router, prefix="/users")
app.include_router(photographer_router, prefix="/photographers")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
