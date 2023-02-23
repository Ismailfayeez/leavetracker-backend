import jwt


class DummyMiddleware(object):
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_view(self, request, view_func, view_args, view_kwargs):
        if bool(request.META.get('HTTP_AUTHORIZATION')):
            token = request.META.get('HTTP_AUTHORIZATION').split()[1]
            data = jwt.decode(token, options={"verify_signature": False})
            if data.get('organization_id'):
                request.org_id = data.get('organization_id')
            # request.organization_id = token

        return None
