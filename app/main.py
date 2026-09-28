from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from app.utilities.enums import ErrorType
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


@app.exception_handler(RequestValidationError)
async def validation_error_rules(request: Request,
                                 exc: RequestValidationError):

    errors = exc.errors()

    for error in errors:
        if error['msg'].startswith(ErrorType.PRICE):
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"detail": error["msg"]}
            )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content={"detail": exc.errors()}
    )
