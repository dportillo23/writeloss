from fastapi import FastAPI
from routers.auth.auth_user import router as auth_router

app = FastAPI()
app.include_router(router=auth_router)

@app.get('/')
async def root():
    return {'message': 'It works'}