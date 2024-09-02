import re
import requests
from bs4 import BeautifulSoup
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseNotFound, HttpResponseForbidden
from django.http import QueryDict
from VPN.utils import link_to_our_website, format_a_link, format_media_link
from urllib.parse import urlparse, urljoin

from sites.models import Site


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

@login_required
def proxy_view(request, site_name, path=None):
    user_site = Site.objects.filter(user=request.user, url=site_name).exists()
    if not user_site:
        return HttpResponseForbidden("You do not have access to this site.")
    # Base URL of the site you are proxying
    base_url = f"https://www.{site_name}/"
    query_string = request.META.get('QUERY_STRING', '')
    if path:
        base_url += path
    if query_string:
        base_url += f"?{query_string}"
    headers = {"user-agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36"}
    r = requests.get(base_url, headers=headers)
    html_content = r.content
    soup = BeautifulSoup(html_content, "html.parser")
    head = soup.find('head')
    # Create a new link tag to replace the old one
    current_host = f"{request.scheme}://{request.get_host()}/proxy"
    if head:
        base_tag = soup.new_tag('base', href=base_url)
        head.insert(0, base_tag)
    for tag in soup.find_all(['a', 'img', 'script', 'link']):
        if tag.name == 'a':
            href = tag.get("href", "")
            full_url = format_a_link(base_url=base_url, href=href, path=path,
                                     site_name=site_name, current_host=current_host)
            tag["href"] = full_url
        else:
            for attr in ['src', 'href']:
                full_url = format_media_link(tag=tag, attr=attr, site_name=site_name, current_host=current_host)
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

@login_required
def static_files_proxy_view(request, site_name, resource_path):
    user_site = Site.objects.filter(user=request.user, url=site_name).exists()
    if not user_site:
        return HttpResponseForbidden("You do not have access to this site.")
    # Ensure the site_name forms a correct URL
    base_url = f"https://{site_name}"
    # Properly join the resource path to the base URL
    full_url = urljoin(base_url, resource_path)
    # Include the query string if it exists
    query_string = request.META.get('QUERY_STRING', '')
    if query_string:
        full_url += f"?{query_string}"
    response = requests.get(full_url)
    response.raise_for_status()  # Raise an error for bad responses (4XX or 5XX)
    proxy_response = HttpResponse(response.content, content_type=response.headers.get('content-type'))
    proxy_response["Access-Control-Allow-Origin"] = "*"
    return proxy_response
