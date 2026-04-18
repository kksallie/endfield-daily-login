import os
import json
import time
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait # NEW
from selenium.webdriver.support import expected_conditions as EC # NEW

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

        # 5. Login Flow (Updated for new popup structure)
                try:
                    # Wait up to 10 seconds for the "Please log in first" text to appear
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.XPATH, "//div[contains(text(), 'Please log in first')]"))
                    )
                    print("Login required. Using credentials...")
            
                    email = os.getenv("SKPORT_EMAIL")
                    password = os.getenv("SKPORT_PASSWORD")
            
                    if email and password:
                        # Click the "Log In" button on the main page to trigger the modal
                        login_button_main = driver.find_element(By.XPATH, "//div[contains(text(), 'Please log in first')]/following-sibling::div//div[contains(text(), 'Log In')]")
                        driver.execute_script("arguments[0].click();", login_button_main)
                
                        # Wait for the modal input fields to become visible
                        email_input = WebDriverWait(driver, 10).until(
                            EC.visibility_of_element_located((By.CSS_SELECTOR, "input[type='text']"))
                        )
                        password_input = driver.find_element(By.CSS_SELECTOR, "input[type='password']")
                
                        email_input.send_keys(email)
                        password_input.send_keys(password)
                
                        # Click the submit button inside the modal
                        login_btn = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
                        driver.execute_script("arguments[0].click();", login_btn)
                
                        # Wait up to 15 seconds for the login prompt to disappear, confirming success
                        WebDriverWait(driver, 15).until(
                            EC.invisibility_of_element_located((By.XPATH, "//div[contains(text(), 'Please log in first')]"))
                        )
                        print("✅ Login successful!")
                    else:
                        print("❌ Missing credentials.")
                        return

                except Exception as e:
                    # If the wait times out, it means the text wasn't found, so we are likely already logged in via cookies.
                    print("Already signed in or login prompt not found. Proceeding...")

        # 7. Claim Logic
                print("Searching for reward...")
                try:
                    # The currently claimable reward always gets this unique animation container
                    claimable_reward = driver.find_element(By.ID, "lottie-container")
                    print("Found claimable day. Clicking...")
            
                    # Click the parent container of the animation to ensure the click registers
                    target = claimable_reward.find_element(By.XPATH, "..")
                    driver.execute_script("arguments[0].click();", target)
            
                    print("✅ Success!")
                    time.sleep(5) # Brief wait to let the claim register
            
                except Exception as e:
                    # If lottie-container isn't found, there is nothing to claim today
                    print("Already signed in or no rewards available today.")

            except Exception as e:
                print(f"Error during execution: {e}")
            finally:
                driver.quit()

if __name__ == "__main__":
    run_checkin()
