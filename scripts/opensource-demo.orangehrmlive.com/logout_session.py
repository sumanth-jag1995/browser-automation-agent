import asyncio
import json
import os
from pathlib import Path
from playwright.async_api import async_playwright

async def run(page, url: str, screenshot_dir: str) -> dict:
    """
    Automation flow for logging out a session.
    Flow: logout_session
    """
    screenshots = []
    try:
        # Navigate to the login page
        await page.goto(url, wait_until="load")
        await page.wait_for_load_state("networkidle")
        
        # Login with default credentials
        username_field = page.get_by_placeholder("Username")
        password_field = page.get_by_placeholder("Password")
        login_button = page.get_by_role("button", name="Login")
        
        # Wait for fields to be visible
        await username_field.wait_for(state="visible", timeout=10000)
        await password_field.wait_for(state="visible", timeout=10000)
        
        # Fill in credentials
        await username_field.fill("Admin")
        await password_field.fill("admin123")
        
        # Click login button
        await login_button.click()
        
        # Wait for dashboard to load after login
        await page.wait_for_load_state("networkidle", timeout=30000)
        await page.wait_for_timeout(1000)
        
        # Find and click the user profile/dropdown menu
        # Usually located at top right corner
        user_menu = page.get_by_role("img", name="profile picture").or_(page.locator("button[class*='user']")).or_(page.locator("div[class*='profile']//button")).first
        
        # Try alternative selectors for the dropdown
        dropdown_button = page.locator("button").filter(has=page.locator("img[alt*='profile']")).first
        if not await dropdown_button.is_visible(timeout=5000):
            dropdown_button = page.locator("//button[contains(@class, 'oxd-userdropdown-tab')]").first
        
        # Take screenshot before logout
        screenshot_path_before = os.path.join(screenshot_dir, "logout_session_before.png")
        os.makedirs(screenshot_dir, exist_ok=True)
        await page.screenshot(path=screenshot_path_before, full_page=True)
        screenshots.append(screenshot_path_before)
        
        # Click the dropdown/profile button
        await dropdown_button.click(timeout=10000)
        await page.wait_for_timeout(500)
        
        # Find and click the logout option
        logout_option = page.get_by_text("Logout", exact=True).or_(page.locator("a").filter(has_text="Logout")).or_(page.locator("button").filter(has_text="Logout")).first
        
        await logout_option.click(timeout=10000)
        
        # Wait for redirect to login page
        await page.wait_for_load_state("networkidle", timeout=30000)
        await page.wait_for_timeout(1000)
        
        # Verify logout was successful by checking for login page elements
        login_button_verify = page.get_by_role("button", name="Login")
        await login_button_verify.wait_for(state="visible", timeout=10000)
        
        # Take final screenshot
        screenshot_path = os.path.join(screenshot_dir, "logout_session.png")
        await page.screenshot(path=screenshot_path, full_page=True)
        screenshots.append(screenshot_path)
        
        return {
            "status": "success",
            "screenshots": screenshots,
            "flow": "logout_session"
        }
        
    except Exception as e:
        # Take screenshot on failure
        error_screenshot_path = os.path.join(screenshot_dir, "logout_session_error.png")
        os.makedirs(screenshot_dir, exist_ok=True)
        try:
            await page.screenshot(path=error_screenshot_path, full_page=True)
            screenshots.append(error_screenshot_path)
        except:
            pass
        
        return {
            "status": "fail",
            "error": str(e),
            "flow": "logout_session",
            "screenshots": screenshots
        }