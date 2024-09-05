import re
from urllib.parse import urlparse

from selenium.webdriver.chrome.options import Options
from selenium import webdriver


from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager

from sites.models import Site


def setup_selenium_driver():
    options = setup_selenium_options()
    driver = webdriver.Chrome(
        service=ChromeService(ChromeDriverManager().install()),
        options=options)
    return driver


def change_soup_links(soup, base_url: str, path: str,
                      site_name: str, current_host: str, user_site):
    for tag in soup.find_all(['a', 'img', 'script',
                              'link', 'source', 'audio', 'video']):
        if tag.name == 'a':
            href = tag.get("href", "")
            full_url = format_a_link(base_url=base_url,
                                     href=href,
                                     path=path,
                                     site_name=site_name,
                                     current_host=current_host)
            tag["href"] = full_url
        else:
            for attr in ['src', 'href', 'srcset']:
                if attr in tag.attrs:
                    url = tag.get(attr, None)
                    full_url = format_media_link(url=url,
                                                 site=user_site,
                                                 current_host=current_host)
                    tag[attr] = full_url
    soup = change_style_tags(soup=soup,
                             current_host=current_host,
                             user_site=user_site)
    return soup


def change_style_tags(soup, current_host, user_site):
    content = str(soup)
    url_pattern = re.compile(r"url\((['\"]?)(\/?[^)'\"\s]+)\1\)")
    for style_tag in soup.find_all('style'):
        style_content = style_tag.string
        if style_content:
            # Find all URLs in the <style> content
            matches = url_pattern.findall(style_content)
            # Replace each found URL with the proxy URL
            for old_url in matches:
                new_url = format_media_link(url=old_url[1],
                                            current_host=current_host,
                                            site=user_site)
                content = content.replace(f"url('{old_url[1]}')",
                                          f"url('{new_url}')")
    return content


def setup_selenium_options():
    chrome_options = Options()
    chrome_options.add_argument('--headless')  # Run in background
    chrome_options.add_argument('--ignore-certificate-errors')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--start-maximized')
    chrome_options.set_capability('goog:loggingPrefs',
                                  {'performance': 'ALL'})
    return chrome_options


def extract_base_domain(url: str) -> str:
    """
    Extracts the base domain from a URL.
    """
    parsed_url = urlparse(url)
    netloc = parsed_url.netloc
    parts = netloc.split('.')

    if len(parts) > 2:
        # For domains like 'www.example.com', 'sub.example.co.uk'
        domain = parts[-2]
    else:
        # For domains like 'example.com'
        domain = parts[0]

    return domain


def check_link_is_relative(parsed_url) -> bool:
    """
    Determines if the provided URL is relative.
    """
    return not parsed_url.netloc and parsed_url.path


def link_to_our_website(site_name: str, current_url: str) -> bool:
    """
    Checks if the given URL points to the same website or is a relative link.
    """
    # Extract the base domain from the site name
    base_domain = extract_base_domain(site_name)
    # Parse the current URL
    parsed_url = urlparse(current_url)

    # Determine if the link is relative
    link_is_relative = check_link_is_relative(parsed_url)

    # Extract domain from the current URL
    current_domain = extract_base_domain(current_url)

    # Check if the current URL's domain is the same as the
    # site name's domain,
    # or if the URL is relative, or if the site name
    # is part of the current domain
    return ((bool(parsed_url.netloc) and base_domain == current_domain)
            or link_is_relative or (
                base_domain in current_url))


def format_a_link(base_url: str, href: str, path: str,
                  site_name: str, current_host: str):
    is_link_to_our_website = link_to_our_website(site_name=base_url,
                                                 current_url=href)
    if is_link_to_our_website:
        parsed_url = urlparse(href)
        # formatted_path = format_path(path)
        if path:
            if "." in path:
                path = "/".join(path.split("/")[:-1])
        if href.startswith("/"):
            link_to_current_page = f"{site_name}"
        else:
            link_to_current_page = f"{site_name}/{path}/"
        link_to_current_page += parsed_url.path
        if not parsed_url.netloc:
            # Construct the full URL if it is a relative path
            full_url = f"{current_host}/{link_to_current_page}"
            if parsed_url.query:
                full_url += f"?{parsed_url.query}"
            if parsed_url.fragment:
                full_url += f"#{parsed_url.fragment}"
        else:
            full_url = href
        return full_url


def format_media_link(url, site, current_host):
    if url:
        parsed_url = urlparse(url)
        # Properly format the URL, including query and fragment
        if parsed_url.netloc:
            full_url = (f"{current_host}/static_files_proxy/{site.name}/"
                        f"{parsed_url.netloc}{parsed_url.path}")
        else:
            if (not parsed_url.path.startswith("/")
                    and not site.url.endswith("/")):
                site.url += "/"
            full_url = (f"{current_host}/static_files_proxy/"
                        f"{site.name}/{site.url}{parsed_url.path}")
        if parsed_url.query:
            full_url += f"?{parsed_url.query}"
        if parsed_url.fragment:
            full_url += f"#{parsed_url.fragment}"
        return full_url


def update_used_traffic(traffic_amount: int, user_site: Site):
    user_site.total_bytes += traffic_amount
    user_site.save()


def update_transitions_count(user_site: Site):
    user_site.transitions_count += 1
    user_site.save()


def get_network_response_headers(driver):
    response = driver.execute_cdp_cmd('Network.getResponseBody',
                                      {'requestId': 'some-request-id'})
    return response
