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
        # 1. Domain Context
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
        
        # 4. WAIT FOR LOGIN STATE
        # We wait up to 15 seconds to see if the Login Modal appears OR the grid loads
        print("Waiting for page to determine login state...")
        time.sleep(10) 

        # Check for the email input field specifically
        email_fields = driver.find_elements(By.XPATH, "//input[@placeholder='Enter email address']")
        
        if email_fields:
            print("Detected Login Modal. Attempting manual login fallback...")
            email = os.getenv("SKPORT_EMAIL")
            password = os.getenv("SKPORT_PASSWORD")
            
            if email and password:
                email_fields[0].send_keys(email)
                driver.find_element(By.XPATH, "//input[@placeholder='Enter password']").send_keys(password)
                login_btn = driver.find_element(By.XPATH, "//button[contains(., 'Log in')]")
                driver.execute_script("arguments[0].click();", login_btn)
                print("Credentials submitted. Waiting for page refresh...")
                time.sleep(15) # Essential: wait for the account-specific grid to load
            else:
                print("❌ Error: Login required but SKPORT_EMAIL/PASSWORD secrets are missing.")
                return

        # 5. VERIFY CORRECT DAY (Avoid Guest Day 1)
        # If we are logged in, we shouldn't see 'Day 1' as ready if you are on Day 6
        items = driver.find_elements(By.CLASS_NAME, "sc-nuIvE")
        for item in items:
            if item.find_elements(By.ID, "completed-overlay"):
                continue
                
            if item.find_elements(By.ID, "lottie-container"):
                day_label = item.find_element(By.CLASS_NAME, "sc-guPfGz")
                
                # Double check: if it still says Day 1, we are likely still not logged in right
                if "Day 1" in day_label.text:
                    print(f"⚠️ Warning: Script sees {day_label.text} as active. This usually means login still failed.")
                
                print(f"Targeting active day: {day_label.text}")
                target = item.find_element(By.CLASS_NAME, "sc-dltKUw")
                driver.execute_script("arguments[0].click();", target)
                print("👍 Click performed on the active day.")
                time.sleep(5)
                return 
            
        print("No claimable day found. You might be already signed in.")

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    run_checkin()
