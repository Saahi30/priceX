from playwright.sync_api import sync_playwright

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # intercept and log POST requests to find the payload
        def log_request(route, request):
            if "unlisted-stocks-intermediary.php" in request.url:
                print(f"Request URL: {request.url}")
                print(f"Post Data: {request.post_data}")
            route.continue_()

        page.route("**/*", log_request)
        page.goto('https://www.sharescart.com/unlisted-shares/unlisted-shares-quotes.php', wait_until='networkidle')
        
        # wait a bit for any data to load
        page.wait_for_timeout(2000)
        
        browser.close()

if __name__ == '__main__':
    run()
