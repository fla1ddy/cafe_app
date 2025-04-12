from fastapi import FastAPI

from producer.routers.auth import router as auth_router
from producer.routers.admin import router as admin_router
from producer.routers.cafe_admin import router as cafe_admin_router
from producer.routers.student import router as student_router
from producer.routers.group_head import router as group_head_router
from producer.routers.guest import router as guest_router
from producer.core.rabbitmq import rabbitmq_manager

app = FastAPI()

app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(cafe_admin_router)
app.include_router(student_router)
app.include_router(group_head_router)
app.include_router(guest_router)

@app.on_event("startup")
async def startup():
    await rabbitmq_manager.connect()
    print("Connected to RabbitMQ")

@app.on_event("shutdown")
async def shutdown():
    await rabbitmq_manager.close()
    print("Connection with RabbitMQ was closed")

@app.get("/")
async def read_root():
    return {"message": "FastAPI приложение работает и подключено к RabbitMQ"}


