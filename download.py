import requests
import os
import time
import sys
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Tuple, Any

# Configuration
# You can set these via environment variables or modify them directly below.
IMMICH_BASE_URL = os.getenv("IMMICH_BASE_URL", "http://ip_addr:port")
API_KEY = os.getenv("IMMICH_API_KEY", "API_key")
ALBUM_ID = os.getenv("IMMICH_ALBUM_ID", "album_ID")
DOWNLOAD_DIR = os.getenv("IMMICH_DOWNLOAD_DIR", "immich_downloads")

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

def sanitize_filename(filename: str) -> str:
    """
    Sanitizes a filename by removing characters that are illegal on most file systems.

    Args:
        filename: The original filename.

    Returns:
        A sanitized filename string.
    """
    # Remove null bytes
    filename = filename.replace('\0', '')
    # Replace illegal characters with underscores
    filename = re.sub(r'[\\/*?:"<>|]', '_', filename)
    # Remove leading/trailing whitespace
    return filename.strip()

def get_unique_filepath(directory: Path, filename: str) -> Path:
    """
    Generates a unique file path by appending a counter if the file already exists.

    Args:
        directory: The target directory Path object.
        filename: The desired filename.

    Returns:
        A Path object guaranteed to not conflict with existing files.
    """
    sanitized_name = sanitize_filename(filename)
    file_path = directory / sanitized_name

    if not file_path.exists():
        return file_path

    stem = file_path.stem
    suffix = file_path.suffix
    counter = 1

    while True:
        new_filename = f"{stem}_{counter:03d}{suffix}"
        new_path = directory / new_filename
        if not new_path.exists():
            return new_path
        counter += 1

def fetch_album_data(base_url: str, album_id: str, headers: Dict[str, str]) -> Optional[Dict[str, Any]]:
    """
    Fetches album metadata and assets from the Immich API.

    Args:
        base_url: The base URL of the Immich instance.
        album_id: The UUID of the album.
        headers: Request headers (including API key).

    Returns:
        A dictionary containing album data or None if the request failed.
    """
    url = f"{base_url}/api/albums/{album_id}"
    logger.info(f"🔍 Fetching album info from: {url}")

    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Failed to fetch album: {e}")
        if hasattr(e, 'response') and e.response is not None:
             logger.error(f"   Server response: {e.response.text}")
        return None

def download_asset(
    base_url: str,
    asset: Dict[str, Any],
    download_dir: Path,
    headers: Dict[str, str]
) -> bool:
    """
    Downloads a single asset to the specified directory.

    Args:
        base_url: The base URL of the Immich instance.
        asset: The asset dictionary from the album data.
        download_dir: The local directory to save the file.
        headers: Request headers.

    Returns:
        True if successful, False otherwise.
    """
    asset_id = asset['id']
    original_filename = asset.get('originalFileName', f"asset_{asset_id}")

    download_url = f"{base_url}/api/assets/{asset_id}/original"

    try:
        # Stream the download to handle large files efficiently
        with requests.get(download_url, headers=headers, stream=True, timeout=60) as response:
            if response.status_code == 200:
                target_path = get_unique_filepath(download_dir, original_filename)

                with open(target_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                return True
            else:
                logger.error(f"❌ Failed: {original_filename} (HTTP {response.status_code})")
                return False

    except Exception as e:
        logger.error(f"❌ Error downloading {original_filename}: {e}")
        return False

def run_downloader() -> None:
    """
    Main function to orchestrate the album download process.
    """
    # Validation
    if IMMICH_BASE_URL == "http://ip_addr:port" or not IMMICH_BASE_URL.startswith("http"):
        logger.error("❌ Error: Please configure IMMICH_BASE_URL in the script or environment variables.")
        return
    if API_KEY == "API_key":
        logger.error("❌ Error: Please configure API_KEY in the script or environment variables.")
        return
    if ALBUM_ID == "album_ID":
        logger.error("❌ Error: Please configure ALBUM_ID in the script or environment variables.")
        return

    headers = {
        "x-api-key": API_KEY,
        "Accept": "application/json"
    }

    logger.info("🚀 Starting SAFE download from album")
    logger.info("=" * 60)
    
    # Create timestamped download directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    download_path = Path(DOWNLOAD_DIR) / f"backup_{timestamp}"

    try:
        download_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"📁 Download directory: {download_path.absolute()}")
    except OSError as e:
        logger.error(f"❌ Error creating directory: {e}")
        return

    # Get album assets
    album_data = fetch_album_data(IMMICH_BASE_URL, ALBUM_ID, headers)
    if not album_data:
        return

    assets = album_data.get('assets', [])
    album_name = album_data.get('albumName', 'Unknown Album')
    
    logger.info(f"📸 Album Name: {album_name}")
    logger.info(f"📊 Total assets to download: {len(assets):,}")
    logger.info(f"⏰ Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("-" * 60)
    
    success_count = 0
    error_count = 0
    start_time = time.time()
    
    # Download loop
    for i, asset in enumerate(assets, 1):
        # Progress indicator
        if i % 10 == 0 or i == 1 or i == len(assets):
             percentage = (i / len(assets)) * 100
             logger.info(f"📦 Progress: {i:,}/{len(assets):,} ({percentage:.1f}%)")
        
        success = download_asset(IMMICH_BASE_URL, asset, download_path, headers)
        
        if success:
            success_count += 1
        else:
            error_count += 1
        
        # Small delay to be nice to the server
        time.sleep(0.1)
    
    # Calculate statistics
    total_time = time.time() - start_time
    logger.info("-" * 60)
    logger.info("🎉 DOWNLOAD COMPLETE!")
    logger.info(f"✅ Successful: {success_count:,}")
    logger.info(f"⚠️  Errors: {error_count:,}")
    logger.info(f"⏱️  Total time: {total_time/60:.1f} minutes")
    logger.info(f"📁 Files saved to: {download_path.absolute()}")
    logger.info(f"🕒 End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    # Check for non-interactive flag
    is_non_interactive = len(sys.argv) > 1 and sys.argv[1] == "--yes"

    if is_non_interactive:
        run_downloader()
    else:
        logger.info("This script will download all assets from the configured Immich Album.")
        logger.info(f"Target URL: {IMMICH_BASE_URL}")
        logger.info(f"Album ID: {ALBUM_ID}")

        # Using input() directly as it's an interaction point, not loggable info
        try:
            confirmation = input("Type 'YES' to continue: ")
            if confirmation.strip() == 'YES':
                run_downloader()
            else:
                logger.info("Download cancelled.")
        except KeyboardInterrupt:
            logger.info("\nDownload cancelled.")
