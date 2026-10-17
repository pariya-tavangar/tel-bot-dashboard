
from pathlib import Path
from playwright.sync_api import sync_playwright

PROFILE = Path(__file__).parent / "telegram_browser_profile"

SELECTORS = [
    "[data-message-id]",
    ".message",
    ".bubble",
    ".message-list-item",
]

with sync_playwright() as p:
    context = p.chromium.launch_persistent_context(
        user_data_dir=str(PROFILE),
        headless=False,
    )

    page = context.pages[0] if context.pages else context.new_page()
    page.goto("https://web.telegram.org/")

    input(
        "Open your private channel in the browser, "
        "then press Enter here..."
    )

    for selector in SELECTORS:
        elements = page.locator(selector)
        count = elements.count()
        print(f"\n{selector}: {count} elements")

        for i in range(max(0, count - 3), count):
            try:
                element = elements.nth(i)
                if element.is_visible():
                    text = element.inner_text(timeout=1500)
                    if text.strip():
                        print(" -", text[:180].replace("\n", " "))
            except Exception:
                pass

    input("\nInspection finished. Press Enter to close...")
    context.close()
