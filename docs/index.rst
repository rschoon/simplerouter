
simplerouter
============

simplerouter is an expansion of DIY framework described in the
WebOB documentation.

Quick Example
-------------

app.py:

.. code-block:: python

    from simperouter import Router

    router = Router()
    router.add_route('/post/{name}', 'views:post_view')
    router.add_route('/', 'views:index_view')

    application = router.as_wsgi

    if __name__=='__main__':
        from wsgiref.simple_server import make_server
        make_server('', 8000, application).server_forever()

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

The ``Router`` object maps paths to views.  Routes are added view
the ``Router.add_route()`` method, which takes a path and a view.

.. code-block:: python

    router.add_route('/path', viewfunc)

A route path is matched against a ``Request``'s ``path_info``
variable, which is the portion of the url after the application
``script_name``.  Route paths may contain variables, which are
indicated by curly braces:

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

Views may be given as a callable, or as a ``module:funcname``
name, in which case a dotted notation ``module`` would be
loaded and searched for ``funcname``:

.. code-block:: python

    router.add_route('/path', 'module.views:named_view')


Using a Router
--------------

Under typical circumstances, you may want to construct the ``Request``
vobject from the WSGI environ yourself, and then call the ``Router``
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
provided.  If it is determined that this is the case, then a temporary
rederict response will be returned.

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
is not likely to change, it might be desirable set the priority of
a route without altering the order that they are originally added, which
can be done by supplying the ``Router.add_route`` method with the
priority keyword:

.. code-block:: python

    Router.add_route('/path', viewfunc, priority=10)

Routes with higher number priorty values are matched against before routes
with lower number priority values.


WSGI Views
..........

A WSGI application can be provided as a view if the `wsgi`` keyword is
provided to the ``Router.add_route`` method:

.. code-block:: python

    def app_view(environ, start_response):
        start_response('200 OK', [('Content-Type', 'text/plain')])
        return [b'hello, world\n']
    
    router.add_route('/hello', app_view, wsgi=True)
