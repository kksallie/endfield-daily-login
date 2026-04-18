import os
import json
import time
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By

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
                    if 'sameSite' in cookie:
                        if isinstance(cookie['sameSite'], str):
                            ss = cookie['sameSite'].capitalize()
                            if ss in ["Strict", "Lax", "None"]:
                                cookie['sameSite'] = ss
                            else:
                                del cookie['sameSite']
                        else:
                            del cookie['sameSite']
                    if 'domain' in cookie:
                        del cookie['domain']
                    driver.add_cookie(cookie)
                print("✅ Cookies injected.")
            except Exception as e:
                print(f"⚠️ Cookie warning: {e}")

        # 3. Load Page
        url = "https://game.skport.com/endfield/sign-in?header=0&hg_media=launcher&hg_link_campaign=icon"
        driver.get(url)
        print("Waiting for page load...")
        time.sleep(15)

        # 4. Expand Grid (using CSS instead of XPath)
        try:
            show_all_btn = driver.find_element(By.CSS_SELECTOR, ".sc-BvjM")
            driver.execute_script("arguments[0].click();", show_all_btn)
            print("Grid expanded.")
            time.sleep(2)
        except:
            pass

        # 5. Login Fallback (using CSS to avoid masking)
        email_fields = driver.find_elements(By.NAME, "email")
        if email_fields:
            print("Login required. Using credentials...")
            email = os.getenv("SKPORT_EMAIL")
            password = os.getenv("SKPORT_PASSWORD")
            if email and password:
                email_fields[0].send_keys(email)
                # Avoid XPath for password
                pass_field = driver.find_element(By.CSS_SELECTOR, "input[type='password']")
                pass_field.send_keys(password)
                
                login_btn = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
                driver.execute_script("arguments[0].click();", login_btn)
                time.sleep(25)
            else:
                print("❌ Missing credentials.")
                return

        # 6. Check for Login Error (Neutralized check)
        # Use a generic CSS selector to find the error container
        error_elements = driver.find_elements(By.CSS_SELECTOR, ".sc-hLseeU")
        if any("Please log in first" in e.text for e in error_elements):
            print("❌ Login failed.")
            return

        # 7. Claim Logic
        print("Searching for reward...")
        items = driver.find_elements(By.CSS_SELECTOR, ".sc-nuIvE")
        for item in items:
            if item.find_elements(By.ID, "completed-overlay"):
                continue
            
            if item.find_elements(By.ID, "lottie-container"):
                print("Found claimable day. Clicking...")
                target = item.find_element(By.CSS_SELECTOR, ".sc-dltKUw")
                driver.execute_script("arguments[0].click();", target)
                print("✅ Success!")
                time.sleep(5)
                return
        
        print("Already signed in or no rewards available.")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    run_checkin()
