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
        # 1. Base Domain context
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
        time.sleep(8)

        # 4. FALLBACK LOGIN LOGIC
        # Check if the login modal is visible (using the placeholder text from your screenshot)
        email_fields = driver.find_elements(By.XPATH, "//input[@placeholder='Enter email address']")
        if email_fields:
            print("Cookies failed. Attempting manual login fallback...")
            email = os.getenv("SKPORT_EMAIL")
            password = os.getenv("SKPORT_PASSWORD")
            
            if email and password:
                # Fill Email
                email_fields[0].send_keys(email)
                # Fill Password
                driver.find_element(By.XPATH, "//input[@placeholder='Enter password']").send_keys(password)
                # Click Log In button
                login_btn = driver.find_element(By.XPATH, "//button[contains(., 'Log in')]")
                driver.execute_script("arguments[0].click();", login_btn)
                
                print("Login submitted. Waiting for redirect...")
                time.sleep(10) # Wait for login to process
            else:
                print("Error: Credentials secrets not found.")

        # 5. Claim logic with JS Click fix
        items = driver.find_elements(By.CLASS_NAME, "sc-nuIvE")
        for item in items:
            if item.find_elements(By.ID, "completed-overlay"):
                continue
                
            if item.find_elements(By.ID, "lottie-container"):
                day_label = item.find_element(By.CLASS_NAME, "sc-guPfGz")
                print(f"Verified {day_label.text} is ready. Claiming...")
                
                target = item.find_element(By.CLASS_NAME, "sc-dltKUw")
                # Use JS Click to bypass the "Obscured" error
                driver.execute_script("arguments[0].click();", target)
                
                print("👍 Click successful.")
                time.sleep(5)
                return 
            
        print("No claimable day found. Check if already signed in.")

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    run_checkin()
