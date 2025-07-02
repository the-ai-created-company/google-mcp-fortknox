import urllib.request
import json

url = "https://storage.googleapis.com/discovery/v1/apis/storage/v1/rest"
print(f"Downloading storage discovery document from {url}...")

try:
    with urllib.request.urlopen(url) as response:
        data = response.read()
        with open("storage_discovery.json", "wb") as f:
            f.write(data)
    print(f"Successfully downloaded {len(data)} bytes")
except Exception as e:
    print(f"Error downloading: {e}")
