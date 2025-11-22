"""
agent_graph.py
- AI 강사 Agent v2.0 전체 파이프라인 그래프 정의
- StateGraph 구성
"""

from langgraph.graph import StateGraph, START, END

from ppt_parser import State, node_parse_ppt
from tool_search import node_tool_search
from text_generator import node_generate_text
from script_generator import node_generate_script_with_context
from tts_engine import node_tts
from video_maker import node_make_video
from concat_video import node_concat


# ------------------------------------------------------------
# 그래프 정의
# ------------------------------------------------------------

builder = StateGraph(State)

# 노드 등록
builder.add_node("parse_ppt", node_parse_ppt)
builder.add_node("tool_search", node_tool_search)
builder.add_node("generate_page", node_generate_text)
builder.add_node("generate_script", node_generate_script_with_context)
builder.add_node("tts_mp3", node_tts)
builder.add_node("make_video", node_make_video)
builder.add_node("concat", node_concat)

# 연결
builder.add_edge(START, "parse_ppt")
builder.add_edge("parse_ppt", "tool_search")
builder.add_edge("tool_search", "generate_page")
builder.add_edge("generate_page", "generate_script")
builder.add_edge("generate_script", "tts_mp3")
builder.add_edge("tts_mp3", "make_video")
builder.add_edge("make_video", "concat")
builder.add_edge("concat", END)

# 최종 앱
app = builder.compile()
