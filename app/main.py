from fastapi import FastAPI

from app.routers import categories, products, users, login, review


app = FastAPI(
    title="Fastapi internet store",
    version="0.1.0"
)

app.include_router(categories.router)
app.include_router(products.router)
app.include_router(users.router)
app.include_router(login.router)
app.include_router(review.router)


@app.get("/")
async def root():

    return {"message": "welcome to our store"}
