import math

def format_ms_to_time(ms: int) -> str:
    """Milliseconds to MM:SS"""
    if ms < 0:
        ms = 0
    total_seconds = math.floor(ms / 1000)
    minutes = math.floor(total_seconds / 60)
    seconds = total_seconds % 60
    return f"{minutes:02d}:{seconds:02d}"

def format_ms_range(start_ms: int, end_ms: int) -> str:
    """(3:00) - (6:00)"""
    return f"{format_ms_to_time(start_ms)} - {format_ms_to_time(end_ms)}"

def generate_youtube_link(video_id: str, start_ms: int) -> str:
    start_seconds = math.floor(start_ms / 1000)
    return f"https://www.youtube.com/watch?v={video_id}&t={start_seconds}s"