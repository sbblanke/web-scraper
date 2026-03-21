# crawl.py

from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup


def normalize_url(input_url: str) -> str:
    url_parse = urlparse(input_url)
    full_url = f"{url_parse.netloc}{url_parse.path}"
    full_url = full_url.rstrip("/")
    return full_url.lower()


def get_heading_from_html(html_str: str) -> str:
    soup = BeautifulSoup(html_str, "html.parser")
    if soup.find("h1"):
        header = soup.find("h1").get_text().strip()
    elif soup.find("h2"):
        header = soup.find("h2").get_text().strip()
    else:
        return ""
    return header


def get_first_paragraph_from_html(html_str: str) -> str:
    soup = BeautifulSoup(html_str, "html.parser")
    if not soup.find("p"):
        return ""

    main_tag = soup.find("main")
    if main_tag:
        main_text = main_tag.find("p")
        if main_text:
            para = main_text.get_text().strip()
            return para
        else:
            return soup.find("p").get_text().strip()
    else:
        return soup.find("p").get_text().strip()


def get_urls_from_html(html_str: str, base_url: str) -> list[str]:
    soup = BeautifulSoup(html_str, "html.parser")
    if not soup.find_all("a"):
        return []

    links = []
    for link in soup.find_all("a"):
        if not link.get("href"):
            continue
        href_link = link.get("href")
        abs_link = urljoin(base_url, href_link)
        links.append(abs_link)

    return links


def get_images_from_html(html_str: str, base_url: str) -> list[str]:
    soup = BeautifulSoup(html_str, "html.parser")
    if not soup.find_all("img"):
        return []

    links = []
    for link in soup.find_all("img"):
        if not link.get("src"):
            continue
        href_link = link.get("src")
        abs_link = urljoin(base_url, href_link)
        links.append(abs_link)

    return links


def extract_page_data(html_str: str, page_url: str) -> None:
    page = {}
    page["url"] = page_url
    page["heading"] = get_heading_from_html(html_str)
    page["first_paragraph"] = get_first_paragraph_from_html(html_str)
    page["outgoing_links"] = get_urls_from_html(html_str, page_url)
    page["image_urls"] = get_images_from_html(html_str, page_url)
    return page
