# from fastapi.responses import JSONResponse
# from app import app
# class apierror(Exception): ## Here we made this custome exception
#     def __init__(self, message:str,statusCode:int):
#         self.message = message
#         self.statusCode = statusCode

# @app.exception_handler(apierror) ## we created the exception handler which is compatable with the fast api
# async def app_error(req,exc):
#     return JSONResponse(
#         status_code=exc.code,
#         content={"error": exc.message}
#     )

# use Httpexception in build by fast api
