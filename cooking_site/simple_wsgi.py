from urllib.parse import parse_qs

def application(environ, start_response):
    method = environ['REQUEST_METHOD']
    get = parse_qs(environ.get('QUERY_STRING', ''))
    post = parse_qs(environ['wsgi.input'].read(int(environ.get('CONTENT_LENGTH', 0))).decode()) if method == 'POST' else {}
    html = f'<h1>{method}</h1><pre>GET: {get}\nPOST: {post}</pre>'
    start_response('200 OK', [('Content-Type', 'text/html')])
    return [html.encode()]