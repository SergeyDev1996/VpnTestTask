import re
import requests
from bs4 import BeautifulSoup
from django.http import HttpResponse
from django.http import QueryDict
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

try:
    from urlparse import urlparse
except:
    from urllib.parse import urlparse, urljoin

from requests_html import HTMLSession


def proxy_viewbad(request, site_name, requests_args=None):
    """
    Forward as close to an exact copy of the request as possible along to the
    given url.  Respond with as close to an exact copy of the resulting
    response as possible.

    If there are any additional arguments you wish to send to requests, put
    them in the requests_args dictionary.
    """
    url = f"https://www.{site_name}"
    requests_args = (requests_args or {}).copy()
    headers = get_headers(request.META)
    params = request.GET.copy()

    if 'headers' not in requests_args:
        requests_args['headers'] = {}
    if 'data' not in requests_args:
        requests_args['data'] = request.body
    if 'params' not in requests_args:
        requests_args['params'] = QueryDict('', mutable=True)

    # Overwrite any headers and params from the incoming request with explicitly
    # specified values for the requests library.
    headers.update(requests_args['headers'])
    params.update(requests_args['params'])

    # If there's a content-length header from Django, it's probably in all-caps
    # and requests might not notice it, so just remove it.
    for key in list(headers.keys()):
        if key.lower() == 'content-length':
            del headers[key]

    requests_args['headers'] = headers
    requests_args['params'] = params

    response = requests.request(request.method, url, **requests_args)

    proxy_response = HttpResponse(
        response.content,
        status=response.status_code,
    content_type=response.headers['Content-Type'])
    print(1)
    excluded_headers = set([
        # Hop-by-hop headers
        # ------------------
        # Certain response headers should NOT be just tunneled through.  These
        # are they.  For more info, see:
        # http://www.w3.org/Protocols/rfc2616/rfc2616-sec13.html#sec13.5.1
        'connection', 'keep-alive', 'proxy-authenticate',
        'proxy-authorization', 'te', 'trailers', 'transfer-encoding',
        'upgrade',

        # Although content-encoding is not listed among the hop-by-hop headers,
        # it can cause trouble as well.  Just let the server set the value as
        # it should be.
        'content-encoding',

        # Since the remote server may or may not have sent the content in the
        # same encoding as Django will, let Django worry about what the length
        # should be.
        'content-length',
    ])
    for key, value in response.headers.items():
        if key.lower() in excluded_headers:
            continue
        elif key.lower() == 'location':
            # If the location is relative at all, we want it to be absolute to
            # the upstream server.
            proxy_response[key] = make_absolute_location(response.url, value)
        else:
            proxy_response[key] = value

    return proxy_response


def make_absolute_location(base_url, location):
    """
    Convert a location header into an absolute URL.
    """
    absolute_pattern = re.compile(r'^[a-zA-Z]+://.*$')
    if absolute_pattern.match(location):
        return location

    parsed_url = urlparse(base_url)

    if location.startswith('//'):
        # scheme relative
        return parsed_url.scheme + ':' + location

    elif location.startswith('/'):
        # host relative
        return parsed_url.scheme + '://' + parsed_url.netloc + location

    else:
        # path relative
        return parsed_url.scheme + '://' + parsed_url.netloc + parsed_url.path.rsplit('/', 1)[0] + '/' + location

    return location


def get_headers(environ):
    """
    Retrieve the HTTP headers from a WSGI environment dictionary.  See
    https://docs.djangoproject.com/en/dev/ref/request-response/#django.http.HttpRequest.META
    """
    headers = {}
    for key, value in environ.items():
        # Sometimes, things don't like when you send the requesting host through.
        if key.startswith('HTTP_') and key != 'HTTP_HOST':
            headers[key[5:].replace('_', '-')] = value
        elif key in ('CONTENT_TYPE', 'CONTENT_LENGTH'):
            headers[key.replace('_', '-')] = value
    return headers


def replace_css_url(css_content, base_url):
    # Define a regex pattern to match URLs in the CSS content
    pattern = re.compile(r'url\((["\']?)(.*?)\1\)')

    # Replace relative URLs with absolute URLs
    def replace_url(match):
        url = match.group(2)  # Extract the URL
        # Check if the URL is already absolute
        if not urlparse(url).scheme:
            url = urljoin(base_url, url)
        return f'url("{url}")'
    new_css_content = pattern.sub(replace_url, css_content)
    return new_css_content

def proxy_view(request, site_name):
    # Base URL of the site you are proxying
    base_url = f"https://www.{site_name}"
    headers = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36"
    }

    # Make the external HTTP request
    r = requests.get(base_url, headers=headers)
    print(1)
    # Parse the HTML content
    soup = BeautifulSoup(r.content, 'html.parser')
    # Handle img, script, and link tags
    for tag in soup.find_all(['img', 'script', 'link']):
        if tag.has_attr('src'):
            src_url = tag['src']
            # Only apply urljoin if src is a relative URL
            if not urlparse(src_url).scheme:
                tag['src'] = urljoin(base_url, src_url)
        if tag.name == 'img':
            if tag.has_attr('srcset'):
                srcset_urls = tag['srcset'].split(', ')
                tag['srcset'] = ', '.join(urljoin(base_url, urlparse(url).path) if not urlparse(url).scheme else url for url in srcset_urls)
        if tag.has_attr('href'):
            href_url = tag['href']
            # Only apply urljoin if href is a relative URL
            if not urlparse(href_url).scheme:
                tag['href'] = urljoin(base_url, href_url)

    # Handle <style> tags for CSS URL replacement
    for tag in soup.find_all(style=True):
        style = tag['style']
        updated_style = style.replace('url(', f'url({base_url}')
        tag['style'] = updated_style
    # Handle URLs in <style> tags as before
    for style_tag in soup.find_all('style'):
        if style_tag.string:
            updated_css = style_tag.string.replace('url(', f'url({base_url}')
            style_tag.string = updated_css

    # Determine content type
    content_type = r.headers.get('Content-Type', 'text/html')
    # Return the modified HTML content
    return HttpResponse(str(soup), content_type=content_type)
