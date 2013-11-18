
from webob import Request, Response, exc
from nose.tools import eq_

class view_factory(object):
    def __init__(self, payload):
        self.payload = payload

    def __call__(self, request):
        if len(request.urlvars) > 0:
            return self.payload, request.urlvars
        return self.payload

#
# Simple Tests
#

def test_func_view():
    from simplerouter import Router

    def view(request):
        return "hello!"

    r = Router()
    r.add_route('/test', view)

    assert r(Request.blank('/test')) == "hello!"

def test_simple_paths():
    from simplerouter import Router

    r = Router()
    r.add_route('/', view_factory('root'))
    r.add_route('/path', view_factory('path'))
    r.add_route('/path/', view_factory('path_slash'))
    r.add_route('/path/{element}', view_factory('path_var'))

    eq_(r(Request.blank('/')), "root")
    eq_(r(Request.blank('/path')), "path")
    eq_(r(Request.blank('/path/')), "path_slash")
    eq_(r(Request.blank('/path/pie')) , ("path_var", {'element' : 'pie'}))

def test_default_default():
    from simplerouter import Router

    r = Router()
    eq_(r(Request.blank('/')).status_code, 404)
    eq_(r(Request.blank('/path')).status_code, 404)

def test_routes_arg():
    from simplerouter import Router

    r = Router([
        ('/', view_factory('root')),
        ('/path', view_factory('path')),
        ('/vars', view_factory('vars'), { 'vars' : { 'key' : 'value' } })
    ])

    eq_(r(Request.blank('/')), "root")
    eq_(r(Request.blank('/path')), "path")
    eq_(r(Request.blank('/vars')), ('vars', {'key':'value'}))

#
# WSGI Tests
#

def test_as_wsgi():
    from simplerouter import Router

    def call_app(app, path):
        return Request.blank(path).call_application(app)

    r = Router(default=None)
    r.add_route('/', lambda req: Response("root"))
    r.add_route('/path', lambda req: Response("path"))

    statusRoot, headersRoot, bodyRoot = call_app(r.as_wsgi, '/')
    assert statusRoot.startswith('200')
    eq_(b''.join(bodyRoot), b'root')

    statusRoot, headersRoot, bodyRoot = call_app(r.as_wsgi, '/path')
    assert statusRoot.startswith('200')
    eq_(b''.join(bodyRoot), b'path')

    statusInvalid, headersInvalid, bodyInvalid = call_app(r.as_wsgi, '/invalid')
    assert statusInvalid.startswith('500')

def test_wsgi_view():
    from simplerouter import Router

    def call_app(app, path):
        return Request.blank(path).call_application(app)

    def app(environ, start_response):
        start_response('200 OK', [('Content-Type', 'text/plain')])
        return [environ['PATH_INFO'].encode('utf-8')]

    r = Router()
    r.add_route('/', view_factory('root'))
    r.add_route('/app', app, wsgi=True)

    statusAppRoot, headersAppRoot, bodyAppRoot = call_app(r.as_wsgi, '/app/')
    assert statusAppRoot.startswith('200')
    eq_(b''.join(bodyAppRoot), b'/')
    
    statusAppRoot, headersAppRoot, bodyAppRoot = call_app(r.as_wsgi, '/app/sub')
    assert statusAppRoot.startswith('200')
    eq_(b''.join(bodyAppRoot), b'/sub')

#
# Regexes
#

def test_null():
    from simplerouter import Router

    r = Router()
    r.add_route(None, view_factory('catchall'))
    r.add_route('/', view_factory('something'), priority=1)

    eq_(r(Request.blank('/')), 'something')
    eq_(r(Request.blank('/x')), 'catchall')

def test_regex():
    from simplerouter import Router

    r = Router()
    r.add_route('/{d:\d+}', view_factory('digit'))
    r.add_route('/{d:\d+}/', view_factory('digitSlash'))
    r.add_route('/term/{t:[^_]+}', view_factory('incSlash'))

    eq_(r(Request.blank('/1234')), ('digit', {'d' : '1234'}))
    eq_(r(Request.blank('/1234/')), ('digitSlash', {'d' : '1234'}))
    eq_(r(Request.blank('/term/abc/def')), ('incSlash', {'t' : 'abc/def'}))

