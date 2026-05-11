from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator
from app.database import engine, Base
from app.routes import patients, policies, claims

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Health Insurance API",
    description="Système de gestion d'assurance santé",
    version="1.0.0"
)

Instrumentator().instrument(app).expose(app)

app.include_router(patients.router)
app.include_router(policies.router)
app.include_router(claims.router)

@app.get("/")
def root():
    return {"message": "Health Insurance API", "version": "1.0.0"}

@app.get("/health")
def health():
    return {"status": "healthy", "service": "health-insurance-api"}
