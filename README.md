# Immich Album Downloader

A simple, robust Python script to download all original assets (photos and videos) from a specific [Immich](https://immich.app/) album.

## Why use this?

Immich is a self-hosted photo and video backup solution. While it has a great web interface and mobile app, sometimes you might want to:
- Create a local "cold storage" backup of a specific album.
- Share files offline.
- Migrate assets to another system.

This script automates the process of fetching every file in an album, handling duplicates, and organizing them into a timestamped folder.

## Features

- 🔒 **Safe**: Doesn't modify anything on your Immich server.
- 📂 **Organized**: Saves downloads in a new, timestamped directory each run.
- 🔄 **Smart**: Automatically handles duplicate filenames (e.g., `IMG_1234.jpg`, `IMG_1234_001.jpg`).
- 🚀 **Efficient**: Streams large files to keep memory usage low.

## Prerequisites

- Python 3.6+
- An Immich server instance.
- An API Key from your Immich server.

## Installation

1. Clone this repository or download the files.
2. Install the required dependencies:

   ```bash
   pip install -r requirements.txt
   ```

## Configuration

You can configure the script by editing `download.py` directly or by setting environment variables.

### Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `IMMICH_BASE_URL` | The URL of your Immich server (e.g., `http://192.168.1.100:2283`) | `http://ip_addr:port` |
| `IMMICH_API_KEY` | Your personal API Key | `API_key` |
| `IMMICH_ALBUM_ID` | The UUID of the album you want to download | `album_ID` |
| `IMMICH_DOWNLOAD_DIR` | Base directory for downloads | `immich_downloads` |

### Getting the Album ID

1. Open your Immich web interface.
2. Navigate to the Album you want to download.
3. Look at the URL in your browser address bar. It will look like this:
   `https://immich.yourdomain.com/albums/550e8400-e29b-41d4-a716-446655440000`
4. The last part (`550e8400...`) is your **Album ID**.

## Usage

Run the script:

```bash
python download.py
```

Follow the prompt to confirm the settings and start the download.

### Non-Interactive Mode

For automation (e.g., cron jobs), use the `--yes` flag to skip the confirmation prompt:

```bash
python download.py --yes
```

## Example with Environment Variables

```bash
export IMMICH_BASE_URL="http://192.168.1.50:2283"
export IMMICH_API_KEY="your_secret_key"
export IMMICH_ALBUM_ID="your_album_uuid"

python download.py --yes
```
