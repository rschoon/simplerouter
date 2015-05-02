"""
simplerouter is an expansion of DIY framework described in the
WebOB documentation.
    
"""

__version__ = '1.2'
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
def parse_template(template, path_info):
    fmt = []
    regex = []
    last_pos = 0

    for match in VAR_REGEX.finditer(template):
        regex.append(re.escape(template[last_pos:match.start()]))
        fmt.append(template[last_pos:match.start()])

        regex.append('(?P<%s>%s)' % (match.group(1), match.group(2) or '[^/]+'))
        fmt.append('{%s}'%(match.group(1), ))

        last_pos = match.end()

    regex.append(re.escape(template[last_pos:]))
    fmt.append(template[last_pos:])

    if path_info is not None:
        if path_info is True:
            path_info = '/.*'
        regex.append('(?P<%s>%s)' % (PATH_INFO_VAR, path_info))

    return re.compile('^%s$' % "".join(regex)), "".join(fmt)

def lookup_view(view):
    if callable(view):
        return view

    module_name, func_name = view.split(':', 1)
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
    def __init__(self, path_re, viewname, vars=None, wsgi=False, no_alt_redir=False, priority=0, path_info=None, method=None):
        if wsgi and path_info is None:
            path_info = True

        if path_re is not None or path_info is not None:
            if path_re is None:
                path_re = ""
            self.path_re, self.path_fmt = parse_template(path_re, path_info)
        else:
            self.path_fmt = None
            self.path_re = re.compile("")

        if callable(viewname):
            self._view = viewname
            if hasattr(self._view, "__name__"):
                self.viewname = self._view.__name__
            elif hasattr(self._view, "__class__"):
                self.viewname = self._view.__class__.__name__
        else:
            self.viewname = viewname

        self.vars = vars
        self.wsgi = wsgi
        self.no_alt_redir = no_alt_redir
        self.priority = priority

        if isinstance(method, str):
            self.method = (method, )
        else:
            self.method = method
        if self.method is not None and "GET" in self.method:
            self.method = list(self.method) + ["HEAD"]

    def __repr__(self):
        if self.method is None:
            method = ""
        else:
            method = "|".join(self.method)

        return "<Route(%s%s @ %s)>"%(method, self.viewname, self.path_re.pattern)

    def match(self, request, alt=False):
        if alt and self.no_alt_redir:
            return False
        if self.method is not None and request.method not in self.method:
            return False
        return self.path_re.match(request.path_info)

    @property
    def view(self):
        try:
            return self._view
        except AttributeError:
            pass
        view = lookup_view(self.viewname)
        self._view = view
        return view

    def __call__(self, request):
        m = self.match(request)
        if m is not None:
            script_name_orig = request.script_name
            path_info_orig = request.path_info
            urlvars_orig = request.urlvars

            urlvars = m.groupdict()
            if PATH_INFO_VAR in urlvars:
                del urlvars[PATH_INFO_VAR]
                begin, end = m.span(PATH_INFO_VAR)
                request.script_name += request.path_info[:begin]
                request.path_info = request.path_info[begin:end]

            request.urlvars = urlvars
            if self.vars is not None:
                request.urlvars.update(self.vars)

            if self.wsgi:
                return self.view
            else:
                resp = self.view(request)
                if resp is None:
                    request.script_name = script_name_orig
                    request.path_info = path_info_orig
                    request.urlvars = urlvars_orig
                return resp

class Router(object):
    def __init__(self, *routes, **options):
        self._set_options(**options)

        self.routes = []
        for route in routes:
            if isinstance(route[-1], dict):
                self.add_route(*route[:-1], **route[-1])
            else:
                self.add_route(*route)

    def _set_options(self, default=not_found_view, try_slashes=False, catch_raised_responses=True):
        if default is not None:
            self.default = lookup_view(default)
        else:
            self.default = None
        self.try_slashes = try_slashes
        self.catch_raised_responses = catch_raised_responses

    def add_route(self, path, view, **kwargs):
        """Add a route to the router."""
        if isinstance(view, (list, tuple)):
            if isinstance(view[-1], dict):
                view = Router(*view[:-1], **view[-1])
            else:
                view = Router(*view)

        route = Route(path, view, **kwargs)
        for i, rti in enumerate(self.routes):
            if rti.priority < route.priority:
                self.routes.insert(i, route)
                return
        
        self.routes.append(route)
        
    def __call__(self, req):
        """Invoke router as a view."""

        # verify url was decoded properly
        try:
            req.path_info, req.script_name
        except (UnicodeDecodeError, UnicodeEncodeError):
            return exc.HTTPBadRequest()

        # try normal view
        matches = set()
        for view in self.matches(req):
            if view is not None:
                try:
                    r = view(req)
                except exc.HTTPException as respexc:
                    if not self.catch_raised_responses:
                        raise
                    return respexc
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

    def _find_route_by_identifier(self, route):
        """Find a route by its name or callable or itself."""
        if isinstance(route, Route):
            return route
        elif isinstance(route, str):
            for r in self.routes:
                if r.viewname == route:
                    return r
        elif callable(route):
            for r in self.routes:
                if r.view == route:
                    return r
        else:
            raise TypeError("Expected a string or route callable, but got `%s' instead", type(route).__name__)
        raise ValueError("No such route %r"%(route, ))

    def reverse(self, route, vars={}, path_info=None):
        route = self._find_route_by_identifier(route)
        if route.path_fmt is None:
            raise ValueError("%r cannot be reversed"%(route, ))

        url = route.path_fmt.format(**vars)
        if path_info is not None:
            url += path_info
        return url

    def as_wsgi(self, environ, start_response):
        """Invoke router as an wsgi application."""
        req = Request(environ)
        resp = self(req)
        if resp is None:
            start_response('500 Internal Server Error', [('Content-Type', 'text/plain')])
            return [b'no default in wsgi call']
        return resp(environ, start_response)

