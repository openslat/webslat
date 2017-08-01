from django.utils.deprecation import MiddlewareMixin
from django.http import HttpResponseForbidden

class FilterHostMiddleware(MiddlewareMixin):

    def process_request(self, request):
        allowed_hosts = ['127.0.0.1', 'localhost']  # specify complete host names here
        host = request.META.get('HTTP_HOST')

        if host[:10] == '127.0.0.1:': # Local host, with port number
            allowed_hosts.append(host)
        elif host[:10] == 'localhost:':  # Local host, with port number
            allowed_hosts.append(host)
        elif host[:7] == '132.181':  # UC address
            allowed_hosts.append(host)

        print(host)
        print(allowed_hosts)

        if host not in allowed_hosts:
            print("NOT ALLOWED")
            return HttpResponseForbidden()

        return None
