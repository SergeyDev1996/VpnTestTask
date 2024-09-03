import os
import re
import requests
from bs4 import BeautifulSoup
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseNotFound, HttpResponseForbidden
from django.http import QueryDict
from selenium.webdriver.chrome.service import Service

from selenium import webdriver

# import undetected_chromedriver2 as uc

from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager

from VPN.utils import link_to_our_website, format_a_link, format_media_link, update_used_traffic, \
    update_transitions_count, get_network_response_headers
from urllib.parse import urlparse, urljoin

from sites.models import Site


def replace_url(match):
    original_url = match.group(1)  # Extract the content inside url(...)
    # Example of how to replace it, you can modify this as needed
    new_url = f"url({original_url})"  # Replace this line with your desired logic
    return new_url

@login_required
def proxy_view(request, site_name, path=None):
    user_site = Site.objects.filter(user=request.user, name=site_name).first()
    if not user_site:
        return HttpResponseForbidden("You do not have access to this site")
    # Base URL of the site you are proxying
    base_url = user_site.url
    query_string = request.META.get('QUERY_STRING', '')
    if path:
        base_url += path
    if query_string:
        base_url += f"?{query_string}"
    headers = {"user-agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36"}
    # response = requests.get(base_url, headers=headers)
    chrome_options = Options()

    chrome_options.add_argument('--headless')  # run in background
    chrome_options.add_argument('--ignore-certificate-errors')
    # for running in docker container
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--start-maximized')
    chrome_options.set_capability(
        'goog:loggingPrefs',  # for getting performance and network
        {'performance': 'ALL'}  # chrome devtools protocol logs
    )
    ChromeDriverManager().install()
    driver_path = "/root/.wdm/drivers/chromedriver/linux64/128.0.6613.119/chromedriver-linux64/chromedriver"
    os.chmod(driver_path, 0o755)
    service = Service(executable_path=driver_path)

    # Create a new instance of the Chrome driver
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.get(base_url)
    # Wait for the page to fully load
    driver.implicitly_wait(4)  # Adjust wait time if needed
    # Get page source after JavaScript execution
    html_content = driver.page_source
    driver.quit()  # Quit the browser after rendering
    # update_used_traffic(traffic_amount=int(response.headers.get('Content-Length', 0)), user_site=user_site)
    # update_transitions_count(user_site)
    # html_content = response.content
    soup = BeautifulSoup(html_content, "html.parser")
    head = soup.find('head')
    # Create a new link tag to replace the old one
    current_host = f"{request.scheme}://{request.get_host()}/proxy"
    # if head:
    #     base_tag = soup.new_tag('base', href=base_url)
    #     head.insert(0, base_tag)
    for tag in soup.find_all(['a', 'img', 'script', 'link']):
        if tag.name == 'a':
            href = tag.get("href", "")
            # if "FranklinGothicFS" in href:
            #     print(1)
            full_url = format_a_link(base_url=base_url, href=href, path=path,
                                     site_name=site_name, current_host=current_host)
            tag["href"] = full_url
        else:
            for attr in ['src', 'href']:
                if attr == "srcset":
                    srcset_urls = tag['srcset'].split(', ')
                    formatted_srcset_urls = []
                    for srcset_url in srcset_urls:
                        current_srcset = format_media_link(tag=srcset_url, attr=attr, site=user_site, current_host=current_host)
                        formatted_srcset_urls.append(current_srcset)
                    tag['srcset'] = ', '.join(formatted_srcset_urls)
                else:
                    full_url = format_media_link(tag=tag, attr=attr, site=user_site, current_host=current_host)
                    tag[attr] = full_url
                    # print(f"ATTR: {tag[attr]}")

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
    # pattern = re.compile(r'url\(([^)]+)\)')
    # def replace_url(match):
    #     old_url = match.group(1).strip('\"\'')  # Extract and clean the content inside url(...)
    #     new_url = f"url({site_name}static_files_proxy/{old_url})"  # Create the new URL
    #     return new_url
    # for style_tag in soup.find_all('style'):
    #
    #     if style_tag.string:
    #         if "lynx-path-left-side.png" in style_tag.string:
    #             print(f"ORIGIN: {style_tag.string}")
    #         updated_style = re.sub(pattern, replace_url, style_tag.string)
    #         style_tag.string.replace_with(updated_style)
    #         print(f"AFTER: {style_tag.string}")
    # pattern = re.compile(r'url\(["\']?([^"\')]+)["\']?\)')
    content = str(soup)
    # response_headers = get_network_response_headers(driver)
    # for style_tag in soup.find_all('style'):
    #     if style_tag.string:
    #         print(f"STYLE: {style_tag.string}")
    #         updated_style = re.sub(pattern, replace_url, style_tag.string)
    #         style_tag.string.replace_with(updated_style)

    # Also handle inline style attributes in any HTML tag
    # for tag in soup.find_all(True, style=True):
    #     print(f"STYLE: {tag['style']}")
    #     updated_style = re.sub(pattern, replace_url, tag['style'])
    #     tag['style'] = updated_style
    # # Also handle inline style attributes in any HTML tag
    # for tag in soup.find_all(True, style=True):
    #     updated_style = re.sub(pattern, replace_url, tag['style'])
    #     tag['style'] = updated_style
    # content_type = response_headers.headers.get('content-type')
    # proxy_response = HttpResponse(content, content_type=content_type, status=response.status_code)
    proxy_response = HttpResponse(content)
    return proxy_response

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
    response.raise_for_status()  # Raise an error for bad responses (4XX or 5XX)

    update_used_traffic(traffic_amount=int(response.headers.get('Content-Length', 0)), user_site=user_site)

    content_type = response.headers.get('content-type')
    current_host = f"{request.scheme}://{request.get_host()}/proxy"

    # if content_type.startswith('text/css'):
    #     content = response.text
    #     url_pattern = re.compile(r'url\((.*?)\)')
    #     matches = url_pattern.findall(content)
    #
    #     for old_url in matches:
    #         old_relative_path = urlparse(old_url).path
    #         parsed_url = urlparse(old_relative_path)
    #         # Properly format the URL, including query and fragment
    #         if parsed_url.netloc:
    #             full_url = f"{current_host}/static_files_proxy/{user_site.name}/{parsed_url.netloc}{parsed_url.path}"
    #         else:
    #             full_url = f"{current_host}/static_files_proxy/{user_site.name}/{user_site.url}{parsed_url.path}"
    #         content = content.replace(f'url({old_url})', f'url({full_url})')
    #
    #     # Update the response content with the modified CSS content
    #     proxy_response = HttpResponse(content, content_type=content_type)
    # else:
    #     # For non-CSS content, just pass the original content through
    proxy_response = HttpResponse(response.content, content_type=content_type)
    proxy_response["Access-Control-Allow-Origin"] = "*"
    return proxy_response
