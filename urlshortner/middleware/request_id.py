import uuid
import time
import logging
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)

class RequestIDMiddleware(MiddlewareMixin):

    def process_request(self,request):
        request.request_id = str(uuid.uuid4())
        request.start_time = time.time()

    def process_response(self,request,response):
        if hasattr(request,"start_time"):
            duration = time.time() - request.start_time

            logger.info(
                "request_completed",
                extra={
                    "request_id": getattr(request,"request_id",None),
                    "path": request.path,
                    "method": request.method,
                    "status_code": response.status_code,
                    "duration": round(duration * 1000,2),
                }
            )
        response["X-Request-ID"] = getattr(request,"request_id","")
        return response

    def process_exception(self, request, exception):
        logger.error(
            "request_failed",
            extra={
                "request_id": getattr(request, "request_id", None),
                "path":request.path,
                "method":request.method,
                "error":str(exception),
            }
        )
