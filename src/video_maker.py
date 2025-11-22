"""
video_maker.py
- node_make_video / render_mp4
- ffmpeg 기반 슬라이드별 영상 생성
- 모듈화
"""

import os
import subprocess
from typing import List, Dict, TypedDict
from dataclasses import dataclass

from ppt_parser import SlideData
from script_generator import State  # 동일한 State 구조 사용

# ------------------------------------------------------------
# ffprobe_duration (원본과 동일)
# ------------------------------------------------------------
def ffprobe_duration(path: str) -> float:
    cmd = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=nokey=1:noprint_wrappers=1",
        path
    ]
    try:
        out = subprocess.check_output(cmd, stderr=subprocess.STDOUT).decode().strip()
        return float(out)
    except:
        return 0.0


# ------------------------------------------------------------
# render_mp4
# ------------------------------------------------------------
def render_mp4(image_path: str, audio_path: str, output_path: str) -> str:
    """
    이미지 1장 + 음성 1개를 하나의 MP4 영상으로 변환
    원본 render_mp4 그대로 사용
    """

    audio_dur = ffprobe_duration(audio_path)
    if audio_dur <= 0:
        print(f"[WARNING] 음성 길이 측정 실패: {audio_path}")

    cmd = [
        "ffmpeg",
        "-y",
        "-loop", "1",
        "-i", image_path,
        "-i", audio_path,
        "-t", str(audio_dur),
        "-vf", "scale=1280:720",
        "-c:v", "libx264",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        output_path
    ]

    print(f"[INFO] ffmpeg 실행 → {output_path}")
    subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    return output_path


# ------------------------------------------------------------
# node_make_video
# ------------------------------------------------------------
def node_make_video(state: State) -> State:
    """
    각 슬라이드별 이미지 + 오디오 → MP4 생성
    slide.video 경로 저장
    """

    for slide in state.get("slides", []):
        if not slide.audio:
            print(f"[WARNING] Page {slide.page}: audio 없음 → 영상 생성 건너뜀")
            continue

        image_path = slide.slide_image
        audio_path = slide.audio
        video_path = os.path.join(
            state["media_dir"],
            f"{slide.page}_video.mp4"
        )

        render_mp4(image_path, audio_path, video_path)

        slide.video = video_path
        print(f"[INFO] Page {slide.page}: 영상 생성 완료 → {video_path}")

    return {
        **state,
        "slides": state["slides"]
    }
