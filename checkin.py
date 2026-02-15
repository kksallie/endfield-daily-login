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
            cookies = json.loads(cookies_raw)
            for cookie in cookies:
                if 'sameSite' in cookie and cookie['sameSite'] not in ["Strict", "Lax", "None"]:
                    del cookie['sameSite']
                driver.add_cookie(cookie)

        # 3. Go to Sign-in page
        driver.get("https://game.skport.com/endfield/sign-in?header=0&hg_media=launcher&hg_link_campaign=icon")
        
        print("Waiting for page to load...")
        time.sleep(10) 

        # 4. AGGRESSIVE LOGIN CHECK
        # We look for the "Please log in first" text which appears for guests
        if "Please log in first" in driver.page_source:
            print("Session not found via cookies. Attempting manual login fallback...")
            
            email = os.getenv("SKPORT_EMAIL")
            password = os.getenv("SKPORT_PASSWORD")
            
            if email and password:
                # Find the email field (it might be inside an iframe or slow to load)
                email_input = driver.find_element(By.XPATH, "//input[@placeholder='Enter email address']")
                email_input.send_keys(email)
                
                pass_input = driver.find_element(By.XPATH, "//input[@placeholder='Enter password']")
                pass_input.send_keys(password)
                
                login_btn = driver.find_element(By.XPATH, "//button[contains(., 'Log in')]")
                driver.execute_script("arguments[0].click();", login_btn)
                
                print("Login clicked. Waiting for the page to reload and settle...")
                time.sleep(20) # Long wait for the redirect/reload you mentioned
            else:
                print("❌ Error: Login required but secrets are missing.")
                return

        # 5. FINAL VERIFICATION
        # If we still see "Please log in first", the login failed.
        if "Please log in first" in driver.page_source:
            print("❌ Critical Error: Still logged out after login attempt. Stopping to avoid Day 1 trap.")
            return

        # 6. CLAIM LOGIC
        print("Login verified. Searching for today's reward...")
        items = driver.find_elements(By.CLASS_NAME, "sc-nuIvE")
        for item in items:
            if item.find_elements(By.ID, "completed-overlay"):
                continue
                
            if item.find_elements(By.ID, "lottie-container"):
                day_label = item.find_element(By.CLASS_NAME, "sc-guPfGz")
                
                # Protection: Don't click Day 1 if we know we are further along
                if "Day 1" in day_label.text:
                    print(f"🛑 Refusing to click {day_label.text}. Logic suggests we are still seeing the guest view.")
                    return

                print(f"Targeting active day: {day_label.text}")
                target = item.find_element(By.CLASS_NAME, "sc-dltKUw")
                driver.execute_script("arguments[0].click();", target)
                print("👍 Click performed on the correct day.")
                time.sleep(5)
                return 
            
        print("No claimable day found. You might be already signed in.")

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    run_checkin()
