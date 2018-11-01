#!/bin/sh
gunicorn --worker-class gevent -w 1 --timeout 600 --log-level=debug --bind 127.0.0.1:5000 --certfile=ssl/cert.pem --keyfile=ssl/privkey.pem run:app
