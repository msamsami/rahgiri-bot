from contextlib import asynccontextmanager, suppress
from typing import AsyncGenerator, Callable, Optional

from fake_useragent import UserAgent
from playwright.async_api import (
    ElementHandle,
    Page,
    ProxySettings,
    ViewportSize,
    async_playwright,
)

from bot.models import TrackingRecord

from .exceptions import TrackingError

__all__ = ("validate_tracking_number", "ParcelTracker")


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


class ParcelTracker:
    """
    A class to track parcels using the Iran Post Tracking website. Provides methods
    to scrape the tracking website and fetch parcel tracking details as text records or as a screenshot image.

    Args:
        normalizer (Optional[Callable[[str], str]]): A function to normalize the extracted text data. Defaults to None.
        proxy (Optional[ProxySettings]): Proxy settings for web scraping requests. Defaults to None.
    """

    def __init__(self, normalizer: Optional[Callable[[str], str]] = None, proxy: Optional[ProxySettings] = None) -> None:
        self.normalizer = normalizer
        self.proxy = proxy
        self._sep = " | "

    @asynccontextmanager
    async def _open_tracking_page(self, tracking_number: str, timeout: Optional[float]) -> AsyncGenerator[Page, None]:
        timeout_ms = timeout * 1000 if timeout else None
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(args=["--no-sandbox", "--disable-setuid-sandbox"], headless=True)
            try:
                context = await browser.new_context(user_agent=UserAgent().random, proxy=self.proxy)
                page = await context.new_page()
                await page.goto(f"https://tracking.post.ir/?id={tracking_number}", wait_until="load", timeout=timeout_ms)
            except Exception:
                await browser.close()
                raise
            yield page
            await browser.close()

    async def _extract_tracking_rows(self, page: Page) -> list[ElementHandle]:
        await page.click("#btnSearch")
        await page.wait_for_selector("#pnlMain")

        all_row_divs = await page.query_selector_all("#pnlResult div.row")

        if not all_row_divs:
            alert_divs = await page.query_selector_all("#pnlResult div.alert")
            if alert_divs:
                raise TrackingError(await alert_divs[0].text_content())

        return all_row_divs

    @staticmethod
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

    async def _extract_tracking_records(self, tracking_rows: list[ElementHandle]) -> list[TrackingRecord]:
        result: list[str] = []
        for div in tracking_rows:
            columns = await div.query_selector_all("div.newtddata")
            if not columns:
                columns = await div.query_selector_all("div.newtdheader")
            row_data = [await column.text_content() for column in columns]
            if not row_data:
                continue
            result.append(self._sep.join(value.strip() for value in row_data if value))

        if not result:
            return []

        if self.normalizer:
            result = [self.normalizer(item) for item in result]

        return self._parse_tracking_result(result, self._sep)

    async def track_as_text(self, tracking_number: str, timeout: Optional[float] = None) -> list[TrackingRecord]:
        """Fetch tracking details as structured text records.

        Args:
            tracking_number (str): The tracking number of the parcel.
            timeout (Optional[float]): Timeout for loading the tracking website, in seconds. Defaults to None.

        Returns:
            list[TrackingRecord]: A list of `TrackingRecord` items containing tracking details.

        Raises:
            TrackingError: Raised when the tracking service returns an error. The exception message provides the tracking error message.
        """
        async with self._open_tracking_page(tracking_number, timeout) as page:
            tracking_rows = await self._extract_tracking_rows(page)
            return await self._extract_tracking_records(tracking_rows)

    async def track_as_image(self, tracking_number: str, timeout: Optional[float] = None) -> bytes:
        """Fetch tracking details as a screenshot image.

        Args:
            tracking_number (str): The tracking number of the parcel.
            timeout (Optional[float]): Timeout for loading the tracking website, in seconds. Defaults to None.

        Returns:
            bytes: The screenshot of the tracking website in PNG format.

        Raises:
            TrackingError: Raised when the tracking service returns an error. The exception message provides the tracking error message.
        """
        async with self._open_tracking_page(tracking_number, timeout) as page:
            await self._extract_tracking_rows(page)
            content_height = 2000
            with suppress(Exception):
                content_height = await page.evaluate("document.documentElement.scrollHeight")
            await page.set_viewport_size(ViewportSize(width=1920, height=content_height))
            return await page.screenshot(type="png")

    def __repr__(self) -> str:
        return f"ParcelTracker<(normalizer={self.normalizer}, proxy={self.proxy})>"
