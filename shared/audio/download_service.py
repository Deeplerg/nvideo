import yt_dlp
import os
from tempfile import gettempdir

class DownloadService:
    def download_video_by_id(self, video_id, output_dir=gettempdir()):
        url = f"https://www.youtube.com/watch?v={video_id}"
        output_path = os.path.join(output_dir, "%(title)s.%(ext)s")

        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": output_path,
            "noprogress": True,
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }
            ],
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            downloaded_file_path = ydl.prepare_filename(info).replace(".webm", ".mp3").replace(".m4a", ".mp3").replace(".mp4", ".mp3")

        return downloaded_file_path