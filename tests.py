
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