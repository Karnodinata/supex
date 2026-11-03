import re
import requests
import gdown

url = "https://drive.google.com/drive/folders/1jzLaqUAP0St3atEdsIRR4o8vu0lvLFy6"
print("Scanning for 'tes dulu'...")
files = gdown.download_folder(url, skip_download=True, quiet=False)

test_files = [f for f in files if "tes dulu" in getattr(f, "path", "").lower() or "tes" in getattr(f, "path", "").lower()]
print(f"Found {len(test_files)} files in test folder:")
for f in test_files:
    print(f"Path: {f.path} | ID: {f.id}")
X