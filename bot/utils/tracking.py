from typing import Callable, Optional

from fake_useragent import UserAgent
from playwright.async_api import async_playwright

from bot.models import TrackingRecord


def validate_tracking_number(tracking_number: str) -> bool:
    return len(tracking_number) == 24 and tracking_number.isdigit()


def _parse_tracking_result(result: list[str], sep: str) -> list[TrackingRecord]:
    items: list[TrackingRecord] = []

    date: Optional[str] = None

    for item in result:
        if "موقعیت" in item and "ساعت" in item:
            date = item.split(sep)[0]
            continue

        parts = [part.strip() for part in item.split(sep)]

        if len(parts) == 3:
            record = TrackingRecord(
                id=int(parts[0]),
                time=parts[2],
                description=parts[1],
            )
        elif len(parts) == 4:
            record = TrackingRecord(
                id=int(parts[0]),
                time=parts[3],
                location=parts[2],
                description=parts[1],
            )

        if date:
            record.date = date

        items.append(record)

    return items


async def track_parcel(
    tracking_number: str,
    sep: str = " | ",
    timeout: Optional[float] = None,
    normalizer: Optional[Callable[[str], str]] = None,
) -> list[TrackingRecord]:
    result: list[str] = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent=UserAgent().random)
        page = await context.new_page()

        # Open the post tracking website
        await page.goto("https://tracking.post.ir/", wait_until="load", timeout=timeout)

        # Input the tracking number
        await page.fill("#txtbSearch", tracking_number)

        # Clicking the search button
        await page.click("#btnSearch")

        # Wait for the tracking result to load
        await page.wait_for_selector("#pnlMain")

        # Fetch all divs with class 'row'
        all_row_divs = await page.query_selector_all("#pnlResult div.row")

        # Extract and clean data from each row
        for div in all_row_divs:
            columns = await div.query_selector_all("div.newtddata")
            if not columns:
                columns = await div.query_selector_all("div.newtdheader")
            row_data = [await column.text_content() for column in columns]
            if not row_data:
                continue
            result.append(sep.join(data.strip() for data in row_data if data))

        # Close the browser
        await browser.close()

    if result and normalizer:
        result = [normalizer(item) for item in result]

    return _parse_tracking_result(result, sep)
