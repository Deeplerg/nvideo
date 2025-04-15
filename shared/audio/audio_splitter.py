import os
import tempfile
from collections.abc import Generator
from dataclasses import dataclass
from pydub import AudioSegment
import math

@dataclass
class AudioChunk:
    start_time_ms: int
    end_time_ms: int
    chunk_path: str

def split_audio(file_path, segment_length_ms=3 * 60 * 1000, use_temp_dir=True) -> Generator[AudioChunk]:
    filename_without_extension = os.path.splitext(file_path)[0]
    out_format="mp3"

    out_dir=tempfile.gettempdir() if use_temp_dir else os.path.dirname(file_path)

    audio = AudioSegment.from_file(file_path)
    total_length = len(audio)
    num_segments = math.ceil(total_length / segment_length_ms)

    for i in range(num_segments):
        start_time = i * segment_length_ms
        end_time = min((i + 1) * segment_length_ms, total_length)
        segment = audio[start_time:end_time]

        output_file = os.path.join(out_dir, f"{filename_without_extension}_part{i + 1}.{out_format}")

        segment.export(output_file, format=out_format)


        yield AudioChunk(
            start_time_ms=start_time,
            end_time_ms=end_time,
            chunk_path=output_file
        )