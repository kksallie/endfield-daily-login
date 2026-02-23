import os
import json
import time
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def run_checkin():
    options = Options()
    options.add_argument("--headless")
    options.set_preference("general.useragent.override", "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0")
    driver = webdriver.Firefox(options=options)
    driver.set_window_size(1920, 1080)
    
    try:
        # 1. Base Domain
        driver.get("https://game.skport.com")

        # 2. Inject Cookies
        cookies_raw = os.getenv("SKPORT_COOKIES")
        if cookies_raw:
            try:
                cookies = json.loads(cookies_raw)
                for cookie in cookies:
                    # Clean sameSite (Selenium only likes specific strings)
                    if 'sameSite' in cookie:
                        if isinstance(cookie['sameSite'], str):
                            ss = cookie['sameSite'].capitalize()
                            if ss in ["Strict", "Lax", "None"]:
                                cookie['sameSite'] = ss
                            else:
                                del cookie['sameSite']
                        else:
                            del cookie['sameSite']
                    
                    # Fix domain issues to prevent "InvalidCookieDomainError"
                    if 'domain' in cookie:
                        del cookie['domain']
                    driver.add_cookie(cookie)
                print("✅ Cookies injected successfully.")
            except Exception as e:
                print(f"⚠️ Cookie injection warning: {e}")

        # 3. Go to Sign-in page
        driver.get("https://game.skport.com/endfield/sign-in?header=0&hg_media=launcher&hg_link_campaign=icon")
        print("Waiting for page load and session check...")
        time.sleep(15)

        # 4. Ensure the grid is expanded
        try:
            show_all_btn = driver.find_element(By.CLASS_NAME, "sc-BvjM")
            if "Show All" in show_all_btn.text:
                driver.execute_script("arguments[0].click();", show_all_btn)
                print("Expanded the reward grid.")
                time.sleep(2)
        except:
            pass

        # 5. ROBUST LOGIN FALLBACK
        email_fields = driver.find_elements(By.NAME, "email")
        if email_fields:
            print("Login modal detected. Attempting credentials fallback...")
            email = os.getenv("SKPORT_EMAIL")
            password = os.getenv("SKPORT_PASSWORD")
            if email and password:
                email_fields[0].send_keys(email)
                pass_field = driver.find_element(By.XPATH, "//input[@type='password']")
                pass_field.send_keys(password)
                
                # Using a generic selector for login button to avoid masking issues
                login_btn = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
                driver.execute_script("arguments[0].click();", login_btn)
                print("Login submitted. Waiting for the post-login reload...")
                time.sleep(25)
            else:
                print("❌ Error: Login required but secrets (EMAIL/PASSWORD) are missing.")
                return

        # 6. FINAL GUEST CHECK
        # Simplified XPath to avoid potential GitHub secret masking conflicts
        login_check = driver.find_elements(By.XPATH, "//*[text()='Please log in first']")
        if login_check:
            print("❌ Critical Error: Login failed. 'Please log in first' message is still visible.")
            return

        # 7. CLAIM LOGIC
        print("Login verified. Locating correct reward day...")
        items = driver.find_elements(By.CLASS_NAME, "sc-nuIvE")
        for item in items:
            # Skip if checkmark exists
            if item.find_elements(By.ID, "completed-overlay"):
                continue
            
            # Find the glowing 'claimable' day
            if item.find_elements(By.ID, "lottie-container"):
                day_label = item.find_element(By.CLASS_NAME, "sc-guPfGz")
                print(f"Found active reward: {day_label.text}. Clicking...")
                target = item.find_element(By.CLASS_NAME, "sc-dltKUw")
                driver.execute_script("arguments[0].click();", target)
                print("✅ Success: Claim action triggered.")
                time.sleep(5)
                return
        
        print("No claimable day found. You might be already signed in.")

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    run_checkin()
