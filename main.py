# main.py

import asyncio
import sys
from crawl import crawl_site_async
from json_report import write_json_report
from typing import cast


async def main_async():
    if len(sys.argv) < 2:
        print("no website provided")
        sys.exit(1)
    elif len(sys.argv) > 4:
        print("too many arguments provided")
        sys.exit(1)
    else:
        BASE_URL = sys.argv[1]
        print(f"starting crawl of: {BASE_URL}")

    max_concurrency: int | None = None
    max_pages: int | None = None
    if len(sys.argv) in [3, 4]:
        max_concurrency = int(sys.argv[2])

        if sys.argv[3] is not None:
            max_pages = int(sys.argv[3])

    page_data = await crawl_site_async(BASE_URL, max_concurrency, max_pages)

    write_json_report(page_data)


if __name__ == "__main__":
    asyncio.run(main_async())
