import requests

url = "https://www.sharescart.com/web-services/unlisted-stocks-intermediary.php"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Accept": "application/json, text/plain, */*",
    "Content-Type": "application/x-www-form-urlencoded",
    "Referer": "https://www.sharescart.com/unlisted-shares/unlisted-shares-quotes.php"
}
data = "action=unlisted_shares_quotes_new&company_name=&mcap=all&price=all&industry=all&instaBuy=No"

response = requests.post(url, headers=headers, data=data, timeout=30)
try:
    json_data = response.json()
    if "data" in json_data:
        print("data type:", type(json_data["data"]))
        if isinstance(json_data["data"], dict):
            print("data keys:", json_data["data"].keys())
        elif isinstance(json_data["data"], list):
            print("data length:", len(json_data["data"]))
            if len(json_data["data"]) > 0:
                print("First item keys:", json_data["data"][0].keys())
except Exception as e:
    print("Error:", e)
