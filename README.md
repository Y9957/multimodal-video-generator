# 📘 multimodal-video-generator

이 프로젝트는 OpenAI 기반 멀티모달 에이전트 파이프라인을 구성하여 PPT만 업로드하면 강의 영상을 자동으로 생성하는 시스템 입니다.

🚀 주요 기능

✔ 1. PPT 분석 (Parsing)

텍스트 / 이미지 / 표 추출

슬라이드 스냅샷 PNG 생성

Python-pptx + LibreOffice + pdftoppm 기반

✔ 2. 검색 기반 보조 정보 생성

SERPAPI로 제목 기반 관련 정보 검색

LLM이 요약/스크립트 생성 시 참고

✔ 3. LLM 기반 내용 생성

슬라이드 내용 요약 (node_generate_text)

요약 + 검색 + 이미지 기반 장문 스크립트 생성 (node_generate_script_with_context)

사용자 톤/스타일 반영

✔ 4. 음성 생성 (TTS)

OpenAI gpt-4o-mini-tts 사용

자동 톤 분석 → voice 자동 선택

슬라이드별 mp3 파일 생성

✔ 5. 영상 생성

이미지 + 음성을 ffmpeg로 합성 (slide 단위 mp4)

720p 기본 출력

✔ 6. 최종 영상 병합

모든 슬라이드 영상을 순서대로 결합해

최종 강의 영상 MP4 생성

🧩 프로젝트 구조

src/
 ├── parsing/
 │     └── ppt_parser.py
 │
 ├── searching/
 │     └── tool_search.py
 │
 ├── generation/
 │     ├── text_generator.py
 │     ├── script_generator.py
 │     └── tts_engine.py
 │
 ├── video/
 │     ├── video_maker.py
 │     └── concat_video.py
 │
 └── graph/
       └── agent_graph.py

🔗 전체 파이프라인 흐름

PPT 입력
   ↓
parse_ppt
   ↓
tool_search
   ↓
generate_text
   ↓
generate_script_with_context
   ↓
tts_mp3
   ↓
make_video
   ↓
concat
   ↓
최종 강의 영상 완성 🎥

🛠 기술 스택

Python 3.10+

LangChain / LangGraph

OpenAI GPT-4o-mini / GPT-4o-mini-tts

python-pptx

LibreOffice (PPT → PDF/PNG 변환)

ffmpeg (영상 합성)

SERPAPI (검색)

이미지 처리: base64 인코딩

⚙️ 실행 방법

이 프로젝트는 하나의 PPT 파일을 입력해
강의 영상 자동 생성 파이프라인을 실행하는 방식입니다.

## 1) 환경 변수 설정

OpenAI API Key와 SERPAPI Key를 환경 변수로 등록해야 합니다 .

(Google Colab)
import os
os.environ["OPENAI_API_KEY"] = "api_key"
os.environ["SERPAPI_API_KEY"] = "serpapi_key"

(Windows PowerShell / 로컬)
setx OPENAI_API_KEY "api_key"
setx SERPAPI_API_KEY "serpapi_key"

## 2) 필수 Python 패키지 설치

pip install -r requirements.txt

## 3) 시스템 프로그램 설치 (ffmpeg, libreoffice, poppler)

(PPT 이미지 변환 및 영상 생성에 필요)

Ubuntu
sudo apt install ffmpeg libreoffice poppler-utils

macOS
brew install ffmpeg libreoffice poppler

Windows
ffmpeg: https://ffmpeg.org/download.html

LibreOffice: https://www.libreoffice.org/download

poppler: https://blog.alivate.com.au/poppler-windows/

## 4) 실행 스크립트 (run.py)

from src.graph.agent_graph import app
import os

# =======================================
# 1) PPT 파일 경로 지정
# =======================================
pptx_path = "sample.pptx"  # 분석할 ppt 경로 입력

# =======================================
# 2) 사용자 프롬프트 설정
# =======================================
USER_PROMPT = {
    "voice": "alloy",
    "tone": "친절하고 명료한 강의 톤",
    "style": "예시 중심 설명 스타일",
    "user_prompt": "4~6문장 요약",
    "presentation_rule": "불필요한 도입 금지, 핵심 중심",
}

# =======================================
# 3) 출력 폴더 생성
# =======================================

WORK_DIR = "./output"
MEDIA_DIR = "./output/media"
os.makedirs(WORK_DIR, exist_ok=True)
os.makedirs(MEDIA_DIR, exist_ok=True)

# =======================================
# 4) 초기 state 생성
# =======================================

state = {
    "pptx_path": pptx_path,
    "prompt": USER_PROMPT,
    "work_dir": WORK_DIR,
    "media_dir": MEDIA_DIR,
}

# =======================================
# 5) Agent 그래프 실행
# =======================================

print("[INFO] 파이프라인 실행 중...")
state = app.invoke(state, config={"recursion_limit": 100})
print("[INFO] 실행 완료!")

# =======================================
# 6) 생성 결과 출력
# =======================================

print("\n🎬 최종 강의 영상 경로:")
print(state.get("full_video_path"))

print("\n📝 생성된 전체 스크립트 경로:")
print(state.get("full_script_path"))


## 5) 실행

```bash
python run.py
```

## 6) 결과물

| 항목              | 경로                                   |
|-------------------|-----------------------------------------|
| 슬라이드별 음성(mp3) | output/media/{page}_tts.mp3             |
| 슬라이드별 영상(mp4) | output/media/{page}_video.mp4           |
| **최종 강의 영상**   | **output/media/final_lecture.mp4**      |
| 전체 스크립트       | output/full_script.txt                  |
