import requests
import os
import time
from datetime import datetime

# Configuration
IMMICH_BASE_URL = "http://ip_addr:port"
API_KEY = "API_key"
ALBUM_ID = "album_ID"
DOWNLOAD_DIR = "download_directory"

headers = {"x-api-key": API_KEY}

def safe_download_all_assets():
    print("🚀 Starting SAFE download from album")
    print("=" * 60)
    
    # Create timestamped download directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    download_path = f"{DOWNLOAD_DIR}_{timestamp}"
    os.makedirs(download_path, exist_ok=True)
    
    print(f"📁 Download directory: {download_path}")
    
    # Get album assets
    album_response = requests.get(f"{IMMICH_BASE_URL}/api/albums/{ALBUM_ID}", headers=headers)
    album_data = album_response.json()
    assets = album_data.get('assets', [])
    
    print(f"📊 Total assets to download: {len(assets):,}")
    print(f"⏰ Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 60)
    
    success_count = 0
    skip_count = 0
    error_count = 0
    start_time = time.time()
    
    # Download with progress
    for i, asset in enumerate(assets, 1):
        asset_id = asset['id']
        original_filename = asset['originalFileName']
        
        # Progress indicator
        if i % 100 == 0 or i <= 10:
            print(f"📦 Progress: {i:,}/{len(assets):,} ({i/len(assets)*100:.1f}%)")
        
        # Download the file
        download_url = f"{IMMICH_BASE_URL}/api/assets/{asset_id}/original"
        
        try:
            download_response = requests.get(download_url, headers=headers, timeout=30)
            
            if download_response.status_code == 200:
                file_path = os.path.join(download_path, original_filename)
                
                # Handle duplicates
                counter = 1
                base_name, ext = os.path.splitext(original_filename)
                while os.path.exists(file_path):
                    file_path = os.path.join(download_path, f"{base_name}_{counter:03d}{ext}")
                    counter += 1
                    if counter > 100:  # Safety limit
                        break
                
                # Save file
                with open(file_path, 'wb') as f:
                    f.write(download_response.content)
                
                success_count += 1
                
            else:
                print(f"❌ Failed: {original_filename} (HTTP {download_response.status_code})")
                error_count += 1
                
        except Exception as e:
            print(f"❌ Error: {original_filename} - {e}")
            error_count += 1
        
        # Small delay to be nice to the server
        time.sleep(0.1)
    
    # Calculate statistics
    total_time = time.time() - start_time
    print("-" * 60)
    print("🎉 DOWNLOAD COMPLETE!")
    print(f"✅ Successful: {success_count:,}")
    print(f"⚠️  Errors: {error_count:,}")
    print(f"⏱️  Total time: {total_time/60:.1f} minutes")
    print(f"📁 Files saved to: {download_path}")
    print(f"🕒 End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    confirmation = input("Type 'YES' to continue: ")
    
    if confirmation == 'YES':
        safe_download_all_assets()
    else:
        print("Download cancelled.")
