# crawl.py

import asyncio
import aiohttp
import requests
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup


class AsyncCrawler:
    def __init__(self, base_url, max_concurrency=10, max_pages=100):
        if not base_url.startswith("http"):
            base_url = f"https://{base_url}"

        self.base_url = base_url
        self.base_domain = urlparse(base_url).hostname
        self.page_data = {}
        self.lock = asyncio.Lock()
        self.max_concurrency = max_concurrency
        self.semaphore = asyncio.Semaphore(self.max_concurrency)
        self.session = None
        self.max_pages = max_pages
        self.should_stop = False
        self.all_tasks = set()
        self.visited = set()

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.close()

    async def add_page_visit(self, normalized_url: str) -> bool:
        async with self.lock:
            if self.should_stop:
                return False
            if len(self.page_data) >= self.max_pages:
                self.should_stop = True
                print("Reached maximum number of pages to crawl.")
                for task in self.all_tasks:
                    task.cancel()
                return False
            if normalized_url not in self.visited:
                self.visited.add(normalized_url)
                return True
            return False

    async def fetch(self, url: str) -> str:  # FKA get_html()
        async with self.session.get(url) as resp:
            content_type = resp.headers.get("content-type", "")
            if resp.status >= 400:
                print(f"got HTTP error: {resp.status} {resp.reason}")
            elif "text/html" not in content_type:
                print(f"got non-HTML response: {content_type}")
            elif resp.status == 200:
                return await resp.text()

    async def crawl_page(self, current_url=None) -> list[str]:
        if self.should_stop:
            return
        # Handle "None" inputs for current_url and page_data (starting use case)
        if current_url is None:
            current_url = self.base_url

        # Compare base to current and return if they're not on the same domain
        if self.base_domain != urlparse(current_url).hostname:
            return self.page_data

        # Check if we've already visited this page
        curr_normalized = normalize_url(current_url)
        first_time_visited = await self.add_page_visit(curr_normalized)
        if not first_time_visited:
            return self.page_data

        async with self.semaphore:
            page_html = await self.fetch(current_url)
            if not page_html:
                return self.page_data
            curr_page_data = extract_page_data(page_html, current_url)

            async with self.lock:
                self.page_data[curr_normalized] = curr_page_data

            tasks = []
            links_for_async_tasks = curr_page_data["outgoing_links"]
            for link in links_for_async_tasks:
                task = asyncio.create_task(self.crawl_page(link))
                tasks.append(task)
                self.all_tasks.add(task)

        if tasks:
            try:
                await asyncio.gather(*tasks, return_exceptions=True)
            finally:
                for task in tasks:
                    self.all_tasks.discard(task)

        return self.page_data

    async def crawl(self):
        await self.crawl_page(self.base_url)
        return self.page_data


async def crawl_site_async(base_url, max_concurrency=None, max_pages=None):
    if max_concurrency is not None:
        updated_max_concurrency = max_concurrency
    if max_pages is not None:
        updated_max_pages = max_pages
    async with AsyncCrawler(
        base_url, updated_max_concurrency, updated_max_pages
    ) as crawler:
        await crawler.crawl()
        return crawler.page_data


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


def extract_page_data(html_str: str, page_url: str) -> dict[str:str]:
    page = {}
    page["url"] = page_url
    page["heading"] = get_heading_from_html(html_str)
    page["first_paragraph"] = get_first_paragraph_from_html(html_str)
    page["outgoing_links"] = get_urls_from_html(html_str, page_url)
    page["image_urls"] = get_images_from_html(html_str, page_url)
    return page


def safe_get_html(url: str):
    try:
        return get_html(url)
    except Exception as e:
        print(f"{e}")
        return None
