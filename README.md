# aproxy
   Aproxy - basic HTTP asynchronous proxy server based on asyncio.

   Proxy server supports HTTP requests and Range headers/query and has stats page `/aproxy/stats`.


# Usage

   All you need is Python 3.4.1 to run proxy in terminal by typing `$ python3 aproxy.py` command.
You should be able to visit stats page at `localhost:8888/aproxy/stats`.

   Alternatively its possible to build Docker image `$ docker build .` (first cd where Dockerfile is)
and run it in container: `$ docker run -it --rm <image id/name>`.

   It is possible to set `APROXY_HOST` and `APROXY_PORT` using environment variables.


# Note

   This server is meant for learning purpose and software is provided WITHOUT WARRANTY OF ANY KIND.