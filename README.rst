
simplerouter
============

simplerouter is a simple WSGI/WebOb router partially based on
the router described in `WebOB's DIY Framework Tutorial
<http://docs.webob.org/en/latest/do-it-yourself.html>`_.
Python 2.7 and Python 3.2 and newer are supported.

Documentation is available at `readthedocs.org
<http://simplerouter.readthedocs.org/en/latest/>`_.

The main git repository is available at `Bitbucket
<https://bitbucket.org/rschoon/simplerouter>`_.


Installing
----------

simplerouter uses a setup.py script in the usual fashion, like so::

    $ python ./setup.py install

Alternately, simplerouter is available on pypi and can be installed
using pip::

    $ pip install simplerouter


Quick Example
-------------

app.py:

.. code-block:: python

    from simplerouter import Router

    router = Router()
    # view names are composed of modulename:function
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
