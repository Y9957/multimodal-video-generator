"""
tts_engine.py
- node_tts / select_voice_by_tone / ffprobe_duration
- 모듈화
"""

import os
import subprocess
from typing import List, Dict, TypedDict
from dataclasses import dataclass

from openai import OpenAI

from ppt_parser import SlideData     # 동일한 구조 사용
from script_generator import State    # 동일한 State 구조 사용


# ------------------------------------------------------------
# ffprobe_duration
# ------------------------------------------------------------
def ffprobe_duration(path: str) -> float:
    """
    ffprobe로 음성 길이 추출 (초 단위)
    """
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
# select_voice_by_tone
# ------------------------------------------------------------
def select_voice_by_tone(tone: str) -> str:
    """
    tone(톤)의 의미에 따라 TTS voice 자동 선택
    (원본 로직 그대로 복사)
    """
    tone = tone.lower()

    # 밝고 친근한 인상
    if any(kw in tone for kw in ["밝", "친근", "명랑", "부드", "상냥", "따뜻", "편안"]):
        voice = "shimmer"

    # 차분하고 안정적인 / 전문적인
    elif any(kw in tone for kw in ["차분", "진지", "전문", "고급", "안정", "느긋"]):
        voice = "coral"

    # 지적하고 명료한 / 분석적
    elif any(kw in tone for kw in ["지적", "명료", "논리", "분석", "설명", "강의"]):
        voice = "sage"

    # 활발하고 에너지 넘치는
    elif any(kw in tone for kw in ["활발", "빠르", "에너지", "생동", "열정", "리듬", "역동"]):
        voice = "nova"

    # 감성적 / 서정적 / 잔잔한
    elif any(kw in tone for kw in ["서정", "감성", "잔잔", "감미", "감정", "따뜻한", "포근"]):
        voice = "fable"

    # 남성적 / 낮고 묵직한
    elif any(kw in tone for kw in ["무게감", "남성", "낮은", "중후", "묵직", "깊은"]):
        voice = "onyx"

    # 정중하고 발표용 / 공식적
    elif any(kw in tone for kw in ["정중", "격식", "공식", "프레젠테이션", "발표", "포멀"]):
        voice = "verse"

    # 따뜻하고 서사적인 이야기체
    elif any(kw in tone for kw in ["이야기", "내레이션", "스토리텔링", "표현", "감정적"]):
        voice = "ballad"

    # 세련되고 중립적인 / 도시적인
    elif any(kw in tone for kw in ["세련", "도시", "냉정", "중립", "차가운"]):
        voice = "ash"

    # 맑고 명쾌한 / 청명한
    elif any(kw in tone for kw in ["맑", "깨끗", "명쾌", "선명", "투명"]):
        voice = "echo"

    # 기본/표준
    elif any(kw in tone for kw in ["기본", "표준", "무난"]):
        voice = "alloy"

    # 자연스러운 / 여유있는 / 차분한
    elif any(kw in tone for kw in ["서사", "자연", "여유", "차분한", "잔잔한"]):
        voice = "marin"

    # 나무결처럼 따뜻한
    elif any(kw in tone for kw in ["나무", "편안함", "자연스러움", "온화"]):
        voice = "cedar"

    else:
        print(f"[WARNING] tone '{tone}' 매칭 실패 → 기본값 alloy")
        voice = "alloy"

    print(f"[INFO] 선택된 톤: '{tone}' → 선택된 목소리: '{voice}'")
    return voice


# ------------------------------------------------------------
# node_tts 
# ------------------------------------------------------------
TTS_MODEL = "gpt-4o-mini-tts"

def node_tts(state: State) -> State:
    """
    슬라이드별 스크립트를 TTS로 변환하여 mp3 생성
    원본 node_tts 그대로 모듈화
    """
    client = OpenAI()

    prompt = state.get("prompt", {})
    tone = prompt.get("tone", "")
    user_voice = prompt.get("voice", None)

    # 사용자가 직접 voice 선택했으면 우선 적용
    if user_voice and user_voice.strip():
        voice = user_voice
        print(f"[INFO]🎙️ 사용자 지정 목소리 사용: {voice}")
    else:
        voice = select_voice_by_tone(tone)
        print(f"[INFO]🎙️ tone '{tone}' → 자동 선택된 목소리: {voice}")

    # 유효한 voice 목록
    valid_voices = {
        "alloy","echo","fable","onyx","nova","shimmer",
        "coral","verse","ballad","ash","sage","marin","cedar"
    }
    if voice not in valid_voices:
        print(f"[WARN] '{voice}'는 지원되지 않아 기본값 alloy 사용")
        voice = "alloy"

    # state에 실제 voice 반영
    state.setdefault("prompt", {})["voice"] = voice

    # 슬라이드별 TTS 생성
    for slide in state.get("slides", []):
        script_text = slide.script
        if not script_text:
            print(f"[WARNING] Page {slide.page}: 스크립트 없음, 건너뜀")
            continue

        audio_path = f"{state['media_dir']}/{slide.page}_tts.mp3"

        # TTS 생성 (원본 그대로)
        with client.audio.speech.with_streaming_response.create(
            model=TTS_MODEL,
            voice=voice,
            input=script_text
        ) as response:
            audio_bytes = response.read()

        # 저장
        with open(audio_path, "wb") as f:
            f.write(audio_bytes)

        duration = ffprobe_duration(audio_path)
        print(f"[INFO] Page {slide.page} 음성 생성 완료: {audio_path} ({duration:.2f} sec)")

        slide.audio = audio_path

    return {
        **state,
        "slides": state["slides"]
    }
