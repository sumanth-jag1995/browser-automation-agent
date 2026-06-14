async def run(page, url: str, screenshot_dir: str) -> dict:
    import asyncio
    import os

    last_error = None
    for attempt in range(3):
        result = {"status": "success", "screenshots": []}
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=90000)
            await page.wait_for_load_state("networkidle", timeout=60000)
            os.makedirs(screenshot_dir, exist_ok=True)
            path = os.path.join(screenshot_dir, "repaired_flow.png")
            await page.screenshot(path=path, full_page=True)
            result["screenshots"].append(path)
            return result
        except Exception as exc:
            last_error = exc
            await asyncio.sleep(1 * (attempt + 1))
    return {"status": "fail", "error": type(last_error).__name__ + ": " + str(last_error)}