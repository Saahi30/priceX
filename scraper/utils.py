import requests
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

def get_session():
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
        "Accept": "application/json, text/html, application/xhtml+xml",
        "Accept-Language": "en-US,en;q=0.9"
    })
    return session

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((requests.RequestException, ValueError))
)
def fetch_url(url, session=None, timeout=30):
    sess = session or get_session()
    response = sess.get(url, timeout=timeout)
    response.raise_for_status()
    return response

def clean_value(v):
    if not isinstance(v, str):
        return v
    return v.replace("₹", "").replace(",", "").replace("%", "").strip()
