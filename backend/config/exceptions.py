from rest_framework.views import exception_handler
from rest_framework.response import Response


class AppError(Exception):
    def __init__(self, message, status_code=400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


def custom_exception_handler(exc, context):
    if isinstance(exc, AppError):
        return Response({"error": exc.message}, status=exc.status_code)

    response = exception_handler(exc, context)

    if response is not None:
        if response.status_code == 404:
            response.data = {"error": "Not found"}
        elif response.status_code == 401:
            response.data = {"error": "Unauthorized"}
        elif response.status_code == 403:
            response.data = {"error": "Forbidden"}
        elif response.status_code == 400 and isinstance(response.data, dict):
            errors = {}
            for field, messages in response.data.items():
                if isinstance(messages, list):
                    errors[field] = str(messages[0])
                else:
                    errors[field] = str(messages)
            if len(errors) == 1:
                response.data = {"error": next(iter(errors.values()))}
            else:
                response.data = {"error": "Validation failed", "fields": errors}

    return response
