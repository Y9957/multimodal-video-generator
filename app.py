import gradio as gr
import io, sys, os, time, shutil
import threading, queue

# -------------------- 설정 프리셋 --------------------
VOICES = [
    "alloy","echo", "fable", "onyx", "nova", "shimmer", "coral", "verse", "ballad", "ash", "sage", "marin", "cedar"
]
TONES = [
    "친근하고 밝은 톤", "차분하고 전문적인 톤", "지적이고 명료한 강의 톤",
    "활발하고 에너지 넘치는 톤", "감정 표현 중심의 따뜻한 톤",
    "서정적이고 부드러운 톤", "무게감 있는 저음 톤", "정중하고 발표용 톤",
]
STYLES = [
    "예시와 핵심 요점 중심", "이론 중심으로 자세히 설명", "비유와 스토리텔링 중심",
    "질문-답변 형식으로 진행", "학생 참여형 설명",
]
PRESENTATION_RULES = [
    "각 슬라이드의 핵심 문장만 요약하여 대본 구성",
    "모든 슬라이드의 텍스트를 기반으로 세부 설명 추가",
    "텍스트 외 이미지나 그래프 내용도 언급하도록 구성",
    "짧고 간결한 발표용 대본 중심",
    "자연스러운 대화체로 재작성된 강의 대본",
]

# -------------------- 실시간 로그용 파이프라인 실행 --------------------
def run_pipeline_ui_stream(pptx_file, tone_dropdown, tone_custom, voice_dropdown, voice_custom,
                           style_dropdown, style_custom, pres_dropdown, pres_custom,
                           user_prompt_input):
    """
    Generator: yields (out_video_for_preview, out_video_file_for_download,
                        out_script_file_for_download, log_text)
    """
    log = ""

    # ---- 입력 처리 ----
    tone = tone_custom.strip() if tone_custom.strip() else tone_dropdown
    style = style_custom.strip() if style_custom.strip() else style_dropdown
    voice = voice_custom.strip() if voice_custom.strip() else voice_dropdown
    presentation_rule = pres_custom.strip() if pres_custom.strip() else pres_dropdown
    user_prompt = user_prompt_input.strip() if user_prompt_input and user_prompt_input.strip() else ""

    if pptx_file is None:
        log += "[ERROR] PPT 파일이 업로드되지 않았습니다.\n"
        yield None, None, None, log
        return

    # ---- 작업 디렉토리 및 파일 복사 ----
    work_dir = os.path.join("./webio", f"run-{int(time.time())}")
    os.makedirs(work_dir, exist_ok=True)
    pptx_path = os.path.join(work_dir, "input.pptx")
    src_path = getattr(pptx_file, "name", str(pptx_file))
    shutil.copy(src_path, pptx_path)

    log += f"[INFO] 작업 디렉토리 생성: {work_dir}\n"
    log += f"[INFO] 톤: {tone}\n"
    log += f"[INFO] 목소리: {voice}\n"
    log += f"[INFO] 스타일: {style}\n"
    log += f"[INFO] 대본 규칙: {presentation_rule}\n"
    log += f"[INFO] 유저 프롬프트: {user_prompt}\n"
    # 초기 상태(아직 파일 없음)
    yield None, None, None, log

    # ---- 상태(state) 초기화 ----
    MEDIA_DIR = os.path.join(work_dir, "media")
    os.makedirs(MEDIA_DIR, exist_ok=True)
    state = {
        "pptx_path": pptx_path,
        "work_dir": work_dir,
        "media_dir": MEDIA_DIR,
        "prompt": {
            "voice": voice or "alloy",
            "tone": tone,
            "style": style,
            "presentation_rule": presentation_rule,
            "user_prompt": user_prompt,
        },
    }

    # -------------------- stdout 캡처 및 스레드 실행 --------------------
    q = queue.Queue()
    orig_stdout, orig_stderr = sys.stdout, sys.stderr

    class QueueWriter:
        def write(self, s):
            # 일부 라이브러리는 빈 문자열/개행을 여러번 보낼 수 있으므로 그대로 enqueue
            if s is not None and s != "":
                q.put(str(s))
        def flush(self):
            pass

    exception_holder = {}

    def target_invoke():
        try:
            print("[INFO] app.invoke(state) 실행 중...")
            # 실제 파이프라인 호출: app.invoke는 전역에 정의되어 있어야 함
            final_state = app.invoke(state)
            exception_holder["result"] = final_state
            print("[INFO] app.invoke 실행 완료 ✅")
        except Exception as e:
            exception_holder["exc"] = e
            q.put(f"[EXC] {repr(e)}\n")
        finally:
            q.put(None)  # 종료 신호

    # redirect stdout/stderr to queue writer while thread runs
    sys.stdout = QueueWriter()
    sys.stderr = QueueWriter()
    t = threading.Thread(target=target_invoke, daemon=True)
    t.start()

    # 실시간 로그 읽기
    while True:
        try:
            item = q.get(timeout=0.2)
        except queue.Empty:
            # 주기적 갱신
            yield None, None, None, log
            continue

        if item is None:
            break

        log += str(item)
        yield None, None, None, log

    # 복원
    sys.stdout = orig_stdout
    sys.stderr = orig_stderr
    t.join(timeout=1.0)

    # 예외 확인
    if "exc" in exception_holder:
        exc = exception_holder["exc"]
        log += f"[ERROR] 실행 중 예외 발생: {exc}\n"
        yield None, None, None, log
        return

    final_state = exception_holder.get("result", {}) or {}
    video_path = final_state.get("full_video_path")
    script_path = final_state.get("full_script_path")

    if not video_path or not os.path.exists(video_path):
        log += "[WARNING] 영상 파일을 찾을 수 없습니다.\n"
        yield None, None, None, log
        return

    log += f"[INFO] 영상 생성 완료 → {video_path}\n"
    if script_path and os.path.exists(script_path):
        log += f"[INFO] 스크립트 생성 완료 → {script_path}\n"
    else:
        script_path = None
        log += "[WARNING] 스크립트 파일을 찾을 수 없습니다.\n"

    # 최종: out_video(미리보기), out_download(파일 경로), out_script_download(스크립트 파일 경로), log
    yield video_path, video_path, script_path, log

