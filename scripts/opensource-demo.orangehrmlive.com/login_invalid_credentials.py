import asyncio
import json
import os
from pathlib import Path
from playwright.async_api import async_playwright, expect

async def run(page, url: str, screenshot_dir: str) -> dict:
    """
    Automation script for login_invalid_credentials flow.
    Tests login with invalid credentials on OrangeHRM demo site.
    """
    screenshots = []
    try:
        # Load credentials from JSON file
        credentials_file = r'D:\04_Self\10_Agents\02_Projects\04_Browser_Automation_Agent\browser-automation-agent\test_data\credentials.json'
        
        invalid_username = 'InvalidUser'
        invalid_password = 'WrongPassword123'
        
        if os.path.exists(credentials_file):
            with open(credentials_file, 'r') as f:
                creds_data = json.load(f)
                if 'login' in creds_data:
                    # Use invalid credentials for testing
                    invalid_username = creds_data['login'].get('invalid_username', invalid_username)
                    invalid_password = creds_data['login'].get('invalid_password', invalid_password)
        
        # Navigate to the login page
        await page.goto(url, wait_until='networkidle')
        await page.wait_for_load_state('networkidle')
        
        # Wait for username field to be visible using locator for backward compatibility
        username_field = page.locator('input[name="username"]')
        await expect(username_field).to_be_visible(timeout=5000)
        
        # Fill in invalid username
        await username_field.fill(invalid_username)
        
        # Fill in invalid password using locator for backward compatibility
        password_field = page.locator('input[name="password"]')
        await expect(password_field).to_be_visible(timeout=5000)
        await password_field.fill(invalid_password)
        
        # Click the login button
        login_button = page.locator('button:has-text("Login")')
        await expect(login_button).to_be_visible(timeout=5000)
        await login_button.click()
        
        # Wait for error message to appear
        await page.wait_for_timeout(2000)
        
        # Check for error message
        error_message = page.locator('[role="alert"]')
        await expect(error_message).to_be_visible(timeout=5000)
        
        # Verify we're still on the login page (not logged in)
        await expect(page).to_have_url(url, timeout=5000)
        
        # Take a screenshot showing the error state
        screenshot_path = os.path.join(screenshot_dir, 'login_invalid_credentials.png')
        await page.screenshot(path=screenshot_path, full_page=True)
        screenshots.append(screenshot_path)
        
        return {
            'status': 'success',
            'screenshots': screenshots,
            'flow': 'login_invalid_credentials'
        }
        
    except Exception as e:
        # Take a screenshot on failure
        try:
            screenshot_path = os.path.join(screenshot_dir, 'login_invalid_credentials_error.png')
            await page.screenshot(path=screenshot_path, full_page=True)
            screenshots.append(screenshot_path)
        except:
            pass
        
        return {
            'status': 'fail',
            'error': str(e),
            'flow': 'login_invalid_credentials',
            'screenshots': screenshots
        }
