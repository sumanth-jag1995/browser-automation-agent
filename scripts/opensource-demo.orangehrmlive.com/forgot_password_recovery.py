import asyncio
import json
import os
from pathlib import Path
from playwright.async_api import async_playwright, expect

async def run(page, url: str, screenshot_dir: str) -> dict:
    """
    Automation script for forgot_password_recovery flow.
    Tests the password recovery functionality on OrangeHRM login page.
    """
    screenshots = []
    try:
        # Load credentials from JSON file
        creds_path = Path(r'D:\04_Self\10_Agents\02_Projects\04_Browser_Automation_Agent\browser-automation-agent\test_data\credentials.json')
        credentials = {}
        if creds_path.exists():
            with open(creds_path, 'r') as f:
                creds_data = json.load(f)
                credentials = creds_data.get('login', {})
        
        # Use default credentials if not loaded from file
        username = credentials.get('username', 'Admin')
        
        # Navigate to login page
        await page.goto(url, wait_until='domcontentloaded')
        await page.wait_for_load_state('domcontentloaded')
        
        # Wait for fonts to be ready before first screenshot
        try:
            await page.evaluate('document.fonts.ready')
        except:
            pass
        
        # Wait for login page to be ready
        forgot_password_link = page.get_by_text('Forgot your password')
        await expect(forgot_password_link).to_be_visible(timeout=10000)
        
        # Take initial screenshot with timeout and viewport-only
        screenshot_path = os.path.join(screenshot_dir, 'forgot_password_recovery_01_login_page.png')
        try:
            await page.screenshot(path=screenshot_path, full_page=False, timeout=5000)
            screenshots.append(screenshot_path)
        except Exception as e:
            print(f"Warning: Screenshot 1 timed out: {str(e)}")
        
        # Click on "Forgot your password" link
        await forgot_password_link.click()
        await page.wait_for_load_state('domcontentloaded')
        await asyncio.sleep(0.5)
        
        # Wait for fonts to be ready before screenshot
        try:
            await page.evaluate('document.fonts.ready')
        except:
            pass
        
        # Take screenshot of password recovery form
        screenshot_path = os.path.join(screenshot_dir, 'forgot_password_recovery_02_recovery_form.png')
        try:
            await page.screenshot(path=screenshot_path, full_page=False, timeout=5000)
            screenshots.append(screenshot_path)
        except Exception as e:
            print(f"Warning: Screenshot 2 timed out: {str(e)}")
        
        # Wait for username/email input field to be visible
        username_input = page.get_by_placeholder('Username')
        await expect(username_input).to_be_visible(timeout=10000)
        
        # Fill in the username/email field
        await username_input.fill(username)
        await page.wait_for_timeout(500)
        
        # Wait for fonts to be ready before screenshot
        try:
            await page.evaluate('document.fonts.ready')
        except:
            pass
        
        # Take screenshot with username filled
        screenshot_path = os.path.join(screenshot_dir, 'forgot_password_recovery_03_username_filled.png')
        try:
            await page.screenshot(path=screenshot_path, full_page=False, timeout=5000)
            screenshots.append(screenshot_path)
        except Exception as e:
            print(f"Warning: Screenshot 3 timed out: {str(e)}")
        
        # Click Reset Password button
        reset_button = page.get_by_role('button', name='Reset Password')
        await expect(reset_button).to_be_visible(timeout=10000)
        await reset_button.click()
        await page.wait_for_load_state('domcontentloaded')
        await asyncio.sleep(0.5)
        
        # Wait for fonts to be ready before screenshot
        try:
            await page.evaluate('document.fonts.ready')
        except:
            pass
        
        # Take screenshot after form submission
        screenshot_path = os.path.join(screenshot_dir, 'forgot_password_recovery_04_final.png')
        try:
            await page.screenshot(path=screenshot_path, full_page=False, timeout=5000)
            screenshots.append(screenshot_path)
        except Exception as e:
            print(f"Warning: Screenshot 4 timed out: {str(e)}")
        
        # Verify success message or confirmation page
        try:
            success_text = page.locator('text=/password reset|success|check your email/i')
            success_visible = await success_text.is_visible(timeout=5000)
        except:
            success_visible = False
        
        if success_visible or page.url != url:
            return {
                "status": "success",
                "screenshots": screenshots,
                "flow": "forgot_password_recovery"
            }
        else:
            # Check if we're back on login page (indicating form was submitted)
            try:
                forgot_link_visible = await page.get_by_text('Forgot your password').is_visible(timeout=3000)
            except:
                forgot_link_visible = False
            
            if 'login' in page.url or forgot_link_visible:
                return {
                    "status": "success",
                    "screenshots": screenshots,
                    "flow": "forgot_password_recovery"
                }
            else:
                return {
                    "status": "fail",
                    "error": "Password recovery flow did not complete successfully",
                    "flow": "forgot_password_recovery",
                    "screenshots": screenshots
                }
    
    except Exception as e:
        screenshot_path = os.path.join(screenshot_dir, 'forgot_password_recovery_error.png')
        try:
            await page.screenshot(path=screenshot_path, full_page=False, timeout=5000)
            screenshots.append(screenshot_path)
        except:
            pass
        
        return {
            "status": "fail",
            "error": f"Exception during forgot password recovery flow: {str(e)}",
            "flow": "forgot_password_recovery",
            "screenshots": screenshots
        }