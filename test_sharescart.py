from playwright.sync_api import sync_playwright

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto('https://www.sharescart.com/unlisted-shares/unlisted-shares-quotes.php', wait_until='networkidle')
        
        # wait a second
        page.wait_for_timeout(2000)
        
        # let's try to find rows
        rows = page.locator("tr").count()
        print(f"Found {rows} table rows")
        
        if rows > 0:
            for i in range(min(5, rows)):
                print(page.locator("tr").nth(i).inner_text())
                
        with open("sharescart_test.html", "w", encoding="utf-8") as f:
            f.write(page.content())
            
        browser.close()

if __name__ == '__main__':
    run()
