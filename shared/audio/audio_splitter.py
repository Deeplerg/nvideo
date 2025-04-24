import asyncio
import json
import logging
import os
import subprocess
import tempfile
from dataclasses import dataclass
import math
from logging import Logger

from typing import AsyncGenerator


@dataclass
class AudioChunk:
    start_time_ms: int
    end_time_ms: int
    chunk_path: str

@dataclass
class AudioInfo:
    duration_ms: float
    codec_name: str

@dataclass
class ExtensionInfo:
    extension: str
    is_fallback: bool

async def get_audio_info(
        file_path: str,
        logger: Logger = logging.getLogger()) -> AudioInfo:
    command = [
        'ffprobe',
        '-v', 'quiet',
        '-print_format', 'json',
        '-show_format',
        '-show_streams',
        file_path
    ]
    try:
        result = await asyncio.to_thread(subprocess.run,command, capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError as e:
        error_message = ("Error running ffmpeg.\n"
                         f"Return code: {e.returncode}\n"
                         f"Stderr: {e.stderr}\n"
                         f"Stdout: {e.stdout}")
        logger.error(error_message)
        raise
    data = json.loads(result.stdout)

    duration_s = None
    codec_name = None
    if 'format' in data and 'duration' in data['format']:
        duration_s = float(data['format']['duration'])
    if 'streams' in data:
        for stream in data['streams']:
            if stream['codec_type'] == 'audio':
                if 'codec_name' in stream:
                    codec_name = stream['codec_name']
                    break

    if duration_s is None:
         raise ValueError(f"Could not determine duration for {file_path}")
    if codec_name is None:
         raise ValueError(f"Could not determine codec name for {file_path}")

    return AudioInfo(
        duration_ms=duration_s * 1000,
        codec_name=codec_name
    )


def get_compatible_extension(
        codec_name: str,
        logger: Logger = logging.getLogger()) -> ExtensionInfo:
    codec_map = {
        'opus': 'opus',
        'aac': 'm4a',
        'mp3': 'mp3',
        'vorbis': 'ogg',
        'pcm_s16le': 'wav'
    }
    ext = codec_map.get(codec_name.lower())
    fallback = False
    if ext is None:
        ext = "wav"
        logger.warning(f"Unsupported codec '{codec_name}'. Falling back to '{ext}'.")
        fallback = True
    return ExtensionInfo(
        extension=ext,
        is_fallback=fallback
    )


async def split_audio(
        file_path,
        segment_length_ms=3 * 60 * 1000,
        use_temp_dir=True,
        logger: Logger = logging.getLogger()
) -> AsyncGenerator[AudioChunk, None]:
    if not os.path.exists(file_path):
         raise FileNotFoundError(f"Input file not found: {file_path}")

    filename_without_extension = os.path.splitext(os.path.basename(file_path))[0]
    segment_time_seconds = segment_length_ms / 1000.0

    out_dir = tempfile.gettempdir() if use_temp_dir else os.path.dirname(file_path)
    os.makedirs(out_dir, exist_ok=True)

    audio_info = await get_audio_info(file_path, logger)
    total_duration_ms = int(audio_info.duration_ms)
    codec_name = audio_info.codec_name

    extension = get_compatible_extension(codec_name)
    out_format = extension.extension

    output_pattern = os.path.join(out_dir, f"{filename_without_extension}_part%03d.{out_format}")

    command = [
        'ffmpeg',
        '-i', file_path,
        '-f', 'segment',
        '-segment_time', str(segment_time_seconds),
        *([
            '-segment_format', codec_name,
            '-c:a', 'copy',
          ] if not extension.is_fallback else []),
        '-vn',
        '-reset_timestamps', '1',
        '-map', '0:a:0',
        output_pattern
    ]

    try:
        await asyncio.to_thread(subprocess.run, command, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        error_message = ("Error running ffmpeg.\n"
                         f"Return code: {e.returncode}\n"
                         f"Stderr: {e.stderr}\n"
                         f"Stdout: {e.stdout}")
        logger.error(error_message)
        raise

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
