"""
concat_video.py
- node_concat
- ffmpeg concat demuxer 방식으로 슬라이드별 영상 병합
"""

import os
import subprocess
from typing import List, Dict, TypedDict

from ppt_parser import SlideData
from script_generator import State


# ------------------------------------------------------------
# node_concat
# ------------------------------------------------------------
def node_concat(state: State) -> State:
    """
    media_dir 내의 0_video.mp4, 1_video.mp4, ... 슬라이드 영상을
    순서대로 하나로 결합하여 full_video_path 에 저장.
    """

    media_dir = state["media_dir"]
    output_path = state.get("full_video_path", f"{media_dir}/final_lecture.mp4")

    # 슬라이드별 생성된 비디오들 가져오기
    video_files: List[str] = []
    for slide in state.get("slides", []):
        if slide.video and os.path.exists(slide.video):
            video_files.append(slide.video)

    if not video_files:
        print("[ERROR] 병합할 영상 파일이 없습니다.")
        return state

    # 정렬 (원본 = 슬라이드 순서 유지)
    video_files = sorted(video_files, key=lambda x: int(os.path.basename(x).split("_")[0]))

    # concat용 리스트 파일 생성
    list_path = os.path.join(media_dir, "video_list.txt")
    with open(list_path, "w") as f:
        for vf in video_files:
            f.write(f"file '{vf}'\n")

    print(f"[INFO] 병합 리스트 생성 완료 → {list_path}")

    # ffmpeg concat demuxer 방식 (원본 코드와 동일)
    cmd = [
        "ffmpeg",
        "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", list_path,
        "-c", "copy",
        output_path
    ]

    print(f"[INFO] 최종 영상 병합 시작 → {output_path}")
    subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # 저장 결과
    if os.path.exists(output_path):
        print(f"[INFO] 최종 영상 병합 완료 🎉 → {output_path}")
    else:
        print(f"[ERROR] 최종 영상 병합 실패")

    state["full_video_path"] = output_path
    return state
