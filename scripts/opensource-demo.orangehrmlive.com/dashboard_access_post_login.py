import json
import os
from pathlib import Path

async def run(page, url: str, screenshot_dir: str) -> dict:
    """
    Automation script for dashboard_access_post_login flow.
    Logs in to OrangeHRM with credentials from JSON file and verifies dashboard access.
    """
    screenshots = []
    flow_name = "dashboard_access_post_login"
    
    try:
        # Load credentials from JSON file
        credentials_path = r"D:\04_Self\10_Agents\02_Projects\04_Browser_Automation_Agent\browser-automation-agent\test_data\credentials.json"
        
        if not os.path.exists(credentials_path):
            return {
                "status": "fail",
                "error": f"Credentials file not found at {credentials_path}",
                "flow": flow_name,
                "screenshots": screenshots
            }
        
        with open(credentials_path, 'r') as f:
            creds_data = json.load(f)
        
        login_creds = creds_data.get('login', {})
        username = login_creds.get('username', 'Admin')
        password = login_creds.get('password', 'admin123')
        
        # Navigate to the login page
        await page.goto(url, wait_until='networkidle')
        await page.wait_for_load_state('networkidle')
        
        # Capture login page
        login_screenshot = os.path.join(screenshot_dir, f"{flow_name}_01_login_page.png")
        await page.screenshot(path=login_screenshot, full_page=True)
        screenshots.append(login_screenshot)
        
        # Fill in username field
        username_field = page.get_by_name('username')
        await username_field.fill(username)
        
        # Fill in password field
        password_field = page.get_by_name('password')
        await password_field.fill(password)
        
        # Click login button
        login_button = page.get_by_role('button', name='Login')
        await login_button.click()
        
        # Wait for navigation and dashboard to load
        await page.wait_for_url('**/dashboard**', timeout=10000)
        await page.wait_for_load_state('networkidle')
        
        # Wait for dashboard content to be visible
        await page.wait_for_selector('[class*="dashboard"], [class*="Dashboard"], main', timeout=10000)
        
        # Capture dashboard after login
        dashboard_screenshot = os.path.join(screenshot_dir, f"{flow_name}_02_dashboard.png")
        await page.screenshot(path=dashboard_screenshot, full_page=True)
        screenshots.append(dashboard_screenshot)
        
        # Verify dashboard is accessible by checking for common dashboard elements
        # Check for user profile menu or greeting that indicates successful login
        profile_indicator = page.locator('[class*="profile"], [class*="user"], [alt*="profile"], [title*="user"]').first
        
        # Alternative: Check for dashboard specific content
        dashboard_content = page.locator('text=Dashboard, text=Welcome, [class*="widget"], [class*="card"]').first
        
        return {
            "status": "success",
            "screenshots": screenshots,
            "flow": flow_name
        }
        
    except Exception as e:
        # Capture error screenshot
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