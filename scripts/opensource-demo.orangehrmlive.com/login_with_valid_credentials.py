import json
import os
from pathlib import Path
from datetime import datetime

async def run(page, url: str, screenshot_dir: str) -> dict:
    """
    Login flow with valid credentials for Orange HRM demo site.
    Loads credentials from JSON file and performs login validation.
    """
    flow_name = "login_with_valid_credentials"
    screenshots = []
    
    try:
        # Load credentials from JSON file
        credentials_file = Path("D:\\04_Self\\10_Agents\\02_Projects\\04_Browser_Automation_Agent\\browser-automation-agent\\test_data\\credentials.json")
        
        if not credentials_file.exists():
            return {
                "status": "fail",
                "error": f"Credentials file not found at {credentials_file}",
                "flow": flow_name,
                "screenshots": screenshots
            }
        
        with open(credentials_file, 'r') as f:
            creds_data = json.load(f)
        
        # Extract login credentials from 'login' key
        login_creds = creds_data.get('login', {})
        username = login_creds.get('username', 'Admin')
        password = login_creds.get('password', 'admin123')
        
        # Navigate to the login page
        await page.goto(url, wait_until='load')
        await page.wait_for_load_state('networkidle')
        
        # Take screenshot of login page
        login_page_screenshot = os.path.join(screenshot_dir, f"{flow_name}_01_login_page.png")
        await page.screenshot(path=login_page_screenshot, full_page=True)
        screenshots.append(login_page_screenshot)
        
        # Locate and fill username field
        username_field = page.get_by_placeholder("Username")
        await username_field.wait_for(timeout=5000)
        await username_field.fill(username)
        
        # Locate and fill password field
        password_field = page.get_by_placeholder("Password")
        await password_field.fill(password)
        
        # Take screenshot before login
        before_login_screenshot = os.path.join(screenshot_dir, f"{flow_name}_02_before_login.png")
        await page.screenshot(path=before_login_screenshot, full_page=True)
        screenshots.append(before_login_screenshot)
        
        # Click login button
        login_button = page.get_by_role("button", name="Login")
        await login_button.click()
        
        # Wait for navigation and page load
        await page.wait_for_load_state('networkidle')
        await page.wait_for_timeout(2000)  # Additional wait for dashboard to fully load
        
        # Verify successful login by checking for dashboard elements
        dashboard_header = page.get_by_role("heading").first
        await dashboard_header.wait_for(timeout=10000)
        
        # Take screenshot of successful login
        success_screenshot = os.path.join(screenshot_dir, f"{flow_name}_03_dashboard.png")
        await page.screenshot(path=success_screenshot, full_page=True)
        screenshots.append(success_screenshot)
        
        # Verify we're on a different page (successful login)
        current_url = page.url
        if "login" in current_url.lower():
            return {
                "status": "fail",
                "error": "Still on login page after login attempt. Authentication may have failed.",
                "flow": flow_name,
                "screenshots": screenshots
            }
        
        return {
            "status": "success",
            "screenshots": screenshots,
            "flow": flow_name
        }
        
    except Exception as e:
        error_screenshot = os.path.join(screenshot_dir, f"{flow_name}_error.png")
        try:
            await page.screenshot(path=error_screenshot, full_page=True)
            screenshots.append(error_screenshot)
        except:
            pass
        
        return {
            "status": "fail",
            "error": str(e),
            "flow": flow_name,
            "screenshots": screenshots
        }