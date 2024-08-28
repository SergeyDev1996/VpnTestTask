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