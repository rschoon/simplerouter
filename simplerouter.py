"""
simplerouter is an expansion of DIY framework described in the
WebOB documentation.
    
"""

__version__ = '1.0'
__all__ = ['Router', 'lookup_view']

import sys
import re
from webob import exc, Request, Response

def blank_view(request):
    return Response()

def internal_error_view(msg):
    return lambda req: exc.HTTPInternalServerError(msg)

def not_found_view(request):
    return exc.HTTPNotFound()

PATH_INFO_VAR = '__path_info__'
VAR_REGEX = re.compile(r'{(\w+)(?::([^}]+))?\}')
def template_to_regex(template, path_info):
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
    if path_info is not None:
        if path_info is True:
            path_info = '/.*'
        regex += '(?P<%s>%s)' % (PATH_INFO_VAR, path_info)
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
    def __init__(self, path_re, viewname, vars=None, wsgi=False, no_alt_redir=False, priority=0, path_info=None):
        if path_re is not None:
            self.path_re = template_to_regex(path_re, path_info)
        else:
            self.path_re = re.compile("")

        if callable(viewname):
            self.view = viewname
            if hasattr(self.view, "__name__"):
                self.viewname = self.view.__name__
            elif hasattr(self.view, "__class__"):
                self.viewname = self.view.__class__.__name__
        else:
            self.viewname = viewname

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
            script_name_orig = request.script_name
            path_info_orig = request.path_info

            urlvars = m.groupdict()
            if PATH_INFO_VAR in urlvars:
                del urlvars[PATH_INFO_VAR]
                begin, end = m.span(PATH_INFO_VAR)
                request.script_name += request.path_info[:begin]
                request.path_info = request.path_info[begin:end]

            request.urlvars = urlvars
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
                resp = view(request)
                if resp is None:
                    request.script_name = script_name_orig
                    request.path_info = path_info_orig
                return resp

class Router(object):
    def __init__(self, routes=None, default=not_found_view, try_slashes=False):
        # Note: keep routes=None first

        if default is not None:
            self.default = Route(None, default)
        else:
            self.default = None
        self.try_slashes = try_slashes

        self.routes = []
        if routes is not None:
            for route in routes:
                if isinstance(route[-1], dict):
                    self.add_route(*route[:-1], **route[-1])
                else:
                    self.add_route(*route)

    def add_route(self, *args, **kwargs):
        """Add a route to the router."""
        route = Route(*args, **kwargs)
        for i, rti in enumerate(self.routes):
            if rti.priority < route.priority:
                self.routes.insert(i, route)
                return
        
        self.routes.append(route)
        
    def __call__(self, req):
        """Invoke router as a view."""
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
        
        if self.default is not None: 
            return self.default(req)
        
    def match(self, req, alt=False):
        """Return the first view that the given request matches."""
        for m in self.matches(req, alt):
            return m 

    def matches(self, req, alt=False):
        """Iterate through all views that the given request matches."""
        for route in self.routes:
            m = route.match(req, alt=alt)
            if m:
                if callable(m):
                    yield m
                else:
                    yield route

    def as_wsgi(self, environ, start_response):
        """Invoke router as an wsgi application."""
        req = Request(environ)
        resp = self(req)
        if resp is None:
            start_response('500 Internal Server Error', [('Content-Type', 'text/plain')])
            return [b'no default in wsgi call']
        return resp(environ, start_response)

