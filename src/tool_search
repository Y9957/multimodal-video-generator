"""
tool_search.py
- serpapi 검색 기능
- 검색 결과를 LLM 노드에서 활용하기 위한 node_tool_search 구현
"""

import os
from typing import Dict, List, TypedDict, Optional
import requests


# ------------------------------------------------------------
# State 
# ------------------------------------------------------------

class State(TypedDict, total=False):
    pptx_path: str
    prompt: Dict[str, str]
    work_dir: str
    media_dir: str
    slides: list
    full_script_path: str
    full_video_path: str


# ------------------------------------------------------------
# serpapi 검색 함수 
# ------------------------------------------------------------

def serpapi_search_by_title(title: str, api_key: Optional[str] = None) -> List[Dict]:
    """
    제목 기반 검색 기능.
    원본 코드의 serpapi 관련 로직을 그대로 유지해 모듈화함.
    """
    if api_key is None:
        api_key = os.getenv("SERPAPI_API_KEY", "")

    if not api_key:
        print("[WARN] SERPAPI_API_KEY 환경변수 없음 → 빈 검색 결과 반환")
        return []

    url = "https://serpapi.com/search"
    params = {
        "engine": "google",
        "q": title,
        "api_key": api_key,
        "num": 3
    }

    try:
        response = requests.get(url, params=params)
        data = response.json()

        results = []

        # organic_results 존재 시
        if "organic_results" in data:
            for item in data["organic_results"]:
                entry = {
                    "title": item.get("title", ""),
                    "snippet": item.get("snippet", ""),
                    "link": item.get("link", "")
                }
                results.append(entry)

        return results

    except Exception as e:
        print(f"[ERROR] 검색 실패: {e}")
        return []


# ------------------------------------------------------------
# node_tool_search — LLM의 AssistantContext에 들어갈 external info 생성
# ------------------------------------------------------------

def node_tool_search(state: State) -> State:
    """
    프롬프트 안의 'title'을 기반으로 serpapi 검색.
    검색 결과를 state["search_results"]에 저장.

    원본 node_tool_search 기능을 그대로 수행.
    """

    # prompt 내부에 title이 있어야 한다
    if "prompt" not in state or "title" not in state["prompt"]:
        print("[WARN] prompt.title 없음 → 검색 건너뜀")
        state["search_results"] = []
        return state

    title = state["prompt"]["title"]

    print(f"[INFO] 검색 실행: \"{title}\"")
    results = serpapi_search_by_title(title)
    print(f"[INFO] 검색 결과 {len(results)}개 수집됨")

    state["search_results"] = results
    return state
