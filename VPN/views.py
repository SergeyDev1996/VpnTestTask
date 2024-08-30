import re
import requests
from bs4 import BeautifulSoup
from django.http import HttpResponse, HttpResponseNotFound
from django.http import QueryDict
# from selenium import webdriver
# from selenium.webdriver.chrome.options import Options
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
#
# from webdriver_manager.chrome import ChromeDriverManager

from VPN.utils import link_to_our_website
from urllib.parse import urlparse, urljoin

# from requests_html import HTMLSession


def change_headers(request, site_name, requests_args=None):
    """
    Forward as close to an exact copy of the request as possible along to the
    given url.  Respond with as close to an exact copy of the resulting
    response as possible.

    If there are any additional arguments you wish to send to requests, put
    them in the requests_args dictionary.
    """
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
def format_path(path):
    if not path.endswith('/'):
        # Remove the last part of the path
        path_parts = path.strip('/').split('/')
        if len(path_parts) > 1:
            # Join all parts except the last one
            path = '/' + '/'.join(path_parts[:-1])
    return path

def proxy_view(request, site_name, path=None):
    # Base URL of the site you are proxying
    base_url = f"https://www.{site_name}"
    query_string = request.META.get('QUERY_STRING', '')
    if path:
        base_url += path
    if query_string:
        base_url += f"?{query_string}"
    # requests_args = {}.copy()
    # headers = get_headers(request.META)
    # params = request.GET.copy()
    # if 'headers' not in requests_args:
    #     requests_args['headers'] = {}
    # if 'data' not in requests_args:
    #     requests_args['data'] = request.body
    # if 'params' not in requests_args:
    #     requests_args['params'] = QueryDict('', mutable=True)

    # Overwrite any headers and params from the incoming request with explicitly
    # # specified values for the requests library.
    # headers.update(requests_args['headers'])
    # params.update(requests_args['params'])
    headers = {"user-agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36"}

    # chrome_options = Options()
    #
    # chrome_options.add_argument(
    #     '--headless')  # run in background
    # chrome_options.add_argument('--ignore-certificate-errors')
    # chrome_options.add_argument('--no-sandbox')
    # # chrome_options.add_argument('--disable-gpu')
    # # chrome_options.add_argument('--disable-dev-shm-usage')
    # chrome_options.add_argument('--start-maximized')
    # chrome_options.set_capability(
    #     'goog:loggingPrefs',  # for getting performance and network
    #     {'performance': 'ALL'}  # chrome devtools protocol logs
    # )

    # driver = webdriver.Chrome(options=chrome_options)
    # Make the external HTTP request
    r = requests.get(base_url, headers=headers)
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

    # Parse the HTML content
    # soup = BeautifulSoup(r.content, 'html.parser')
    # Handle img, script, and link tags
    # driver.get(base_url)
    # WebDriverWait(driver, 10) \
    #     .until(
    #     EC.presence_of_element_located((By.TAG_NAME, 'link'))
    # )  # wait for full load of page
    # html_content = driver.page_source
    html_content = r.content
    soup = BeautifulSoup(html_content, "html.parser")
    head = soup.find('head')
    # Create a new link tag to replace the old one
    current_host = f"{request.scheme}://{request.get_host()}"
    if head:
        base_tag = soup.new_tag('base', href=base_url)
        head.insert(0, base_tag)
    for tag in soup.find_all(['a', 'img', 'script', 'link']):
        if tag.name == 'a':
            href = tag.get("href", "")
            if "css_intro" in href:
                print(1)

            is_link_to_our_website = link_to_our_website(site_name=base_url, current_url=href)
            if is_link_to_our_website:
                parsed_url = urlparse(href)
                # formatted_path = format_path(path)
                if not parsed_url.netloc:
                    # Construct the full URL if it is a relative path

                    full_url = f"{current_host}/{site_name}{parsed_url.path}"
                    if parsed_url.query:
                        full_url += f"?{parsed_url.query}"
                    if parsed_url.fragment:
                        full_url += f"#{parsed_url.fragment}"
                else:
                    full_url = href
                tag["href"] = full_url
        else:
            for attr in ['src', 'href']:
                if tag.has_attr(attr):
                    url = tag[attr]
                    parsed_url = urlparse(url)
                        # Properly format the URL, including query and fragment
                    if parsed_url.netloc:
                        full_url = f"{current_host}/static_files_proxy/{parsed_url.netloc}{parsed_url.path}"
                    else:
                        full_url = f"{current_host}/static_files_proxy/{site_name}{parsed_url.path}"
                    if parsed_url.query:
                        full_url += f"?{parsed_url.query}"
                    if parsed_url.fragment:
                        full_url += f"#{parsed_url.fragment}"
                    tag[attr] = full_url
    # for tag in soup.find_all(['img', 'script', 'link', 'meta']):
    #     if tag.has_attr('src'):
    #         src_url = tag['src']
    #         # Only apply urljoin if src is a relative URL
    #         if not urlparse(src_url).scheme:
    #             tag['src'] = urljoin(base_url, src_url)
    #     if tag.name == 'img':
    #         if tag.has_attr('srcset'):
    #             srcset_urls = tag['srcset'].split(', ')
    #             tag['srcset'] = ', '.join(urljoin(base_url, urlparse(url).path) if not urlparse(url).scheme else url for url in srcset_urls)
    #     if tag.has_attr('href'):
    #         href_url = tag['href']
    #         # Only apply urljoin if href is a relative URL
    #         if not urlparse(href_url).scheme:
    #             tag['href'] = urljoin(base_url, href_url)

    # Handle <style> tags for CSS URL replacement
    # for tag in soup.find_all(style=True):
    #     style = tag['style']
    #     updated_style = style.replace('url(', f'url({base_url}')
    #     tag['style'] = updated_style
    # # Handle URLs in <style> tags as before
    # for style_tag in soup.find_all('style'):
    #     if style_tag.string:
    #         updated_css = style_tag.string.replace('url(', f'url({base_url}')
    #         style_tag.string = updated_css
    # for media_tag in soup.find_all(['picture', 'audio', 'video']):
    #     # Replace URLs in 'source' tags within 'picture'
    #     for source in media_tag.find_all('source'):
    #         if source.has_attr('srcset'):
    #             source['srcset'] = urljoin(base_url, source['srcset'])
    #     # Replace URL in 'img' tags within 'picture'
    #     if media_tag.has_attr('src'):
    #         media_tag.img['src'] = urljoin(base_url, media_tag['src'])
    # Determine content type
    # content_type = r.headers.get('Content-Type', 'text/html')
    # Return the modified HTML content
    content_type = r.headers.get('content-type')
    proxy_response = HttpResponse(str(soup), content_type=content_type, status=r.status_code)
    return proxy_response


def static_files_proxy_view(request, site_name, resource_path):
    # Ensure the site_name forms a correct URL
    base_url = f"https://www.{site_name}"

    # Properly join the resource path to the base URL
    full_url = urljoin(base_url, resource_path)
    # Include the query string if it exists
    query_string = request.META.get('QUERY_STRING', '')
    if query_string:
        full_url += f"?{query_string}"
    try:
        response = requests.get(full_url)
        response.raise_for_status()  # Raise an error for bad responses (4XX or 5XX)
    except requests.exceptions.RequestException as e:
        raise HttpResponseNotFound("Requested page was not found")
    proxy_response = HttpResponse(response.content, content_type=response.headers.get('content-type'))
    proxy_response["Access-Control-Allow-Origin"] = "*"
    return proxy_response
