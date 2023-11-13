from django.utils.deprecation import MiddlewareMixin
from rest_framework.response import Response


#  Middleware to count the number of requests made to the application
class RequestCounterMiddleware(MiddlewareMixin):
    request_count = 0

    def __init__(self, get_response):
        self.get_response = get_response

    # logic to perform when a request is made and middleware is called
    def __call__(self, request):
        RequestCounterMiddleware.request_count += 1
        response = self.get_response(request)
        response['X-Request-Count'] = str(self.request_count)
        return response


# reset the count of the requests made to the application
def reset_request_count(request):
    if request.method == 'POST':
        RequestCounterMiddleware.request_count = 0
        return Response({"Message": "Request count reset successfully"})
    else:
        return Response({"Error": "Bad Request"})
