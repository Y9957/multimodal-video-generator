"""
script_generator.py
- node_generate_script_with_context 
- 슬라이드 요약(summary) + 검색 결과 + 사용자 프롬프트 기반으로
  '강의 스크립트(문장)'을 생성하는 단계
"""

import re
from typing import Dict, TypedDict, List
from dataclasses import dataclass

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from ppt_parser import SlideData


# ------------------------------------------------------------
# State 구조 
# ------------------------------------------------------------
class State(TypedDict, total=False):
    pptx_path: str
    prompt: Dict[str, str]          # tone, style 등
    work_dir: str
    media_dir: str
    slides: List[SlideData]         # 페이지별 SlideData
    full_script_path: str
    full_video_path: str


# ------------------------------------------------------------
# 모델명 
# ------------------------------------------------------------
LLM_MODEL = "gpt-4o-mini"


# ------------------------------------------------------------
# node_generate_script_with_context 
# ------------------------------------------------------------
def node_generate_script_with_context(state: dict) -> dict:
    """
    슬라이드 요약(summary), 표, 검색 결과, 이미지 등을 기반으로
    최종 '강의 스크립트'를 생성.
    
    문장 스타일: 사용자 tone/style 프롬프트 반영
    형식 규칙: 스크립트 톤, 강의 흐름 등 원본 규칙 동일
    """

    llm = ChatOpenAI(model=LLM_MODEL, temperature=0.5)

    # 사용자 프롬프트
    tone = state.get("prompt", {}).get("tone", "차분하고 명확한 강의 톤")
    style = state.get("prompt", {}).get("style", "학습자가 이해하기 쉽게 설명하는 스타일")
    long_script_rule = state.get("long_script_rule", "한 슬라이드당 4~8 문장으로 자세히 설명")

    for slide in state.get("slides", []):
        if not slide.summary:
            print(f"[SKIP] Page {slide.page}: summary 없음 → 스크립트 생성 건너뜀")
            continue

        # 기본 summary
        summary_text = slide.summary

        # 이미지 base64 
        def img_to_data_url(path: str):
            import base64
            try:
                with open(path, "rb") as f:
                    encoded = base64.b64encode(f.read()).decode("utf-8")
                return f"data:image/png;base64,{encoded}"
            except:
                return ""

        images_b64 = [img_to_data_url(img_path) for img_path in slide.images[:3]]

        # 검색 결과
        search_str = getattr(slide, "search_result", "")
        if not search_str:
            search_str = "(관련 추가 정보 없음)"

        # 표 정리
        table_str = ""
        if slide.tables:
            blocks = []
            for idx, tbl in enumerate(slide.tables):
                tbl_text = "\n".join([" | ".join(row) for row in tbl])
                blocks.append(f"[표 {idx+1}]\n{tbl_text}")
            table_str = "\n\n".join(blocks)

        # prompt 
        full_prompt_text = (
            f"너는 {tone}의 AI 강사야.\n"
            f"설명 스타일은 '{style}'이며, {long_script_rule} 규칙을 따라.\n\n"
            "- 학습자가 처음 듣는다고 가정하고 친절하지만 과장 없는 학습 설명 제공\n"
            "- 불릿 금지(문장 서술형)\n"
            "- 도입부 멘트(오늘은~, 이번 시간에는~) 금지\n"
            "- PPT에 없는 정보는 추가로 만들지 않되, 검색 정보가 관련 있을 경우만 반영\n\n"

            f"▶ 요약 내용:\n{summary_text}\n\n"
            f"▶ 외부 검색 정보:\n{search_str}\n\n"
            f"▶ 표 데이터:\n{table_str}\n\n"
            "위 내용을 바탕으로 강의자가 학습자에게 설명하듯 자연스러운 5~8문장 스크립트를 작성하라."
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
        script = response.content.strip()

        # 후처리: 강의체 금지 문구 제거
        script = re.sub(
            r"(오늘|이번|다음|이 시간|지금|배워보겠|살펴보겠)[^.!?]*[.!?]",
            "",
            script
        ).strip()

        slide.script = script
        print(f"[INFO] Page {slide.page} 스크립트 생성 완료 🎤")

    return state
