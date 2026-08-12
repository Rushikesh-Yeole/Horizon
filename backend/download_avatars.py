import os
import urllib.request

def download_avatars():
    output_dir = "static/avatars"
    os.makedirs(output_dir, exist_ok=True)

    base_url = "https://api.dicebear.com/7.x/bottts/svg?seed="
    for i in range(1, 31):
        url = f"{base_url}{i}"
        filename = f"{i}.svg"
        filepath = os.path.join(output_dir, filename)
        
        try:
            urllib.request.urlretrieve(url, filepath)
            print(f"Downloaded {filename}")
        except Exception as e:
            print(f"Failed to download {filename}: {e}")

if __name__ == "__main__":
    download_avatars()
