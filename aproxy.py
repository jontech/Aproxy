import re
import asyncio
import urllib.parse
import io
import os
from string import Template
from datetime import datetime


class HTTPRequest:

    def __init__(self, message):
        (self.head,
         self.body) = message.split('\r\n\r\n')

        self.headers = dict(re.findall(r'(?P<name>.+): (?P<value>.+)\r\n', message))

        (self.method,
         self.url,
         self.proto) = message.splitlines()[0].split()
      
        self.url_parts = urllib.parse.urlsplit(self.url)
        self.query = dict(urllib.parse.parse_qsl(self.url_parts.query))

    @property
    def raw(self):
        sheaders = map(lambda x: '{}: {}'.format(x[0], x[1]), self.headers.items())
        message = ' '.join([self.method, self.url, self.proto]) + '\r\n' + '\r\n'.join(sheaders) + '\r\n\r\n' + self.body
        return message.encode('latin1')


class HTTPResponse:

    def __init__(self, code=200, reason='OK', body=''):
        self.status = 'HTTP/1.1 {} {}\r\n'.format(code, reason)
        self.body = body

    @property
    def raw(self):
        message = self.status  + '\r\n' + '\r\n\r\n' + self.body
        return message.encode('latin1')


stats_templ = Template("""
<html>
<head>
  <title>Aproxy stats</title>
</head>
<body>
  <h1>Aproxy / stats</h1>
  <hr>
  <table>
    <tr><td>Connections:</td><td>$conn</td></tr>
    <tr><td>Bytes:</td><td>$bytes</td></tr>
    <tr><td>Bad request:</td><td>$fail</td></tr>
    <tr><td>Up time:</td><td>$up</td></tr>
  </table>
</body>
</html>
""")


class HttpProxyProtocol(asyncio.Protocol):
    
    stats = {'conn': 0, 'bytes': 0, 'fail': 0}
    started = datetime.now()

    def _respond(self, message):
        self.transport.write(message)
        self.transport.close()

    @asyncio.coroutine
    def _forward(self, request):
        connection = asyncio.open_connection(request.url_parts.hostname, 80)
        reader, writer = yield from connection
        
        writer.write(request.raw)
        
        while not reader.at_eof():
            chunk = yield from reader.read(100)  # TODO env
            self.stats['bytes'] += len(chunk)
            if chunk:
                self.transport.write(chunk)  # response to client

        writer.close()
        self.transport.close()

    def connection_made(self, transport):
        peername = transport.get_extra_info('peername')
        print('Connection from {}'.format(peername))
        self.transport = transport
        self.stats['conn'] += 1

    def data_received(self, data):
        message = data.decode('latin1')
        request = HTTPRequest(message)

        if request.url_parts.path == '/aproxy/stats':
            self.stats['up'] = datetime.now() - self.started
            self._respond(HTTPResponse(body=stats_templ.safe_substitute(self.stats)).raw)
 
        else:
            if 'range' in request.query:
                range_param = request.query['range']

                if 'Range' in request.headers and  'bytes='+range_param != request.headers['Range']:
                    self._respond(HTTPResponse(416, 'Requested range not satisfiable').raw)
                    self.stats['fail'] += 1
                else:
                    request.headers['Range'] = 'bytes={}'.format(range_param)
                    asyncio.async(self._forward(request))
            else:
                asyncio.async(self._forward(request))

 
if __name__ == '__main__':
    loop = asyncio.get_event_loop()

    coro = loop.create_server(HttpProxyProtocol,
                              os.getenv('APROXY_HOST', '127.0.0.1'),
                              os.getenv('APROXY_PORT', 8888))

    server = loop.run_until_complete(coro)

    print('Running, CTRL-c to stop', server.sockets, sep='\n')
    
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass

    server.close()

    loop.run_until_complete(server.wait_closed())
    loop.close()
