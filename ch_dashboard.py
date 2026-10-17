from pathlib import Path
from playwright.sync_api import sync_playwright

PROFILE = Path(__file__).parent / "telegram_browser_profile"

with sync_playwright() as p:
    context = p.chromium.launch_persistent_context(
        user_data_dir=str(PROFILE),
        headless=False,
    )

    page = context.pages[0] if context.pages else context.new_page()
    page.goto("https://web.telegram.org/")

    print("Sign in to Telegram Web if prompted.")
    print("Open your private channel and make sure its posts are visible.")
    input("When ready, press Enter here in the terminal...")

    print("Current page:", page.url)
    print("Page title:", page.title())

    input("Browser session ready. Press Enter to close...")
    context.close()