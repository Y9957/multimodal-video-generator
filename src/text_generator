"""
text_generator.py
- node_generate_text 함수를 그대로 모듈화
- 기능, 로직, 변수명, 조건문 
"""

import re
from typing import Dict, TypedDict, List
from dataclasses import dataclass

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

from ppt_parser import SlideData  # 동일한 SlideData 구조 사용
from tool_search import serpapi_search_by_title  # 혹시 사용될 수 있음


# ------------------------------------------------------------
# State 구조 
# ------------------------------------------------------------
class State(TypedDict, total=False):
    pptx_path: str
    prompt: Dict[str, str]
    work_dir: str
    media_dir: str
    slides: List[SlideData]
    full_script_path: str
    full_video_path: str


# ------------------------------------------------------------
# 이미지 → base64 변환 
# ------------------------------------------------------------
import base64

def img_to_data_url(path: str) -> str:
    """이미지를 base64 data URL 로 변환 (원본 코드 그대로)"""
    try:
        with open(path, "rb") as f:
            encoded = base64.b64encode(f.read()).decode("utf-8")
        return f"data:image/png;base64,{encoded}"
    except:
        return ""


# ------------------------------------------------------------
# LLM 모델 설정 
# ------------------------------------------------------------
LLM_MODEL = "gpt-4o-mini"
TTS_MODEL = "gpt-4o-mini-tts"


# ------------------------------------------------------------
# node_generate_text 
# ------------------------------------------------------------
def node_generate_text(state: dict) -> dict:
    """
    슬라이드의 텍스트, 표, 외부검색결과, 사용자 프롬프트를 종합하여
    객관적이고 서술형의 요약 설명문을 생성한다.
    (제목 슬라이드는 자동 건너뜀)
    """
    llm = ChatOpenAI(model=LLM_MODEL, temperature=0.5)

    # 사용자 프롬프트 불러오기
    user_prompt_template = state.get("user_prompt_template", "4~6문장으로 요약하고 과장 금지, 불릿 금지")
    presentation_rule = state.get("presentation_rule", "핵심 내용 중심으로 작성")
    tone = state.get("prompt", {}).get("tone", "명료하고 객관적인 설명 톤")
    style = state.get("prompt", {}).get("style", "보고서형 서술 스타일")

    for slide in state.get("slides", []):
        # 제목 페이지(또는 내용 없는 페이지)는 건너뜀
        all_text = " ".join(slide.texts).strip()
        title_text = " ".join(slide.titles) if hasattr(slide, "titles") else ""
        total_len = len(all_text.split())

        if total_len < 10 or (not slide.texts and title_text) and slide.page == 0:
            all_text = " ".join(slide.texts) if slide.texts else title_text
            print(f"[SKIP] Page {slide.page} 제목 슬라이드 감지 → 요약 건너뜀")
            slide.summary = all_text
            continue

        # 데이터 정리
        texts_str = " ".join(slide.texts)
        search_str = getattr(slide, "search_result", "")
        if not search_str:
            search_str = "(관련 있는 외부 검색 결과 없음)"

        # 표 데이터 정리
        table_str = ""
        if slide.tables:
            table_blocks = []
            for idx, tbl in enumerate(slide.tables):
                table_text = "\n".join([" | ".join(row) for row in tbl])
                table_blocks.append(f"[표 {idx+1}]\n{table_text}")
            table_str = "\n\n".join(table_blocks)

        # 이미지 인코딩 
        images_b64 = [img_to_data_url(img_path) for img_path in slide.images[:3]]

        # system prompt 
        full_prompt_text = (
            f"너는 {tone}의 AI 분석가야. "
            f"설명 스타일은 '{style}', 작성 규칙은 '{presentation_rule}'이야. "
            "슬라이드의 주요 텍스트, 표, 첨부된 이미지, 검색정보를 종합해 **객관적 요약 설명문**을 작성해줘.\n\n"
            f"요약 규칙: {user_prompt_template}\n"
            "- 불필요한 도입 문장(예: '오늘은', '이번 시간에는') 제거\n"
            "- 불릿 금지, 문단 서술형으로 작성\n"
            "- 검색 내용은 PPT 내용과 직접적으로 관련 있을 때만 반영\n"
            "- 과장, 감정 표현, 대화체 금지\n\n"
            f"▶ 슬라이드 텍스트:\n{texts_str}\n\n"
            f"▶ 표:\n{table_str}\n\n"
            f"▶ 외부 검색 정보:\n{search_str}\n\n"
            "위 내용을 바탕으로 객관적이고 논리적인 요약문 작성"
        )

        messages = [
            HumanMessage(content=[
                {"type": "text", "text": full_prompt_text},
                *[
                    {"type": "image_url", "image_url": {"url": img}}
                    for img in images_b64
                ]
            ])
        ]

        # LLM 호출
        response = llm.invoke(messages)
        summary = response.content.strip()

        # 후처리: 강의체 문장 제거
        summary = re.sub(r"(오늘|이번|다음|이 시간|지금|배워보겠|살펴보겠)[^.!?]*[.!?]", "", summary)
        summary = re.sub(r"\n{2,}", "\n", summary).strip()

        slide.summary = summary
        print(f"[INFO] Page {slide.page} 요약문 생성 완료 ✅")

    return {**state, "slides": state["slides"]}
