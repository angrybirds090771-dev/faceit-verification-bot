from playwright.sync_api import sync_playwright

print("STEP 1: Python работает", flush=True)

with sync_playwright() as p:

    print("STEP 2: Playwright запущен", flush=True)

    browser = p.chromium.launch(
        headless=False
    )

    print("STEP 3: Chromium запущен", flush=True)

    page = browser.new_page()

    print("STEP 4: Страница создана", flush=True)

    page.goto(
        "https://www.faceit.com/en/players/eBY21",
        wait_until="domcontentloaded",
        timeout=60000
    )

    print("STEP 5: FACEIT открылся", flush=True)

    page.wait_for_timeout(10000)

    badge = page.locator(
        '[data-testid="verification-icon"]'
    )

    print(
        "STEP 6: Verification icons =",
        badge.count(),
        flush=True
    )

    browser.close()

    print("STEP 7: Браузер закрыт", flush=True)
