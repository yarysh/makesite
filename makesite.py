#!/usr/bin/env python3


import argparse
import os
import sys


NGINX_CONF_PATH = '/etc/nginx'
NGINX_LOG_PATH = '/var/log/nginx'
NGINX_WWW_PATH = '/var/www'


DEFAULT_NGINX_HTML_CONF = """
server {{
    listen 80;

    server_name {name} www.{name};
    root /var/www/{name};

    access_log /var/log/nginx/{name}/access.log;
    error_log /var/log/nginx/{name}/error.log warn;
    
    gzip on;
    gzip_vary on;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types text/plain text/css text/xml application/json application/javascript application/rss+xml application/atom+xml image/svg+xml;

    # security
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;

    # . files
    location ~ /\.(?!well-known) {{
        deny all;
    }}

    location / {{
        try_files $uri $uri/ /index.html;
    }}
}}
"""


def _make_html_site(name: str):
    sa_conf = os.path.join(NGINX_CONF_PATH, 'sites-available', name)
    se_conf = os.path.join(NGINX_CONF_PATH, 'sites-enabled', name)
    www_path = os.path.join(NGINX_WWW_PATH, name)
    log_path = os.path.join(NGINX_LOG_PATH, name)

    for path in [sa_conf, se_conf, www_path, log_path]:
        if os.path.exists(path):
            print("ERROR: path %s - already exists")
            sys.exit(1)

    print('Creating content dir', end='\r')
    os.mkdir(www_path)
    with open(os.path.join(www_path, 'index.html'), 'w') as f:
        f.write(name)
    print(' - DONE!')

    print('Creating log dir', end='\r')
    os.mkdir(log_path)
    print(' - DONE!')

    print('Creating sites-available config', end='\r')
    with open(sa_conf, 'w') as f:
        f.write(DEFAULT_NGINX_HTML_CONF.format(name=name))
    print(' - DONE!')

    print('Creating symlink on sites-enabled', end='\r')
    os.symlink(sa_conf, se_conf)
    print(' - DONE!')

    print('All done! Now you can restart your nginx server')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('name', help='Name of website. Folders with this name will be created.')
    parser.add_argument('--type', default='html', choices=['html'], help='Type of website')
    args = parser.parse_args()

    if args.type == 'html':
        _make_html_site(args.name)
    else:
        print("ERROR: path %s - already exists")
        sys.exit(1)


if __name__ == '__main__':
    main()
