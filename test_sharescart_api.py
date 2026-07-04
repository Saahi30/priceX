import requests

url = "https://www.sharescart.com/web-services/unlisted-stocks-intermediary.php"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Content-Type": "application/x-www-form-urlencoded",
    "Referer": "https://www.sharescart.com/unlisted-shares/unlisted-shares-quotes.php"
}
# Content-length was 91, this perfectly matches
data = "action=unlisted_shares_quotes_new&company_name=&mcap=all&price=all&industry=all&instaBuy=No"
try:
    response = requests.post(url, headers=headers, data=data)
    print("Status Code:", response.status_code)
    try:
        print(response.json())
    except:
        print(response.text[:1000])
except Exception as e:
    print("Error:", e)