#
# Try Slash Tests
#

def test_wrong_slash():
    from simplerouter import Router

    r = Router(default=view_factory('wrong'))
    r.add_route('/path', view_factory('path'))

    r2 = Router(default=view_factory('wrong'))
    r2.add_route('/path/', view_factory('path'))

    eq_(r(Request.blank('/path')), "path")
    eq_(r2(Request.blank('/path/')), "path")
    eq_(r(Request.blank('/path/')), "wrong")
    eq_(r2(Request.blank('/path')), "wrong")

def test_wrong_slash_try_slashes():
    from simplerouter import Router

    r = Router(default=view_factory('wrong'), try_slashes=True)
    r.add_route('/path', view_factory('path'))

    r2 = Router(default=view_factory('wrong'), try_slashes=True)
    r2.add_route('/path/', view_factory('path'))

    eq_(r(Request.blank('/path')), "path")
    eq_(r2(Request.blank('/path/')), "path")

    respRedir = r(Request.blank('/path/'))
    eq_(respRedir.status_code, 307)
    eq_(respRedir.location, "http://localhost/path")

    respRedir = r2(Request.blank('/path'))
    eq_(respRedir.status_code, 307)
    eq_(respRedir.location, "http://localhost/path/")

def test_no_try_slash():
    from simplerouter import Router

    r = Router(try_slashes=True)
    r.add_route('/path', view_factory('path'), no_alt_redir=True)
    
    eq_(r(Request.blank('/path/')).status_code, 404)

#
# Priority Tests
#

def test_priority():
    from simplerouter import Router

    r = Router()
    r.add_route('/1', view_factory('low'), priority=-1)
    r.add_route('/1', view_factory('normal'))
    eq_(r(Request.blank('/1')), "normal")

    r.add_route('/2', view_factory('normal'))
    r.add_route('/2', view_factory('low'), priority=-1)
    eq_(r(Request.blank('/2')), "normal")

    r = Router()
    r.add_route('/3', view_factory('high'), priority=1)
    r.add_route('/3', view_factory('normal'))
    r.add_route('/3', view_factory('low'), priority=-1)
    eq_(r(Request.blank('/3')), "high")

#
# View lookup tests
#

def test_failed_lookup():
    from simplerouter import Router

    r = Router()
    r.add_route('/missingModule', 'nonexistent.invalid:view')
    r.add_route('/missingView', 'simplerouter:xxx_nonexistent_view')

    resp = r(Request.blank('/missingModule'))
    eq_(resp.status_code, 500)
    
    resp = r(Request.blank('/missingView'))
    eq_(resp.status_code, 500)

def test_named():
    from simplerouter import Router

    r = Router()
    r.add_route('/blank', 'simplerouter:blank_view')
    eq_(r(Request.blank('/blank')).body, b'')

def test_default_named():
    from simplerouter import Router

    r = Router(default='simplerouter:blank_view')
    eq_(r(Request.blank('/')).body, b'')

#
# Path adjustment tests
#

def test_path_info():
    from simplerouter import Router

    def view(req):
        return req.script_name, req.path_info
    
    r = Router()
    r.add_route('/test', view, path_info=True)
    r.add_route('/slash/', view, path_info='.*') # not a good path_info
    
    eq_(r(Request.blank('/test/pants')), ('/test', '/pants'))
    eq_(r(Request.blank('/slash/test')), ('/slash/', 'test'))
    eq_(r(Request.blank('/test')).status_code, 404)

def test_path_info_restore():
    from simplerouter import Router

    def nullview(req):
        return None

    def view(req):
        return req.script_name, req.path_info

    r = Router()
    r.add_route('/test', nullview, path_info=True, priority=100)
    r.add_route('/test/2', view)
    
    eq_(r(Request.blank('/test/2')), ('', '/test/2'))
