
simplerouter
============

simplerouter is an expansion of DIY framework described in the
WebOB documentation.

Quick Example
-------------

app.py::

    from simperouter import Router

    router = Router()
    router.add_route('/post/{name}', 'views:post_view')
    router.add_route('/', 'views:index_view')

    application = router.as_wsgi

    if __name__=='__main__':
        from wsgiref.simple_server import make_server
        make_server('', 8000, application).server_forever()

views.py::

    from webob import Response

    def post_view(request):
        post_name = request.urlvars['name']
        # ... process post name ...
        return Response("Post output")

    def index_view(request):
        return Response("Site index")


Router
------

XXX Talk about things
