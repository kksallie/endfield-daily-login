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
                    # 1. Fix sameSite case (Strict/Lax/None)
                    if 'sameSite' in cookie and cookie['sameSite']:
                        ss = str(cookie['sameSite']).capitalize()
                        if ss in ["Strict", "Lax", "None"]:
                            cookie['sameSite'] = ss
                        else:
                            del cookie['sameSite']
                    
                    # 2. Skip incompatible subdomains
                    domain = cookie.get('domain', '')
                    clean_domain = domain[1:] if domain.startswith('.') else domain
                    
                    if clean_domain in ["skport.com", "game.skport.com"]:
                        driver.add_cookie(cookie)
                    else:
                        print(f"Skipping cookie {cookie.get('name')} for domain {domain}")
            except Exception as e:
                print(f"Cookie injection warning: {e}")

        # 3. Go to Sign-in page
        driver.get("https://game.skport.com/endfield/sign-in?header=0&hg_media=launcher&hg_link_campaign=icon")
        
        print("Waiting for page load and session check...")
        time.sleep(12) 

        # 4. ROBUST LOGIN FALLBACK
        # We check for the email field by its 'name' attribute which we saw in your HTML
        email_fields = driver.find_elements(By.NAME, "email")
        
        if email_fields:
            print("Login modal detected. Attempting credentials fallback...")
            email = os.getenv("SKPORT_EMAIL")
            password = os.getenv("SKPORT_PASSWORD")
            
            if email and password:
                # Fill Email
                email_fields[0].send_keys(email)
                
                # Find Password field by type
                pass_field = driver.find_element(By.XPATH, "//input[@type='password']")
                pass_field.send_keys(password)
                
                # Click the Log In button by its type
                login_btn = driver.find_element(By.XPATH, "//button[@type='submit' and contains(., 'Log in')]")
                driver.execute_script("arguments[0].click();", login_btn)
                
                print("Login submitted. Waiting for the post-login reload...")
                # The page reloads after login, so we wait extra time for it to settle
                time.sleep(25) 
            else:
                print("❌ Error: Login required but secrets (EMAIL/PASSWORD) are missing.")
                return

        # 5. FINAL GUEST CHECK
        if "Please log in first" in driver.page_source:
            print("❌ Critical Error: Still seeing 'Please log in first'. Login failed.")
            return

        # 6. CLAIM LOGIC
        print("Login verified. Locating correct reward day...")
        items = driver.find_elements(By.CLASS_NAME, "sc-nuIvE")
        for item in items:
            # Skip if checkmark exists
            if item.find_elements(By.ID, "completed-overlay"):
                continue
                
            # Find the glowing 'claimable' day
            if item.find_elements(By.ID, "lottie-container"):
                day_label = item.find_element(By.CLASS_NAME, "sc-guPfGz")
                
                # Safety check for Day 1 trap
                if "Day 1" in day_label.text:
                    print(f"🛑 Refusing to click {day_label.text}. Account is on Day 6+ but site shows Guest view.")
                    return

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
