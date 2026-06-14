async def run(page, url: str, screenshot_dir: str) -> dict:
    """Automate flow: password_reset_flow"""
    import os

    result = {"status": "success", "screenshots": [], "flow": "password_reset_flow"}
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=60000)
        await page.wait_for_load_state("networkidle", timeout=30000)
        import json
        from pathlib import Path

        creds_path = Path("D:\\04_Self\\10_Agents\\02_Projects\\04_Browser_Automation_Agent\\browser-automation-agent\\test_data\\credentials.json")
        creds = {"username": "Admin", "password": "admin123"}
        if creds_path.exists():
            creds = json.loads(creds_path.read_text(encoding="utf-8")).get("login", creds)

        username = page.locator(
            'input[name="username"], input[type="email"], input[name="email"]'
        ).first
        password = page.locator(
            'input[name="password"], input[type="password"]'
        ).first
        submit = page.get_by_role("button", name="Login").or_(
            page.get_by_role("button", name="Sign in")
        ).or_(page.locator('button[type="submit"]')).first

        if await username.count() > 0:
            await username.fill(creds["username"])
        if await password.count() > 0:
            await password.fill(creds["password"])
        if await submit.count() > 0:
            await submit.click(timeout=10000)

        await page.wait_for_load_state("networkidle", timeout=30000)
        os.makedirs(screenshot_dir, exist_ok=True)
        screenshot_path = os.path.join(screenshot_dir, "password_reset_flow.png")
        await page.screenshot(path=screenshot_path, full_page=True)
        result["screenshots"].append(screenshot_path)
    except Exception as exc:
        result = {
            "status": "fail",
            "error": type(exc).__name__ + ": " + str(exc),
            "flow": "password_reset_flow",
            "screenshots": result.get("screenshots", []),
        }
    return result
