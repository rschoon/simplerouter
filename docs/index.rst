
simplerouter
============

simplerouter is an expansion of the DIY framework described in the
WebOB documentation.

Quick Example
-------------

app.py:

.. code-block:: python

    from simplerouter import Router

    router = Router()
    router.add_route('/post/{name}', 'views:post_view')
    router.add_route('/', 'views:index_view')

    application = router.as_wsgi

    if __name__=='__main__':
        from wsgiref.simple_server import make_server
        make_server('', 8000, application).serve_forever()

views.py:

.. code-block:: python

    from webob import Response

    def post_view(request):
        post_name = request.urlvars['name']
        # ... process post_name
        return Response("Post output for %s"%post_name)

    def index_view(request):
        return Response("Site index")


Adding Routes
-------------

The ``Router`` object is composed of mappings of paths to views
called routes, and are added using the ``Router.add_route()``
method.  The route path is matched against the ``Request``'s 
``path_info`` [#pathinfo]_ variable, and the view is either a callable, or
a string indicating the location of a callable in
``module_name:callable_name`` format.   

.. code-block:: python

    router.add_route('/path', viewfunc)
    router.add_route('/path', 'module.views:named_view')

Route paths may contain variables, which are indicated by curly braces:

.. code-block:: python

    router.add_route('/path/{variable}/extra', viewfunc)

By default, variables will match any string not containing a forward
slash. Alternatively, variables can match more or less restrictively
by providing a colon and a regular expression after the variable name:

.. code-block:: python

    router.add_route(r'/path/{variable:\d+}', viewfunc)

Any variables specified in the route path can be accessed in a
dictionary attached to the ``Request`` object called ``urlvars``:

.. code-block:: python

    def viewfunc(request):
        return Response(request.urlvars['var1'])

    router.add_route('/path/{var1}/{var2}', viewfunc)

Variables may also be provided via the vars keyword to
``Router.add_route()``, which will cause them to appear in the ``urlvars``
dictionary.  This could be useful if a view expects them but the route
path doesn't contain them:

.. code-block:: python

    route.add_route('/list', viewfunc, vars={'page' : 1})

.. [#pathinfo] The path portion of a URL (the portion of the URL after the
    domain name) is further split into two parts called ``script_name``
    and ``path_info``.  The ``script_name`` portion of URL indicates the path
    that is directly associated with the web application, and the
    ``path_info`` portion is the part of the URL after it.  For a web
    application that is associated with an entire domain, the ``script_name``
    would be blank, and the ``path_info`` would be the entire url path.
    It is the ``path_info`` that the ``Router`` object matches route
    paths against.

Using a Router
--------------

Under typical circumstances, you may want to construct the ``Request``
object from the WSGI environ yourself, and then call the ``Router``
as a callable with the request:

.. code-block:: python

    def application(environ, start_response):
        # create request object
        request = Request(environ)

        # invoke router
        response = router(request)

        # complete request
        return response(environ, start_response)        

Alternatively, the ``Router.as_wsgi`` method may be used to do this all
for you, so long as you don't need to do any extra processing and aren't
using the ``Router`` object within a larger framework:

.. code-block:: python

    application = router.as_wsgi


Advanced Options
----------------

Default View
............

By default, a ``Router`` will return WebOb's HTTPNotFound error response if
no view manages to return a valid response.  This behavior can be changed
by providing a different view via the ``default`` keyword to the
``Router`` initializer.

.. code-block:: python

    router = Router(default="module:error_view")


Trailing Slashes
................

If try_slashes is passed to the ``Router`` initializer, then the ``Router`` 
object will attempt to determine if a failed request would have instead
succeeded if the trailing slash on the url had instead been omitted or
provided.  If an alternate matching route is found, then a HTTP temporary
redirect response will be returned that will tell the user's browser to
use the correct URL.

.. code-block:: python

    router = Router(try_slashes=True)
    router.add_route('/path', viewfunc)
    response = router(Request.blank('/path/'))
    # response will be a redirect

If this option is used, it's a good idea to make sure that any views
that are capable of returning ``None`` should opt out of this check
by setting ``no_alt_redir`` in the ``Router.add_route`` registration
function:

.. code-block:: python

    router.add_route('/path', viewfunc, no_alt_redir=True)

Under certain circumstances failure to handle this could result in an infinite redirect loop, which is why ``try_slashes`` is not default behavior.


View Priority
.............

Routes are checked in the order that they are added.  While this behavior
is not likely to change, it still might be desirable set the priority of
a route without altering the order that they are originally added, which
can be done by supplying the ``Router.add_route`` method with the
priority keyword:

.. code-block:: python

    Router.add_route('/path', viewfunc, priority=10)

Routes with higher number priorty values are matched against before routes
with lower number priority values.


WSGI Views
..........

A WSGI application can be provided as a view if the ``wsgi`` keyword is
provided to the ``Router.add_route`` method:

.. code-block:: python

    def app_view(environ, start_response):
        start_response('200 OK', [('Content-Type', 'text/plain')])
        return [b'hello, world\n']
    
    router.add_route('/hello', app_view, wsgi=True)


Further Reading
---------------

* `PEP3333 (WSGI Specification) <http://www.python.org/dev/peps/pep-3333/>`_
* `WebOb documentation <http://webob.readthedocs.org/en/latest/>`_
