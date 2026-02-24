"""
server.py — 한국사능력검정시험 ChatGPT Apps SDK MCP 서버
FastMCP (Python MCP SDK) 기반

Tools:
  - list_exams       : 사용 가능한 시험 회차 목록
  - get_question     : 특정 회차/문항 번호 조회
  - search_questions : 키워드로 문항 검색
  - grade_answer     : 사용자 답 채점
  - random_quiz      : 랜덤 문항 출제

배포: Cloudflare Workers (무료 10만 req/일)
로컬: python server.py → http://localhost:8787/mcp
"""
import json
import os
import random
import re
from pathlib import Path

from mcp.server.fastmcp import FastMCP

# ─── 데이터 로드 ──────────────────────────────────────────────────────────────
DATA_DIR = Path(__file__).parent.parent / "data"

# GitHub raw 이미지 베이스 URL (public repo)
GITHUB_RAW_BASE = (
    "https://raw.githubusercontent.com/"
    "BeautyfullCastle/KoreanHistoryProficiencyTestGPT/main"
)

def image_url(image_path: str | None) -> str | None:
    """image_path → 완전한 GitHub raw URL 변환. ChatGPT 채팅창에서 이미지 렌더링."""
    if not image_path:
        return None
    return f"{GITHUB_RAW_BASE}/data/{image_path}"

def load_exam(exam_no: int) -> dict | None:
    path = DATA_DIR / f"questions_{exam_no}.json"
    if not path.exists():
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)

# 서버 시작 시 사용 가능한 회차 캐시
AVAILABLE_EXAMS: dict[int, dict] = {}
for p in DATA_DIR.glob("questions_*.json"):
    no = int(re.search(r"questions_(\d+)\.json", p.name).group(1))
    AVAILABLE_EXAMS[no] = load_exam(no)

print(f"📚 로드된 시험 회차: {sorted(AVAILABLE_EXAMS.keys())}")

# ─── MCP 앱 ───────────────────────────────────────────────────────────────────
mcp = FastMCP("한국사능력검정시험")

# ─── Tool: list_exams ────────────────────────────────────────────────────────
@mcp.tool()
def list_exams() -> dict:
    """
    사용 가능한 한국사능력검정시험 심화 회차 목록을 반환합니다.
    각 회차의 번호, 연도, 문항 수, 총점을 포함합니다.
    """
    exams = []
    for no, data in sorted(AVAILABLE_EXAMS.items()):
        meta = data.get("meta", {})
        qs = data.get("questions", [])
        total_score = sum(q.get("score", 0) or 0 for q in qs)
        exams.append({
            "exam_no":        no,
            "year":           meta.get("year"),
            "level":          meta.get("level", "심화"),
            "total_questions": len(qs),
            "total_score":    total_score,
        })
    return {"exams": exams, "count": len(exams)}


# ─── Tool: get_question ──────────────────────────────────────────────────────
@mcp.tool()
def get_question(exam_no: int, question_no: int) -> dict:
    """
    특정 회차의 특정 문항을 반환합니다.
    정답은 사용자가 답을 제출한 후 grade_answer로 확인하세요.

    Args:
        exam_no: 시험 회차 번호 (예: 77)
        question_no: 문항 번호 (1~50)
    """
    data = AVAILABLE_EXAMS.get(exam_no)
    if not data:
        return {"error": f"{exam_no}회 데이터가 없습니다. list_exams로 가능한 회차를 확인하세요."}

    qs = data.get("questions", [])
    q = next((q for q in qs if q["question_no"] == question_no), None)
    if not q:
        return {"error": f"{exam_no}회 {question_no}번 문항을 찾을 수 없습니다."}

    # 정답 숨기고 반환
    img = image_url(q.get("image_path"))
    return {
        "id":              q["id"],
        "exam_no":         exam_no,
        "question_no":     question_no,
        "score":           q["score"],
        "question_text":   q["question_text"],
        "source_material": q["source_material"],
        "has_image":       q["has_image"],
        # 이미지가 있으면 마크다운 형식으로 포함 → ChatGPT 채팅창에서 직접 렌더링
        "image":           f"![{exam_no}회 {question_no}번]({img})" if img else None,
        "choices":         q["choices"],
        "hint":            "grade_answer 도구로 답을 제출하면 정오표를 확인할 수 있습니다.",
    }


