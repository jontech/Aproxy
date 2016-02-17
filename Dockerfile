FROM python:3-onbuild
WORKDIR /usr/src/app
CMD python aproxy.py
ENV APROXY_HOST=0.0.0.0