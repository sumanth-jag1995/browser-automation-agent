import asyncio
import json
import os
from pathlib import Path

async def run(page, url: str, screenshot_dir: str) -> dict:
    """
    Automation script for login_forgot_password flow.
    Tests the forgot password functionality on the OrangeHRM login page.
    """
    screenshots = []
    try:
        # Route to abort external font loading to prevent timeout
        await page.route('**/*.woff2', lambda route: route.abort())
        await page.route('**/*.woff', lambda route: route.abort())
        await page.route('**/*.ttf', lambda route: route.abort())
        
        # Navigate to the login page
        await page.goto(url, wait_until='load')
        await page.wait_for_load_state('domcontentloaded')
        await page.wait_for_load_state('networkidle')
        await page.wait_for_timeout(500)
        
        # Take initial screenshot with increased timeout and visible area only
        initial_screenshot = os.path.join(screenshot_dir, 'login_forgot_password_01_initial.png')
        await page.screenshot(path=initial_screenshot, full_page=False, timeout=20000)
        screenshots.append(initial_screenshot)
        
        # Look for the "Forgot your password?" or similar link
        forgot_password_link = None
        
        # Try multiple ways to find the forgot password link
        try:
            forgot_password_link = page.get_by_role('link', name='Forgot your password')
            if await forgot_password_link.is_visible(timeout=5000):
                pass
            else:
                forgot_password_link = None
        except:
            forgot_password_link = None
        
        if not forgot_password_link:
            try:
                forgot_password_link = page.get_by_text('Forgot your password')
                if await forgot_password_link.is_visible(timeout=5000):
                    pass
                else:
                    forgot_password_link = None
            except:
                forgot_password_link = None
        
        if not forgot_password_link:
            try:
                forgot_password_link = page.locator('a:has-text("Forgot your password")')
                if await forgot_password_link.is_visible(timeout=5000):
                    pass
                else:
                    forgot_password_link = None
            except:
                forgot_password_link = None
        
        if not forgot_password_link:
            try:
                forgot_password_link = page.locator('[href*="password"]')
                if await forgot_password_link.is_visible(timeout=5000):
                    pass
                else:
                    forgot_password_link = None
            except:
                forgot_password_link = None
        
        if forgot_password_link:
            # Click the forgot password link
            await forgot_password_link.click()
            await page.wait_for_load_state('domcontentloaded')
            await page.wait_for_load_state('networkidle')
            await page.wait_for_timeout(500)
            
            # Take screenshot after clicking forgot password
            forgot_password_form_screenshot = os.path.join(screenshot_dir, 'login_forgot_password_02_form.png')
            await page.screenshot(path=forgot_password_form_screenshot, full_page=False, timeout=20000)
            screenshots.append(forgot_password_form_screenshot)
            
            # Load credentials from the JSON file
            credentials_path = r'D:\04_Self\10_Agents\02_Projects\04_Browser_Automation_Agent\browser-automation-agent\test_data\credentials.json'
            username = 'Admin'
            
            if os.path.exists(credentials_path):
                try:
                    with open(credentials_path, 'r') as f:
                        credentials_data = json.load(f)
                        if 'login' in credentials_data and 'username' in credentials_data['login']:
                            username = credentials_data['login']['username']
                except:
                    pass
            
            # Find the username/email input field
            username_input = None
            try:
                username_input = page.get_by_label('Username')
                if await username_input.is_visible(timeout=5000):
                    pass
                else:
                    username_input = None
            except:
                username_input = None
            
            if not username_input:
                try:
                    username_input = page.get_by_placeholder('Username')
                    if await username_input.is_visible(timeout=5000):
                        pass
                    else:
                        username_input = None
                except:
                    username_input = None
            
            if not username_input:
                try:
                    username_input = page.locator('input[name="username"]')
                    if await username_input.is_visible(timeout=5000):
                        pass
                    else:
                        username_input = None
                except:
                    username_input = None
            
            if not username_input:
                try:
                    username_input = page.locator('input[type="text"]').first
                    if await username_input.is_visible(timeout=5000):
                        pass
                    else:
                        username_input = None
                except:
                    username_input = None
            
            if username_input:
                # Fill in the username
                await username_input.fill(username)
                await page.wait_for_timeout(500)
                
                # Take screenshot after filling username
                filled_username_screenshot = os.path.join(screenshot_dir, 'login_forgot_password_03_filled.png')
                await page.screenshot(path=filled_username_screenshot, full_page=False, timeout=20000)
                screenshots.append(filled_username_screenshot)
                
                # Look for the submit button
                submit_button = None
                try:
                    submit_button = page.get_by_role('button', name='Reset Password')
                    if await submit_button.is_visible(timeout=5000):
                        pass
                    else:
                        submit_button = None
                except:
                    submit_button = None
                
                if not submit_button:
                    try:
                        submit_button = page.get_by_role('button', name='Submit')
                        if await submit_button.is_visible(timeout=5000):
                            pass
                        else:
                            submit_button = None
                    except:
                        submit_button = None
                
                if not submit_button:
                    try:
                        submit_button = page.locator('button:has-text("Reset Password")')
                        if await submit_button.is_visible(timeout=5000):
                            pass
                        else:
                            submit_button = None
                    except:
                        submit_button = None
                
                if not submit_button:
                    try:
                        submit_button = page.locator('button[type="submit"]')
                        if await submit_button.is_visible(timeout=5000):
                            pass
                        else:
                            submit_button = None
                    except:
                        submit_button = None
                
                if submit_button:
                    # Click the submit button
                    await submit_button.click()
                    await page.wait_for_load_state('domcontentloaded')
                    await page.wait_for_load_state('networkidle')
                    await page.wait_for_timeout(500)
                    
                    # Take final screenshot
                    final_screenshot = os.path.join(screenshot_dir, 'login_forgot_password_04_result.png')
                    await page.screenshot(path=final_screenshot, full_page=False, timeout=20000)
                    screenshots.append(final_screenshot)
                    
                    return {
                        'status': 'success',
                        'screenshots': screenshots
                    }
                else:
                    return {
                        'status': 'fail',
                        'error': 'Submit button not found',
                        'screenshots': screenshots
                    }
            else:
                return {
                    'status': 'fail',
                    'error': 'Username input field not found',
                    'screenshots': screenshots
                }
        else:
            return {
                'status': 'fail',
                'error': 'Forgot password link not found on login page',
                'screenshots': screenshots
            }
    
    except Exception as e:
        error_screenshot = os.path.join(screenshot_dir, 'login_forgot_password_error.png')
        try:
            await page.screenshot(path=error_screenshot, full_page=False, timeout=20000)
            screenshots.append(error_screenshot)
        except:
            pass
        
        return {
            'status': 'fail',
            'error': str(e),
            'screenshots': screenshots
        }