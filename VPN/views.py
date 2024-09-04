import json
import requests
from bs4 import BeautifulSoup
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseForbidden

from selenium import webdriver


from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager

from VPN.utils import (format_a_link, format_media_link, update_used_traffic,
                       update_transitions_count)
from urllib.parse import urlparse, urljoin

from sites.models import Site


def ensure_trailing_slash(url):
    """Ensure the URL ends with a trailing slash."""
    if not url.endswith('/'):
        return url + '/'
    return url


@login_required
def proxy_view(request, site_name, path=None):
    user_site = Site.objects.filter(user=request.user, name=site_name).first()
    if not user_site:
        return HttpResponseForbidden("You do not have access to this site")
    # Ensure base URL has a trailing slash
    base_url = ensure_trailing_slash(user_site.url)
    if path:
        base_url = urljoin(base_url, path)  # Properly join path to base URL
    query_string = request.META.get('QUERY_STRING', '')
    if query_string:
        base_url = f"{base_url}?{query_string}"
    chrome_options = Options()
    chrome_options.add_argument('--headless')  # Run in background
    chrome_options.add_argument('--ignore-certificate-errors')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--start-maximized')
    chrome_options.set_capability('goog:loggingPrefs',
                                  {'performance': 'ALL'})

    driver = webdriver.Chrome(
        service=ChromeService(ChromeDriverManager().install()),
        options=chrome_options)

    # try:
    driver.get(base_url)
    driver.implicitly_wait(10)  # Wait for page to load
    html_content = driver.page_source

    soup = BeautifulSoup(html_content, 'html.parser')
    current_host = f"{request.scheme}://{request.get_host()}/proxy"
    performance_logs = driver.get_log('performance')
    performance_list = [
        json.loads(log['message'].lower())['message']
        for log in performance_logs
    ]

    total_traffic = sum([
        int(log["params"]["response"]["headers"].get("content-length", 0))
        for log in performance_list
        if log["method"] == "network.responsereceived"
    ])
    update_used_traffic(traffic_amount=total_traffic, user_site=user_site)
    update_transitions_count(user_site=user_site)
    for tag in soup.find_all(['a', 'img', 'script', 'link']):
        if tag.name == 'a':
            href = tag.get("href", "")
            full_url = format_a_link(base_url=base_url,
                                     href=href,
                                     path=path,
                                     site_name=site_name,
                                     current_host=current_host)
            tag["href"] = full_url
        else:
            for attr in ['src', 'href']:
                if attr in tag.attrs:
                    full_url = format_media_link(tag=tag, attr=attr,
                                                 site=user_site,
                                                 current_host=current_host)
                    tag[attr] = full_url
    content = str(soup)
    return HttpResponse(content)


@login_required
def static_files_proxy_view(request, site_name, resource_path):
    user_site = Site.objects.filter(user=request.user, name=site_name).first()
    if not user_site:
        return HttpResponseForbidden("You do not have access to this site.")

    query_string = request.META.get('QUERY_STRING', '')
    if query_string:
        resource_path += f"?{query_string}"
    parsed_url = urlparse(resource_path)
    if not parsed_url.scheme:
        resource_path = f"https://{resource_path}"
    response = requests.get(resource_path)
    response.raise_for_status()
    content_type = response.headers.get('content-type')
    update_used_traffic(
                        traffic_amount=int(response.headers.get(
                            "Content-Length", 0)),
                        user_site=user_site)
    proxy_response = HttpResponse(response.content, content_type=content_type)
    proxy_response["Access-Control-Allow-Origin"] = "*"
    return proxy_response
