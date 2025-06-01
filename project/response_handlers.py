from rest_framework.response import Response
from rest_framework import status
import logging

logger = logging.getLogger(__name__)


def success_response(data=None, message="Success", status_code=status.HTTP_200_OK):
    return Response({
        "status": "ok",
        "message": message,
        "data": data or {},
    }, status=status_code)


def error_response(message="Error", status_code=status.HTTP_400_BAD_REQUEST):
    logger.error(message, exc_info=True)
    return Response({
        "status": "error",
        "message": message,
        "data": {},
    }, status=status_code)
