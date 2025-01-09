from typing import Callable, Optional

from fake_useragent import UserAgent
from playwright.async_api import async_playwright

from bot.models import TrackingRecord

from .exceptions import TrackingError

__all__ = ("validate_tracking_number", "track_parcel")


def validate_tracking_number(tracking_number: str) -> bool:
    """Validate a parcel tracking number.

    A valid tracking number should be 24 digits long and consist only of digits.

    Args:
        tracking_number (str): The tracking number to validate.

    Returns:
        bool: True if the tracking number is valid, False otherwise.
    """
    tracking_number = tracking_number.strip()
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
    timeout: Optional[float] = None,
    normalizer: Optional[Callable[[str], str]] = None,
) -> list[TrackingRecord]:
    """Track a parcel using its tracking number by scraping the Iran Post Tracking website.

    This function uses Playwright to automate a browser session to fetch tracking information
    from the tracking website. It processes the data to extract and return relevant tracking records.

    Args:
        tracking_number (str): The tracking number of the parcel to be tracked.
        timeout (Optional[float]): The timeout for the tracking website to load, in seconds. Defaults to None for 30 seconds.
        normalizer (Optional[Callable[[str], str]]): A function to normalize the extracted text data. Defaults to None.

    Returns:
        list[TrackingRecord]: A list of `TrackingRecord` items containing the parsed tracking records.

    Raises:
        TrackingError: If the tracking service returns an error message. The error message is returned as the exception message.
    """
    result: list[str] = []
    sep = " | "

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent=UserAgent().random)
        page = await context.new_page()

        # Open the post tracking website
        timeout_ms = timeout * 1000 if timeout else None
        await page.goto(f"https://tracking.post.ir/?id={tracking_number}", wait_until="load", timeout=timeout_ms)

        # Clicking the search button
        await page.click("#btnSearch")

        # Wait for the tracking result to load
        await page.wait_for_selector("#pnlMain")

        # Fetch all divs with class 'row'
        all_row_divs = await page.query_selector_all("#pnlResult div.row")

        # Check if the tracking service returned an error message
        if not all_row_divs:
            alert_divs = await page.query_selector_all("#pnlResult div.alert")
            if alert_divs:
                raise TrackingError(await alert_divs[0].text_content())

        # Extract and clean data from each row
        for div in all_row_divs:
            columns = await div.query_selector_all("div.newtddata")
            if not columns:
                columns = await div.query_selector_all("div.newtdheader")
            row_data = [await column.text_content() for column in columns]
            if not row_data:
                continue
            result.append(sep.join(data.strip() for data in row_data if data))

    if result and normalizer:
        result = [normalizer(item) for item in result]

    return _parse_tracking_result(result, sep)
