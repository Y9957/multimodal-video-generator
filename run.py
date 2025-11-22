# run.py
import os
from src.graph.agent_graph import app

def main():
    print("=== 📘 Multimodal Lecture Video Generator ===")
    
    ppt_path = input("PPT 파일 경로를 입력하세요 (.pptx): ").strip()

    if not os.path.exists(ppt_path):
        print("❌ 파일 경로를 찾을 수 없습니다.")
        return

    # 사용자 톤/스타일 프롬프트 설정
    USER_PROMPT = {
        "voice": "alloy",
        "tone": "친절하고 명확한 강의톤",
        "style": "예시 중심 설명 스타일",
        "user_prompt": "4~6문장 요약",
        "presentation_rule": "불필요한 도입 금지, 핵심 중심",
    }

    WORK_DIR = "./output"
    MEDIA_DIR = "./output/media"

    os.makedirs(WORK_DIR, exist_ok=True)
    os.makedirs(MEDIA_DIR, exist_ok=True)

    # State 초기화
    state = {
        "pptx_path": ppt_path,
        "prompt": USER_PROMPT,
        "work_dir": WORK_DIR,
        "media_dir": MEDIA_DIR,
    }

    print("\n[INFO] 파이프라인 실행 중...")
    state = app.invoke(state, config={"recursion_limit": 150})
    print("[INFO] 실행 완료!\n")

    print("🎬 최종 강의 영상 경로:")
    print("➡", state.get("full_video_path", "경로 없음"))

    print("\n📝 전체 스크립트 경로:")
    print("➡", state.get("full_script_path", "경로 없음"))

    print("\n작업 완료 🎉")

if __name__ == "__main__":
    main()
