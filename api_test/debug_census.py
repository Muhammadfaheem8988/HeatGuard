import requests

url = "https://api.census.gov/data/2022/acs/acs5?get=NAME,B01001_001E,B01001_020E&for=tract:*&in=state:04%20county:013"
r = requests.get(url, timeout=60)
print("Status:", r.status_code)
print("Content-Type:", r.headers.get("Content-Type"))
print("Encoding:", r.encoding)
print("First 500 bytes raw:", r.content[:500])
print("Text first 500:", r.text[:500])