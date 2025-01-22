# Gunicorn settings
# https://docs.gunicorn.org/en/stable/configure.html#configuration-file
# https://docs.gunicorn.org/en/stable/settings.html

import multiprocessing
import os

bind = os.getenv('GUNICORN_BIND', "127.0.0.1:8000")
workers = int(os.getenv("GUNICORN_WORKERS", multiprocessing.cpu_count() * 2 + 1))
capture_output = bool(os.getenv("GUNICORN_CAPTURE_OUTPUT", True))
loglevel = os.getenv("GUNICORN_LOGLEVEL", "INFO")
accesslog = os.getenv("GUNICORN_ACCESSLOG")
errorlog = os.getenv("GUNICORN_ERRORLOG", "-")