# -------------------- Gradio UI --------------------
with gr.Blocks(title="AI 강사 Agent", css="""
    #fixed-height-file {
        min-height: 180px !important;
        height: 180px !important;
        max-height: 180px !important;
        overflow: hidden !important;
    }

    #fixed-height-file > div {
        min-height: 180px !important;
        height: 180px !important;
        max-height: 180px !important;
    }

    .equal-height textarea {
        height: 546px !important;
    }


""") as demo:
    with gr.Row():
        with gr.Column(scale=1):
            inp_ppt = gr.File(
                label="PPTX 업로드",
                file_types=[".pptx"],
                height=150,
                elem_id="fixed-height-file"
            )

            logbox = gr.Textbox(
                label="실행 로그",
                lines=15,
                interactive=False,
                elem_classes=["equal-height"],
            )

        # 오른쪽: 옵션
        with gr.Column(scale=1):
            inp_tone_dropdown = gr.Dropdown(TONES, value=TONES[0], label="강의 톤 (프리셋)")
            inp_tone_custom   = gr.Textbox(value="", placeholder="직접 입력 가능", label="강의 톤 (커스텀)")
            inp_voice = gr.Dropdown(VOICES, value=VOICES[0], label="TTS Voice (프리셋)")
            inp_voice_custom = gr.Textbox(value="", label="TTS Voice (커스텀)")
            inp_style_dropdown = gr.Dropdown(STYLES, value=STYLES[0], label="설명 방식 (프리셋)")
            inp_style_custom   = gr.Textbox(value="", label="설명 방식 (커스텀)")
            inp_pres_dropdown = gr.Dropdown(PRESENTATION_RULES, value=PRESENTATION_RULES[0], label="대본 제작 방식 (프리셋)")
            inp_pres_custom   = gr.Textbox(value="", label="대본 제작 방식 (커스텀)")
            user_prompt_input = gr.Textbox(label="유저 프롬프트 입력", placeholder="예: 4~6문장으로 요약, 핵심 내용 중심")

    # 실행 버튼
    run_btn = gr.Button("실행", variant="primary")

    # 출력: 영상(한 줄), 그 아래에 다운로드 버튼들을 세로로 배치
    with gr.Column():
        out_video = gr.Video(label="최종 동영상 미리보기", interactive=False)
        # 다운로드 버튼들을 세로로 배치하려면 각 버튼을 Column에 넣음
        out_download = gr.DownloadButton(label="동영상 다운로드")
        out_script_download = gr.DownloadButton(label="스크립트 다운로드")

    # 클릭 연결: outputs = [out_video_preview, video_file_for_download, script_file_for_download, logbox]
    run_btn.click(
        fn=run_pipeline_ui_stream,
        inputs=[
            inp_ppt,
            inp_tone_dropdown,
            inp_tone_custom,
            inp_voice,
            inp_voice_custom,
            inp_style_dropdown,
            inp_style_custom,
            inp_pres_dropdown,
            inp_pres_custom,
            user_prompt_input,
        ],
        outputs=[out_video, out_download, out_script_download, logbox],
    )

demo.launch()
