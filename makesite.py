#!/usr/bin/env python3


import argparse
from datetime import datetime
import os
import sys
import subprocess


CERTBOT_PATH = '/usr/bin/certbot'

NGINX_CONF_PATH = '/etc/nginx'
NGINX_LOG_PATH = '/var/log/nginx'
NGINX_WWW_PATH = '/var/www'


DEFAULT_NGINX_HTML_CONF = """server {{
    listen 80;
    listen [::]:80;

    server_name {name} www.{name};
    root /var/www/{name};

    access_log /var/log/nginx/{name}/access.log;
    error_log /var/log/nginx/{name}/error.log warn;

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

DEFAULT_NGINX_SSL_HTML_CONF = """server {{
    listen 443 ssl http2;
    listen [::]:443 ssl http2;

    server_name {name} www.{name};
    root /var/www/{name};

    access_log /var/log/nginx/{name}/access.log;
    error_log /var/log/nginx/{name}/error.log warn;

    #ssl
    ssl_certificate /etc/letsencrypt/live/{name}/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/{name}/privkey.pem;
    ssl_trusted_certificate /etc/letsencrypt/live/{name}/chain.pem;

    # security
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;

    # . files
    location ~ /\.(?!well-known) {{
        deny all;
    }}

    location / {{
        try_files $uri $uri/ /index.html;
    }}
}}

server {{
    listen 80;
    listen [::]:80;

    server_name {name} www.{name};

    # . files
    location ~ /\.(?!well-known) {{
        deny all;
    }}

    location / {{
        return 301 https://{name}$request_uri;
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
            print('ERROR: path %s - already exists' % name)
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


def _obtain_cert(name: str, email: str):
    se_conf = os.path.join(NGINX_CONF_PATH, 'sites-enabled', name)
    if not os.path.exists(se_conf):
        print('ERROR: unknown website %s' % name)
        sys.exit(1)

    print('Obtaining letsencrypt certificate', end='\r')
    result = subprocess.run([
        CERTBOT_PATH, 'certonly', '--nginx', '-m', email, '--agree-tos', '-d', name, '-d', 'www.' + name,
    ])
    if result.returncode != 0:
        print("ERROR: can't obtain certificate, error: %s" % result.stderr)
        sys.exit(1)
    print(' - DONE!')

    print('Updating sites-available config', end='\r')
    content = DEFAULT_NGINX_SSL_HTML_CONF.format(name=name)
    with open(se_conf, 'r') as f:
        content += '\n\n#=== Backup - %s ===\n' % datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        for line in f.readlines():
            content += "#%s" % line
    with open(se_conf, 'w') as f:
        f.write(content)
    print(' - DONE!')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('name', help='Name of website. Folders with this name will be created.')
    parser.add_argument('--type', default='html', choices=['html'], help='Type of website')
    parser.add_argument('--get_cert', nargs='?', default=False, const=True, help='Obtain certificate for website')
    parser.add_argument('--cert_email', help='Email for urgent renewal and security notices')
    args = parser.parse_args()

    if args.get_cert:
        if not args.cert_email:
            print('ERROR: parameter --cert_email is required')
            sys.exit(1)
        _obtain_cert(args.name, args.cert_email)
    elif args.type == 'html':
        _make_html_site(args.name)
    else:
        print('ERROR: path %s - already exists' % args.name)
        sys.exit(1)
    print('All done! Now you can restart your nginx server')


if __name__ == '__main__':
    main()
