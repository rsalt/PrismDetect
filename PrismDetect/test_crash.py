import requests
import sys

url = 'http://localhost:8000/detect?min_confidence=0.4'

# Swiggy-Instamart.jpg was not downloaded. I will download it directly here.
img_url = "https://i0.wp.com/www.smartprix.com/bytes/wp-content/uploads/2022/07/Swiggy-Instamart.jpg"
img_data = requests.get(img_url).content

print(f"Downloaded image of size {len(img_data)} bytes")

files = {'file': ('test.jpg', img_data, 'image/jpeg')}

try:
    response = requests.post(url, files=files)
    print("Status Code:", response.status_code)
    print("Response:", response.text)
except requests.exceptions.ConnectionError as e:
    print("Connection closed unexpectedly! The backend crashed.")
    print(e)
