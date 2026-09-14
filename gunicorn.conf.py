import os

# Gunicorn configuration file
# Automatically picked up by Gunicorn to override defaults
timeout = 180
workers = 1
threads = 4
bind = f"0.0.0.0:{os.environ.get('PORT', 5050)}"
