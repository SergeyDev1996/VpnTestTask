from urllib.parse import urlparse


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

    # Check if the current URL's domain is the same as the site name's domain,
    # or if the URL is relative, or if the site name is part of the current domain
    return (bool(parsed_url.netloc) and base_domain == current_domain) or link_is_relative or (
                base_domain in current_url)

def format_a_link(base_url: str, href: str, path: str, site_name: str, current_host: str):
    is_link_to_our_website = link_to_our_website(site_name=base_url, current_url=href)
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


def format_media_link(tag, attr, site_name, current_host):
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
        return full_url