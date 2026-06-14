import asyncio
import json
import os
from pathlib import Path
from playwright.async_api import async_playwright, expect

async def run(page, url: str, screenshot_dir: str) -> dict:
    """
    Flow: login_with_invalid_credentials
    Tests logging in with invalid credentials on OrangeHRM demo site.
    """
    screenshots = []
    flow_name = "login_with_invalid_credentials"
    
    try:
        # Load credentials from JSON file
        credentials_file = r"D:\04_Self\10_Agents\02_Projects\04_Browser_Automation_Agent\browser-automation-agent\test_data\credentials.json"
        credentials = {"username": "Admin", "password": "admin123"}
        
        if os.path.exists(credentials_file):
            with open(credentials_file, 'r') as f:
                creds_data = json.load(f)
                if 'login' in creds_data:
                    credentials = creds_data['login']
        
        # Navigate to login page
        await page.goto(url, wait_until="domcontentloaded")
        await page.wait_for_load_state("networkidle")
        
        # Wait for login form to be visible
        await page.wait_for_selector("input[name='username']", timeout=10000)
        
        # Use invalid credentials (append "_invalid" to the actual credentials)
        invalid_username = credentials.get("username", "Admin") + "_invalid"
        invalid_password = credentials.get("password", "admin123") + "_invalid"
        
        # Fill username field with invalid credentials
        username_field = page.locator("input[name='username']").first
        await username_field.fill(invalid_username)
        
        # Fill password field with invalid credentials
        password_field = page.locator("input[name='password']").first
        await password_field.fill(invalid_password)
        
        # Take screenshot before login attempt
        screenshot_path_before = os.path.join(screenshot_dir, f"{flow_name}_before_submit.png")
        await page.screenshot(path=screenshot_path_before, full_page=True)
        screenshots.append(screenshot_path_before)
        
        # Click login button
        login_button = page.locator("button[type='submit']").first
        await login_button.click()
        
        # Wait for error message to appear (indicating failed login)
        await page.wait_for_timeout(2000)  # Allow time for error to appear
        
        # Check for error message or stay on login page
        error_message = page.locator("div[role='alert'], .oxd-alert-content, span.error").first
        
        # Wait for error message to be visible
        try:
            await expect(error_message).to_be_visible(timeout=5000)
        except:
            # If no specific error element, check if we're still on login page
            await page.wait_for_selector("input[name='username']", timeout=5000)
        
        # Take screenshot after login attempt showing error
        screenshot_path_after = os.path.join(screenshot_dir, f"{flow_name}_after_submit.png")
        await page.screenshot(path=screenshot_path_after, full_page=True)
        screenshots.append(screenshot_path_after)
        
        # Verify we're still on login page (not logged in)
        current_url = page.url
        if "login" not in current_url.lower():
            return {
                "status": "fail",
                "error": "Expected to remain on login page after invalid login attempt, but URL changed to: " + current_url,
                "flow": flow_name,
                "screenshots": screenshots
            }
        
        return {
            "status": "success",
            "screenshots": screenshots,
            "flow": flow_name
        }
        
    except Exception as e:
        screenshot_path_error = os.path.join(screenshot_dir, f"{flow_name}_error.png")
        try:
            await page.screenshot(path=screenshot_path_error, full_page=True)
            screenshots.append(screenshot_path_error)
        except:
            pass
        
        return {
            "status": "fail",
            "error": str(e),
            "flow": flow_name,
            "screenshots": screenshots
        }