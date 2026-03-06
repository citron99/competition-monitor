import asyncio
import json
import re
from pathlib import Path
from typing import Dict, List

from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError


COMPETITORS: Dict[str, List[str]] = {
    "elhim_iskra": [
        "https://elhim-iskra.ru/",
        "https://elhim-iskra.ru/akkumuljatory-dlja-pogruzchikov/",
    ],
    "tab_rus": [
        "https://www.tab-rus.ru/",
        "https://www.tab-rus.ru/product/tyagovye-akkumulyatornye-batarei/",
    ],
    "akb48v": [
        "https://www.akb48v.ru/",
        "https://www.akb48v.ru/catalog/batteries-by-type-of-warehouse-equipment/tyagovye-akkumulyatory-48-volt-dlya-pogruzchikov",
    ],
    "e_akb": [
        "https://www.e-akb.ru/",
        "https://www.e-akb.ru/akkumulyatory/tyagovye-akkumulyatory-dlya-pogruzchikov-i-skladskoj-tekhniki/",
    ],
    "tab_battery": [
        "https://tab-battery.ru/",
    ],
}

BASE_DIR = Path("data")
VIEWPORT = {"width": 1440, "height": 2200}
PAGE_TIMEOUT_MS = 45000


def slugify_url(url: str) -> str:
    cleaned = re.sub(r"^https?://", "", url)
    cleaned = cleaned.strip("/")

    if not cleaned:
        return "homepage"

    cleaned = cleaned.replace("/", "__")
    cleaned = re.sub(r"[^a-zA-Z0-9_.а-яА-Я-]+", "_", cleaned)
    cleaned = cleaned.strip("._-")

    return cleaned or "page"


async def dismiss_popups(page) -> None:
    possible_selectors = [
        "button:has-text('Принять')",
        "button:has-text('Согласен')",
        "button:has-text('Согласна')",
        "button:has-text('Accept')",
        "button:has-text('I agree')",
        "button:has-text('OK')",
        "[aria-label='close']",
        ".cookie-agreement__button",
        ".cookies__button",
        ".cookie-btn",
        ".fancybox-close-small",
        ".popup__close",
        ".modal__close",
    ]

    for selector in possible_selectors:
        try:
            locator = page.locator(selector).first
            if await locator.is_visible(timeout=1500):
                await locator.click(timeout=1500)
                await page.wait_for_timeout(1000)
        except Exception:
            pass


async def save_page_assets(page, url: str, out_dir: Path) -> None:
    file_stem = slugify_url(url)

    png_path = out_dir / f"{file_stem}.png"
    pdf_path = out_dir / f"{file_stem}.pdf"
    html_path = out_dir / f"{file_stem}.html"
    json_path = out_dir / f"{file_stem}.json"

    print(f"  -> Открываю: {url}")
    await page.goto(url, wait_until="domcontentloaded", timeout=PAGE_TIMEOUT_MS)

    try:
        await page.wait_for_load_state("networkidle", timeout=12000)
    except PlaywrightTimeoutError:
        pass

    await dismiss_popups(page)
    await page.wait_for_timeout(1500)

    html = await page.content()
    html_path.write_text(html, encoding="utf-8")

    title = await page.title()
    h1 = ""
    try:
        h1 = await page.locator("h1").first.inner_text(timeout=2000)
    except Exception:
        pass

    metadata = {
        "url": url,
        "title": title,
        "h1": h1,
    }
    json_path.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    await page.screenshot(path=str(png_path), full_page=True)

    await page.pdf(
        path=str(pdf_path),
        print_background=True,
        format="A4",
        margin={"top": "10mm", "right": "10mm", "bottom": "10mm", "left": "10mm"},
    )

    print(f"     Сохранено: {png_path}")
    print(f"     Сохранено: {pdf_path}")
    print(f"     Сохранено: {html_path}")
    print(f"     Сохранено: {json_path}")


async def process_competitor(browser, name: str, urls: List[str]) -> None:
    out_dir = BASE_DIR / name
    out_dir.mkdir(parents=True, exist_ok=True)

    context = await browser.new_context(
        viewport=VIEWPORT,
        locale="ru-RU",
        user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0.0.0 Safari/537.36"
        ),
    )

    page = await context.new_page()

    try:
        for url in urls:
            try:
                await save_page_assets(page, url, out_dir)
            except Exception as e:
                print(f"     Ошибка на {url}: {e}")
    finally:
        await context.close()


async def main() -> None:
    BASE_DIR.mkdir(parents=True, exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        try:
            for name, urls in COMPETITORS.items():
                print(f"\n=== {name} ===")
                await process_competitor(browser, name, urls)
        finally:
            await browser.close()

    print("\nГотово. Все файлы сохранены в папку data/")


if __name__ == "__main__":
    asyncio.run(main())