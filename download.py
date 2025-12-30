import requests
import os
import time
import sys
from datetime import datetime

# Configuration
# You can set these via environment variables or modify them directly below.
IMMICH_BASE_URL = os.getenv("IMMICH_BASE_URL", "http://ip_addr:port")
API_KEY = os.getenv("IMMICH_API_KEY", "API_key")
ALBUM_ID = os.getenv("IMMICH_ALBUM_ID", "album_ID")
DOWNLOAD_DIR = os.getenv("IMMICH_DOWNLOAD_DIR", "immich_downloads")

def safe_download_all_assets():
    """
    Downloads all assets from the specified Immich album to a local directory.
    Creates a new directory with a timestamp for each run.
    """

    # Validation
    if IMMICH_BASE_URL == "http://ip_addr:port" or not IMMICH_BASE_URL.startswith("http"):
        print("❌ Error: Please configure IMMICH_BASE_URL in the script or environment variables.")
        return
    if API_KEY == "API_key":
        print("❌ Error: Please configure API_KEY in the script or environment variables.")
        return
    if ALBUM_ID == "album_ID":
        print("❌ Error: Please configure ALBUM_ID in the script or environment variables.")
        return

    headers = {
        "x-api-key": API_KEY,
        "Accept": "application/json"
    }

    print("🚀 Starting SAFE download from album")
    print("=" * 60)
    
    # Create timestamped download directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    download_path = os.path.join(DOWNLOAD_DIR, f"backup_{timestamp}")

    try:
        os.makedirs(download_path, exist_ok=True)
    except OSError as e:
        print(f"❌ Error creating directory: {e}")
        return
    
    print(f"📁 Download directory: {os.path.abspath(download_path)}")
    
    # Get album assets
    album_url = f"{IMMICH_BASE_URL}/api/albums/{ALBUM_ID}"
    print(f"🔍 Fetching album info from: {album_url}")

    try:
        album_response = requests.get(album_url, headers=headers, timeout=10)
        album_response.raise_for_status()
        album_data = album_response.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to fetch album: {e}")
        if hasattr(e, 'response') and e.response is not None:
             print(f"   Server response: {e.response.text}")
        return

    assets = album_data.get('assets', [])
    album_name = album_data.get('albumName', 'Unknown Album')
    
    print(f"📸 Album Name: {album_name}")
    print(f"📊 Total assets to download: {len(assets):,}")
    print(f"⏰ Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 60)
    
    success_count = 0
    error_count = 0
    start_time = time.time()
    
    # Download with progress
    for i, asset in enumerate(assets, 1):
        asset_id = asset['id']
        original_filename = asset.get('originalFileName', f"asset_{asset_id}")
        
        # Progress indicator
        if i % 10 == 0 or i == 1 or i == len(assets):
             print(f"📦 Progress: {i:,}/{len(assets):,} ({i/len(assets)*100:.1f}%)")
        
        # Download the file
        download_url = f"{IMMICH_BASE_URL}/api/assets/{asset_id}/original"
        
        try:
            # Stream the download to handle large files
            with requests.get(download_url, headers=headers, stream=True, timeout=60) as download_response:
                
                if download_response.status_code == 200:
                    file_path = os.path.join(download_path, original_filename)

                    # Handle duplicates
                    counter = 1
                    base_name, ext = os.path.splitext(original_filename)
                    while os.path.exists(file_path):
                        file_path = os.path.join(download_path, f"{base_name}_{counter:03d}{ext}")
                        counter += 1
                        # Removed arbitrary limit, but safe to assume we won't have infinite duplicates

                    # Save file with streaming
                    with open(file_path, 'wb') as f:
                        for chunk in download_response.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)

                    success_count += 1

                else:
                    print(f"❌ Failed: {original_filename} (HTTP {download_response.status_code})")
                    error_count += 1
                
        except Exception as e:
            print(f"❌ Error downloading {original_filename}: {e}")
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
    print(f"📁 Files saved to: {os.path.abspath(download_path)}")
    print(f"🕒 End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    # Optional: Skip confirmation if running in a CI/automated environment or if forced
    if len(sys.argv) > 1 and sys.argv[1] == "--yes":
        safe_download_all_assets()
    else:
        print("This script will download all assets from the configured Immich Album.")
        print(f"Target URL: {IMMICH_BASE_URL}")
        print(f"Album ID: {ALBUM_ID}")
        confirmation = input("Type 'YES' to continue: ")

        if confirmation.strip() == 'YES':
            safe_download_all_assets()
        else:
            print("Download cancelled.")