# ─── Tool: search_questions ──────────────────────────────────────────────────
@mcp.tool()
def search_questions(keyword: str, exam_no: int = 0, limit: int = 5) -> dict:
    """
    키워드로 문항을 검색합니다. question_text와 source_material에서 검색합니다.

    Args:
        keyword: 검색어 (예: "고려", "조선 건국", "삼국통일")
        exam_no: 특정 회차로 한정 (0이면 전체 검색)
        limit:   최대 반환 개수 (기본 5)
    """
    kw = keyword.strip().lower()
    results = []

    exams_to_search = (
        {exam_no: AVAILABLE_EXAMS[exam_no]}
        if exam_no and exam_no in AVAILABLE_EXAMS
        else AVAILABLE_EXAMS
    )

    for eno, data in exams_to_search.items():
        for q in data.get("questions", []):
            text = (
                (q.get("question_text") or "") + " " +
                (q.get("source_material") or "") + " " +
                " ".join(q.get("choices", {}).values())
            ).lower()
            if kw in text:
                results.append({
                    "id":           q["id"],
                    "exam_no":      eno,
                    "question_no":  q["question_no"],
                    "score":        q["score"],
                    "question_text": q["question_text"],
                    "has_image":    q["has_image"],
                })
                if len(results) >= limit:
                    break
        if len(results) >= limit:
            break

    return {
        "keyword":     keyword,
        "count":       len(results),
        "results":     results[:limit],
        "tip":         "get_question으로 전체 선택지를 확인하세요.",
    }


# ─── Tool: grade_answer ──────────────────────────────────────────────────────
@mcp.tool()
def grade_answer(question_id: str, user_answer: str) -> dict:
    """
    사용자의 답을 채점합니다.

    Args:
        question_id: 문항 ID (예: "77-05")
        user_answer: 사용자가 선택한 답 (①②③④⑤ 중 하나)
    """
    # ID 파싱
    m = re.match(r"(\d+)-(\d+)", question_id)
    if not m:
        return {"error": "question_id 형식이 올바르지 않습니다. 예: '77-05'"}

    exam_no = int(m.group(1))
    q_no    = int(m.group(2))

    data = AVAILABLE_EXAMS.get(exam_no)
    if not data:
        return {"error": f"{exam_no}회 데이터가 없습니다."}

    qs = data.get("questions", [])
    q  = next((q for q in qs if q["question_no"] == q_no), None)
    if not q:
        return {"error": f"{exam_no}회 {q_no}번 문항을 찾을 수 없습니다."}

    correct = q.get("correct_answer", "")
    is_correct = user_answer.strip() == correct

    return {
        "question_id":    question_id,
        "user_answer":    user_answer,
        "correct_answer": correct,
        "is_correct":     is_correct,
        "score":          q.get("score", 0) if is_correct else 0,
        "max_score":      q.get("score", 0),
        "message": (
            f"✅ 정답입니다! ({correct}, {q.get('score')}점)" if is_correct
            else f"❌ 오답입니다. 정답은 {correct}입니다."
        ),
    }


# ─── Tool: random_quiz ───────────────────────────────────────────────────────
@mcp.tool()
def random_quiz(count: int = 5, exam_no: int = 0) -> dict:
    """
    랜덤으로 문항을 출제합니다. 미니 테스트용으로 사용하세요.

    Args:
        count:   출제할 문항 수 (기본 5, 최대 20)
        exam_no: 특정 회차로 한정 (0이면 전체)
    """
    count = min(count, 20)

    all_qs = []
    exams_pool = (
        {exam_no: AVAILABLE_EXAMS[exam_no]}
        if exam_no and exam_no in AVAILABLE_EXAMS
        else AVAILABLE_EXAMS
    )
    for eno, data in exams_pool.items():
        for q in data.get("questions", []):
            all_qs.append((eno, q))

    if not all_qs:
        return {"error": "문항 데이터가 없습니다."}

    sampled = random.sample(all_qs, min(count, len(all_qs)))
    questions = []
    for eno, q in sampled:
        img = image_url(q.get("image_path"))
        questions.append({
            "id":            q["id"],
            "exam_no":       eno,
            "question_no":   q["question_no"],
            "score":         q["score"],
            "question_text": q["question_text"],
            "source_material": q["source_material"],
            "has_image":     q["has_image"],
            "image":         f"![{eno}회 {q['question_no']}번]({img})" if img else None,
            "choices":       q["choices"],
        })

    total_score = sum(q["score"] or 0 for _, q in sampled)
    return {
        "count":       len(questions),
        "total_score": total_score,
        "questions":   questions,
        "tip":         "각 문항에 grade_answer로 답을 제출하면 점수가 집계됩니다.",
    }


# ─── 실행 (Vercel Serverless ASGI) ────────────────────────────────────────────────
# Vercel 환경에서는 파일 스크립트 실행(mcp.run) 대신
# FastAPI/Starlette ASGI 인스턴스인 `app` 변수를 찾습니다.
app = mcp.streamable_http_app()

if __name__ == "__main__":
    # 로컬 테스트용
    port = int(os.environ.get("PORT", 8787))
    host = os.environ.get("HOST", "0.0.0.0")
    print(f"🚀 MCP 로컬 서버 시작 → http://{host}:{port}/mcp")
    mcp.settings.host = host
    mcp.settings.port = port
    mcp.run(transport="streamable-http")

