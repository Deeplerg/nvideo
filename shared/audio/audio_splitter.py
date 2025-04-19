import asyncio
import json
import os
import subprocess
import tempfile
from collections.abc import Generator
from dataclasses import dataclass
import math

from typing import AsyncGenerator


@dataclass
class AudioChunk:
    start_time_ms: int
    end_time_ms: int
    chunk_path: str

def get_audio_duration_ms(file_path: str) -> float:
    command = [
        'ffprobe',
        '-v', 'quiet',
        '-print_format', 'json',
        '-show_format',
        '-show_streams',
        file_path
    ]
    result = subprocess.run(command, capture_output=True, text=True, check=True)
    data = json.loads(result.stdout)

    duration_s = None
    if 'streams' in data:
        for stream in data['streams']:
            if stream.get('codec_type') == 'audio':
                if 'duration' in stream:
                    duration_s = float(stream['duration'])
                    break
    if duration_s is None and 'format' in data and 'duration' in data['format']:
        duration_s = float(data['format']['duration'])

    if duration_s is None:
         raise ValueError(f"Could not determine duration for {file_path}")

    return duration_s * 1000


async def split_audio(file_path, segment_length_ms=3 * 60 * 1000, use_temp_dir=True) -> AsyncGenerator[AudioChunk, None]:
    if not os.path.exists(file_path):
         raise FileNotFoundError(f"Input file not found: {file_path}")

    filename_without_extension = os.path.splitext(os.path.basename(file_path))[0]
    out_format = "wav"
    segment_time_seconds = segment_length_ms / 1000.0

    out_dir = tempfile.gettempdir() if use_temp_dir else os.path.dirname(file_path)
    output_pattern = os.path.join(out_dir, f"{filename_without_extension}_part%03d.{out_format}")

    os.makedirs(out_dir, exist_ok=True)

    total_duration_ms = int(get_audio_duration_ms(file_path))

    command = [
        'ffmpeg',
        '-i', file_path,
        '-f', 'segment',
        '-segment_time', str(segment_time_seconds),
        '-c:a', 'pcm_s16le',
        '-vn',
        '-reset_timestamps', '1',
        '-map', '0:a:0',
        output_pattern
    ]

    await asyncio.to_thread(subprocess.run, command, check=True, capture_output=True, text=True)

    num_segments = math.ceil(total_duration_ms / segment_length_ms)
    for i in range(num_segments):
         expected_chunk_path = os.path.join(out_dir, f"{filename_without_extension}_part{i:03d}.{out_format}")

         start_time = i * segment_length_ms
         end_time = min((i + 1) * segment_length_ms, total_duration_ms)

         yield AudioChunk(
             start_time_ms=int(start_time),
             end_time_ms=int(round(end_time)),
             chunk_path=expected_chunk_path
         )