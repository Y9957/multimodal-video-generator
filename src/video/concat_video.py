"""
concat_video.py
- concat_videos_ffmpeg + node_concat
"""

import os
import subprocess
from typing import List
from ppt_parser import SlideData
from script_generator import State


# ------------------------------------------------------------
# concat_videos_ffmpeg
# ------------------------------------------------------------
def concat_videos_ffmpeg(video_paths: List[str], out_path: str, reencode: bool = False):
    """
    여러 mp4 파일을 하나로 합치는 유틸 함수.
    원본 코드와 동일하게, ffmpeg concat demuxer + list.txt 사용.
    """
    list_path = out_path + ".txt"
    with open(list_path, "w", encoding="utf-8") as f:
        for v in video_paths:
            f.write(f"file '{os.path.abspath(v)}'\n")

    if reencode:
        cmd = [
            "ffmpeg", "-y", "-safe", "0", "-f", "concat", "-i", list_path,
            "-vf", "format=yuv420p",
            "-c:v", "libx264", "-preset", "veryfast",
            "-c:a", "aac", "-b:a", "192k",
            out_path
        ]
    else:
        cmd = [
            "ffmpeg", "-y", "-safe", "0", "-f", "concat",
            "-i", list_path, "-c", "copy", out_path
        ]

    subprocess.check_call(cmd)


# ------------------------------------------------------------
# node_concat
# ------------------------------------------------------------
def node_concat(state: State) -> State:
    """
    슬라이드별 영상들을 하나로 병합하여 최종 영상을 생성.
    결과는 state["full_video_path"]에 저장.
    """
    videos = [s.video for s in state.get("slides", []) if s.video]
    if not videos:
        print("[WARNING] 병합할 영상이 없습니다.")
        return state

    # 최종 결과 파일 경로 지정
    output_final = os.path.join(state["media_dir"], "final_lecture.mp4")

    # concat 실행
    concat_videos_ffmpeg(videos, output_final, reencode=False)

    print(f"[INFO] 최종 영상 병합 완료 → {output_final}")

    return {
        **state,
        "slides": state["slides"],
        "full_video_path": output_final,
    }
