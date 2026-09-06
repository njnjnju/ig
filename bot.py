import time
import random
import secrets
import string
import csv
import re
import pyotp
import requests
import os
from playwright.sync_api import sync_playwright

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# =====================================================================
# ⚙️ USER CONFIGURATION BLOCK
# =====================================================================
# PROXY CONFIGURATION (Format: username:password@host:port)
PROXY_STRING = "8008:MidzRjvmA592@p105.squidproxies.com:9140"

ADSPOWER_API = "http://127.0.0.1:50325/api/v1/browser/start"

# Asset pool folders inside the script directory
AVATAR_FOLDER = os.path.join(BASE_DIR, "avatar_pool")
POST_FOLDER = os.path.join(BASE_DIR, "post_pool")

# =====================================================================
# 📋 NAME & QUOTE DICTIONARIES FOR RANDOMIZATION
# =====================================================================
FIRST_NAMES = [
    "rahul", "ramesh", "harshit", "vivek", "rehan", "ankit", "naman", "sushant", "payal", "rakhi", 
    "deep", "deepak", "deepali", "rohan", "devansh", "devanshu", "shiva", "shiv", "shivani", "amit",
    "raman", "naaz", "naazo", "akshat", "ashtham", "yash", "kirti", "bhavesh", "sia", "arjun"
]
LAST_NAMES = [
    "agarwal", "gupta", "khan", "singh", "gupta", "Patel", "Sharma", "Reddy", "Nair", "Sophia", 
    "devi", "kumar", "kaur", "shukla", "Shah", "Kulkarni", "dubey", "reddy", "devi", "kaur",
    "kumar", "Joshi", "Tendulkar ", "Gavaskar", "sophia", "Yadav", "Tiwari ", "tripathi", "Chauhan", "Dwivedi "
]

INSTAGRAM_QUOTES = [
    "Chasing dreams and catching flights. ✈️🌟",
    "Creating the life I love, one day at a time.",
    "Simplicity is the ultimate sophistication. ✨",
    "Focus on the step in front of you, not the whole staircase. 🏔️",
    "Escape the ordinary, embrace the journey. 🚀",
    "Do what makes your soul shine. ☀️💖",
    "Collect moments, not things. 📸🍃",
    "Keep moving forward. Great things take time. ⏳",
    "Consistency is the secret code to success.🔑",
    "Radiate positive vibes only. 🌈✌️",
    "Living life on my own terms. 💫",
    "Every day is a fresh start to write a new story. 📖"
]

def parse_proxy(proxy_str):
    """Parses 'user:pass@host:port' string into Playwright proxy dictionary format."""
    if not proxy_str:
        return None
    try:
        user_pass, host_port = proxy_str.split("@")
        username, password = user_pass.split(":")
        return {
            "server": f"http://{host_port}",
            "username": username,
            "password": password
        }
    except Exception as e:
        print(f"⚠️ Failed to parse PROXY_STRING '{proxy_str}': {e}")
        return None

