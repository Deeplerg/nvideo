import logging
import math
import isodate
import yt_dlp
from googleapiclient import discovery

logger = logging.getLogger()

def format_ms_to_minutes_seconds(ms: int) -> str:
    """Milliseconds to MM:SS"""
    if ms < 0:
        ms = 0
    total_seconds = math.floor(ms / 1000)
    minutes = math.floor(total_seconds / 60)
    seconds = total_seconds % 60
    return f"{minutes:02d}:{seconds:02d}"

def format_ms_to_hours_minutes_seconds(ms: int) -> str:
    """Milliseconds to HH:MM:SS"""
    if ms < 0:
        ms = 0
    total_seconds = math.floor(ms / 1000)
    hours = math.floor(total_seconds / 60 / 60)
    minutes = math.floor((total_seconds / 60) % 60)
    seconds = total_seconds % 60
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

def format_ms_range(start_ms: int, end_ms: int) -> str:
    """(3:00) - (6:00)"""
    return f"{format_ms_to_minutes_seconds(start_ms)} - {format_ms_to_minutes_seconds(end_ms)}"

def generate_youtube_link(video_id: str, start_ms: int) -> str:
    start_seconds = math.floor(start_ms / 1000)
    return f"https://www.youtube.com/watch?v={video_id}&t={start_seconds}s"

def get_video_duration_google(video_id: str, youtube_api_key: str) -> int | None:
    youtube = discovery.build(
        'youtube', 'v3',
        developerKey=youtube_api_key,
        cache_discovery=True)

    request = youtube.videos().list(
        part="contentDetails",
        id=video_id
    )
    response = request.execute()

    if not response or not response.get("items"):
        logger.warning(f"No items returned for video id {video_id}")
        return None

    item = response["items"][0]
    duration_iso = item.get("contentDetails", {}).get("duration")

    if not duration_iso:
        logger.warning(f"Duration not found for video id {video_id}")
        return None

    duration_seconds = isodate.parse_duration(duration_iso).total_seconds()
    return duration_seconds

def get_video_duration_yt_dlp(video_id: str) -> int | None:
    url = f"https://www.youtube.com/watch?v={video_id}"
    ydl_opts = {
        'quiet': True,
        'no_warnings': False,
        'skip_download': True,
        'forcejson': True,
        'extract_flat': True, # no playlist entries
        'simulate': True # no format processing, just info
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(url, download=False)

        duration = None
        if info_dict:
            if 'duration' in info_dict:
                duration = info_dict.get('duration')
            elif 'entries' in info_dict and 'duration' in info_dict['entries'][0]:
                duration = info_dict['entries'][0].get('duration')

        if duration is not None:
            try:
                return int(float(duration))
            except (ValueError, TypeError):
                logger.error(f"Could not convert duration '{duration}' to int for video {video_id}")
                return None
        else:
            logger.warning(
                f"Duration not found in metadata for video {video_id}. info_dict keys: {info_dict.keys() if info_dict else 'None'}")
            return None
