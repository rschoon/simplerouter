
import sys
import re
from webob import exc, Response

__all__ = ['Router', 'lookup_view']

def internal_error_view(msg):
    return lambda req: exc.HTTPInternalServerError(msg)
NotFoundView = lambda req: exc.HTTPNotFound()

VAR_REGEX = re.compile(r'{(\w+)(?::([^}]+))?\}')
def template_to_regex(template):
    regex = ''
    last_pos = 0
    for match in VAR_REGEX.finditer(template):
        regex += re.escape(template[last_pos:match.start()])
        var_name = match.group(1)
        expr = match.group(2) or '[^/]+'
        expr = '(?P<%s>%s)' % (var_name, expr)
        regex += expr
        last_pos = match.end()
    regex += re.escape(template[last_pos:])
    regex = '^%s$' % regex
    return re.compile(regex)

def lookup_view(fullname):
    module_name, func_name = fullname.split(':', 1)
    try:
        __import__(module_name)
    except ImportError:
        return internal_error_view("Module %s does not exist."%module_name)

    module = sys.modules[module_name]
    try:
        return getattr(module, func_name)
    except AttributeError:
        return internal_error_view("Function %s not found on module %s"%(func_name, module_name))

class Route(object):
    def __init__(self, path_re, viewname, vars=None, wsgi=False, no_alt_redir=False, priority=0):
        if path_re is not None:
            self.path_re = template_to_regex(path_re)
        else:
            self.path_re = re.compile("")

        self.viewname = viewname
        if callable(self.viewname):
            self.view = self.viewname
            self.viewname = self.view.__name__

        self.vars = vars
        self.wsgi = wsgi
        self.no_alt_redir = no_alt_redir
        self.priority = priority

    def __repr__(self):
        return "<Route(%s @ %s)>"%(self.viewname, self.path_re.pattern)

    def match(self, request, alt=False):
        if alt and self.no_alt_redir:
            return False          
        return self.path_re.match(request.path_info)

    def __call__(self, request):
        m = self.match(request)
        if m is not None:
            request.urlvars = m.groupdict()
            if self.vars is not None:
                request.urlvars.update(self.vars)
            
            try:
                view = self.view
            except AttributeError:
                view = lookup_view(self.viewname)
                self.view = view
            
            if self.wsgi:
                return view
            else:
                return view(request)

class Router(object):
    def __init__(self, default=NotFoundView, try_slashes=False):
        self.routes = []
        self.default = default
        self.try_slashes = try_slashes

    def add_route(self, *args, **kwargs):
        route = Route(*args, **kwargs)
        for i, rti in enumerate(self.routes):
            if rti.priority < route.priority:
                self.routes.insert(i, route)
                return
        
        self.routes.append(route)
        
    def __call__(self, req):
        # try normal view
        matches = set()
        for view in self.matches(req):
            if view is not None:
                r = view(req)
                if r is not None:
                    return r
                matches.add(view)
        
        # try redirect to alternate path
        if self.try_slashes:
            if req.environ['PATH_INFO'].endswith("/"):
                req.environ['PATH_INFO'] = req.environ['PATH_INFO'][:-1]
            else:
                req.environ['PATH_INFO'] += "/"
            
            altView = self.match(req, True)
            if altView is not None and altView not in matches:
                return exc.HTTPTemporaryRedirect(location=req.url)
                
        return self.default(req)
        
    def match(self, req, alt=False):
        for m in self.matches(req, alt):
            return m 

    def matches(self, req, alt=False):
        for route in self.routes:
            m = route.match(req, alt=alt)
            if m:
                if callable(m):
                    yield m
                else:
                    yield route
