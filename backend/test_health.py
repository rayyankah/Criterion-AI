import urllib.request
import urllib.error

try:
    print("Sending request to health endpoint...")
    response = urllib.request.urlopen("https://criterion-ai-backend.onrender.com/health", timeout=15)
    print("Status code:", response.getcode())
    print("Body:", response.read().decode())
except urllib.error.HTTPError as e:
    print("HTTPError:", e.code, e.reason)
except urllib.error.URLError as e:
    print("URLError:", e.reason)
except Exception as e:
    print("Exception:", e)