def get_random_image(folder_path):
    """Picks a random image file from the specified folder to ensure unique uploads."""
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
        raise Exception(f"❌ Folder '{folder_path}' was missing. Created it. Please add images inside it!")
    
    files = [f for f in os.listdir(folder_path) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    if not files:
        raise Exception(f"❌ No .jpg or .png images found in '{folder_path}'. Please add some items.")
    
    selected_file = random.choice(files)
    return os.path.abspath(os.path.join(folder_path, selected_file))

def generate_profile_data():
    """Prompts for email manually and generates unique identity, username, and password."""
    print("\n--------------------------------------------------")
    email_address = input("📧 Enter email address for registration: ").strip()
    
    fn = random.choice(FIRST_NAMES)
    ln = random.choice(LAST_NAMES)
    full_name = f"{fn} {ln}"
    
    rand_suffix = secrets.randbelow(89999) + 10000
    username = f"{fn.lower()}_{ln.lower()}_{rand_suffix}"
    
    allowed_chars = string.ascii_letters + string.digits + "!@#$%*"
    password = "".join(secrets.choice(allowed_chars) for _ in range(14))
    
    return full_name, username, password, email_address

def create_browser_profile():
    """Calls AdsPower API to initialize an isolated environment context."""
    print("🌐 Generating an isolated browser profile container...")
    try:
        response = requests.get(ADSPOWER_API, timeout=10).json()
        return response['data']['ws']['puppeteer']
    except Exception as e:
        raise Exception(f"Failed to fetch execution context from AdsPower API: {e}")

def register_account():
    full_name, username, password, email_address = generate_profile_data()
    avatar_path = get_random_image(AVATAR_FOLDER)
    post_path = get_random_image(POST_FOLDER)
    proxy_config = parse_proxy(PROXY_STRING)
    
    print(f"🚀 Attempting Account Creation: {username} ({email_address})")
    if proxy_config:
        print(f"📡 Using Proxy: {proxy_config['server']}")

    ws_url = create_browser_profile()
    
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(ws_url)
        
        if proxy_config:
            context = browser.new_context(
                proxy=proxy_config,
                viewport={"width": 1280, "height": 720}
            )
        else:
            context = browser.contexts[0]
            
        page = context.new_page()
        page.set_viewport_size({"width": 1280, "height": 720})
        
        # --- SUBMISSION STEP ---
        page.goto("https://www.instagram.com/accounts/emailsignup/", wait_until="networkidle")
        time.sleep(2)
        
        page.type("input[name='emailOrPhone']", email_address, delay=random.randint(70, 110))
        page.type("input[name='fullName']", full_name, delay=random.randint(60, 100))
        page.type("input[name='username']", username, delay=random.randint(80, 120))
        page.type("input[name='password']", password, delay=random.randint(90, 130))
        
        submit_btn = page.locator("button[type='submit']")
        submit_btn.click()
        time.sleep(4)
        
        # --- BIRTHDATE SELECTOR STEP ---
        if page.locator("select[title='Month:']").is_visible():
            page.select_option("select[title='Month:']", index=random.randint(1, 12))
            page.select_option("select[title='Day:']", index=random.randint(1, 28))
            page.select_option("select[title='Year:']", value=str(random.randint(1992, 2004)))
            page.locator("button:has-text('Next')").click()
            time.sleep(5)
            
        # --- MANUAL EMAIL VERIFICATION STEP ---
        verification_code = input(f"👉 Enter the 6-digit code sent to {email_address}: ").strip()
        
        page.type("input[name='email_confirmation_code']", verification_code, delay=120)
        page.locator("button:has-text('Next')").click()
        time.sleep(8)
        
        # --- AUTOMATED 2FA ACTIVATION PHASE ---
        print("🔐 Configuring structural App-Based Two-Factor Authentication...")
        page.goto("https://accountscenter.instagram.com/password_and_security", wait_until="networkidle")
        time.sleep(4)
        
        page.locator("text=Two-factor authentication").click()
        time.sleep(2)
        
        page.locator(f"text={username}").click()
        time.sleep(3)
        
        page.locator("text=Authentication app").click()
        page.locator("button:has-text('Next')").click()
        time.sleep(3)
        
        secret_element = page.locator("div[role='dialog'] text=/^[A-Z0-9]{32}$/") 
        if not secret_element.is_visible():
            secret_element = page.locator("span:has-text('Copy Key')").locator("xpath=../preceding-sibling::div")
            
        two_fa_seed = secret_element.inner_text().replace(" ", "")
        print(f"🔑 Found 2FA Seed: {two_fa_seed}")
        
        totp = pyotp.TOTP(two_fa_seed)
        live_token = totp.now()
        
        page.locator("button:has-text('Next')").click()
        time.sleep(2)
        page.type("input[type='text']", live_token, delay=100)
        page.locator("button:has-text('Next')").click()
        time.sleep(4)
        page.locator("button:has-text('Done')").click()
        time.sleep(2)

        # --- PROFILE PHOTO UPLOAD PHASE ---
        print("📸 Navigating to profile dashboard to upload avatar picture...")
        page.goto(f"https://www.instagram.com/{username}/", wait_until="networkidle")
        time.sleep(5)

        file_input_avatar = page.locator("input[type='file']").first
        print(f"🖼️ Uploading avatar: {avatar_path}")
        file_input_avatar.set_input_files(avatar_path)
        time.sleep(6)

        # --- FIRST POST CREATION PHASE ---
        print("➕ Initiating new post creation...")
        create_btn = page.locator("span:has-text('Create')")
        if not create_btn.is_visible():
            create_btn = page.locator("svg[aria-label='New post']").locator("xpath=../..")
            
        create_btn.click()
        time.sleep(3)

        file_input_post = page.locator("input[type='file']").first
        print(f"📤 Uploading post content: {post_path}")
        file_input_post.set_input_files(post_path)
        time.sleep(3)

        page.locator("button:has-text('Next')").click()
        time.sleep(2)
        page.locator("button:has-text('Next')").click()
        time.sleep(2)

        selected_quote = random.choice(INSTAGRAM_QUOTES)
        caption_text = f"{selected_quote} #{username}"
        
        print(f"📝 Writing caption: '{caption_text}'")
        page.locator("div[aria-label='Write a caption...']").type(caption_text, delay=80)
        time.sleep(2)

        print("🚀 Publishing post...")
        page.locator("button:has-text('Share')").click()
        time.sleep(12)

        # --- PROFESSIONAL BUSINESS ACCOUNT CONVERSION PHASE ---
        print("💼 Converting to Professional Business Profile...")
        page.goto("https://www.instagram.com/accounts/edit/", wait_until="networkidle")
        time.sleep(4)
        
        try:
            page.locator("span:has-text('Switch to professional account')").click()
        except:
            page.locator("text=Switch to Professional Account").click()
        time.sleep(3)
        
        page.locator("input[value='business']").click()
        page.locator("button:has-text('Next')").click()
        time.sleep(2)
        page.locator("button:has-text('Next')").click()
        time.sleep(2)
        
        page.locator("select").select_option(label="Entrepreneur")
        page.locator("button:has-text('Save')").click()
        time.sleep(4)
        
        skip_fb_btn = page.locator("button:has-text('Don't Connect to Facebook')")
        if not skip_fb_btn.is_visible():
            skip_fb_btn = page.locator("span:has-text('Skip')")
            
        skip_fb_btn.click()
        time.sleep(5)
        print("✅ Account conversion complete!")

        # --- SAVE DATABASE RECORDS ---
        csv_path = os.path.join(BASE_DIR, "instagram_accounts.csv")
        file_exists = os.path.exists(csv_path)
        with open(csv_path, mode="a", newline="", encoding="utf-8") as csv_file:
            writer = csv.writer(csv_file)
            if not file_exists:
                writer.writerow(["Email", "Username", "Password", "2FA Seed", "Created At"])
            writer.writerow([email_address, username, password, two_fa_seed, time.strftime("%Y-%m-%d %H:%M:%S")])
            
        print(f"✨ Account {username} ({email_address}) successfully created and saved to {csv_path}!")
        browser.close()

if __name__ == "__main__":
    for i in range(5):
        try:
            register_account()
        except Exception as global_err:
            print(f"❌ Automation error: {global_err}")
            time.sleep(10)
