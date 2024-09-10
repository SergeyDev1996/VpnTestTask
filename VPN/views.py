import re

import requests
from bs4 import BeautifulSoup
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseNotFound

from VPN.utils import (format_media_link, update_used_traffic,
                       change_soup_links,
                       prepare_base_url, get_selenium_response, update_site_statistic)
from urllib.parse import urlparse

from sites.models import Site


@login_required
def proxy_view(request, site_name, path=None):
    user_site = Site.objects.filter(user=request.user, name=site_name).first()
    if not user_site:
        return HttpResponseForbidden("You do not have access to this site")
    # Ensure base URL has a trailing slash
    base_url = prepare_base_url(user_site=user_site, request=request, path=path)
    driver = get_selenium_response(base_url)
    html_content = driver.page_source
    soup = BeautifulSoup(html_content, 'html.parser')
    current_host = f"{request.scheme}://{request.get_host()}/proxy"
    update_site_statistic(driver=driver,
                          user_site=user_site
                          )
    soup = change_soup_links(soup=soup,
                             base_url=base_url,
                             user_site=user_site,
                             path=path,
                             current_host=current_host,
                             site_name=site_name)
    content = str(soup)
    return HttpResponse(content)


@login_required
def static_files_proxy_view(request, site_name, resource_path):
    # Check if the user has access to the site
    user_site = Site.objects.filter(user=request.user, name=site_name).first()
    if not user_site:
        return HttpResponseForbidden("You do not have access to this site.")

    # Append the query string if it exists
    query_string = request.META.get('QUERY_STRING', '')
    if query_string:
        resource_path += f"?{query_string}"

    # Parse the URL and make sure it's fully qualified
    parsed_url = urlparse(resource_path)
    if not parsed_url.scheme:
        resource_path = f"https://{resource_path}"

    # Set the User-Agent header for the request
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/128.0.0.0 Safari/537.36"
        )
    }
    try:
        response = requests.get(resource_path, headers=headers)
        response.raise_for_status()
    except requests.exceptions.RequestException:
        return HttpResponseNotFound("The resource can not be downloaded")

    # Determine the content type and host for proxying URLs
    content_type = response.headers.get('content-type')
    current_host = f"{request.scheme}://{request.get_host()}/proxy"

    if content_type and content_type.startswith('text/css'):
        content = response.text

        # Modify URLs in CSS
        url_pattern = re.compile(r'url\((\/[^)]+)\)')
        matches = url_pattern.findall(content)
        for old_url in matches:
            new_url = format_media_link(url=old_url,
                                        current_host=current_host,
                                        site=user_site)
            content = content.replace(f'url({old_url})', f'url({new_url})')
        # Update used traffic based on content length
        update_used_traffic(
            traffic_amount=int(response.headers.get("Content-Length", 0)),
            user_site=user_site
        )
        # Return modified CSS
        proxy_response = HttpResponse(content, content_type=content_type)
    else:
        # Update used traffic for non-CSS resources
        update_used_traffic(
            traffic_amount=int(response.headers.get("Content-Length", 0)),
            user_site=user_site
        )
        # Return non-CSS content directly
        proxy_response = HttpResponse(response.content,
                                      content_type=content_type)
    # Set CORS header
    proxy_response["Access-Control-Allow-Origin"] = "*"
    return proxy_response
