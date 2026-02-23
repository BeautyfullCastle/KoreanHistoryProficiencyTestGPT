"""
parse_exam.py  (v5 - fitz JSON 기반, 폰트 인코딩 우회)
핵심: pdfplumber의 일부 폰트 '?' 변환 문제를 fitz JSON으로 우회.
fitz는 page.get_text("json")으로 블록/라인/span 형태로 텍스트를 보여주며
한글 인코딩도 정상 처리됨.
"""
import re, json
import fitz
from pathlib import Path

PDF_PATH     = Path(__file__).parent.parent / "pdfs" / "77회 한국사_문제지(심화).pdf"
ANSWERS_PATH = Path(__file__).parent.parent / "data" / "answers_77.json"
OUT_PATH     = Path(__file__).parent.parent / "data" / "questions_77.json"

CHOICE_SYMS = {"①", "②", "③", "④", "⑤"}
SCORE_PAT   = re.compile(r'\[(\d)점\]')
HEADER_Y    = 50.0    # 페이지 최상단 여백만 제외 (타이틀 y≈14, 실제 문항은 y≥50)
COL_SPLIT   = 318.0


# ─── 좌표 기반 단어 추출 ────────────────────────────────────────────────────────
def extract_words_fitz(doc: fitz.Document):
    """fitz words 리스트 반환: (x0, y0, x1, y1, text, page_no)"""
    all_words = []
    for p_idx, page in enumerate(doc):
        for w in page.get_text("words"):
            # w = (x0, y0, x1, y1, "text", block_no, line_no, word_no)
            if w[1] < HEADER_Y:
                continue
            all_words.append((w[0], w[1], w[2], w[3], w[4], p_idx))
    return all_words


def sort_2col(words):
    """2컬럼 순서: (page, column, y_snap, x)"""
    def key(w):
        col = 0 if w[0] < COL_SPLIT else 1
        y_snap = round(w[1] / 6) * 6
        return (w[5], col, y_snap, w[0])
    return sorted(words, key=key)


# ─── 문항 경계 탐지 ─────────────────────────────────────────────────────────────
Q_NUM_EXACT = re.compile(r'^(\d{1,2})\.$')


def find_boundaries(words):
    """문항 번호 토큰 인덱스 반환: [(q_no, word_idx)]"""
    boundaries = []
    for i, w in enumerate(words):
        text = w[4].strip()
        m = Q_NUM_EXACT.match(text)
        if not m:
            continue
        q_no = int(m.group(1))
        if not (1 <= q_no <= 50):
            continue
        # 페이지 번호 오탐 제거: 다음 단어가 질문 키워드 포함하거나 x 좌표가 컬럼 선두여야 함
        # → 느슨하게: q_no 가 1~50 범위이면 일단 포함
        boundaries.append((q_no, i))

    # 중복 제거 (첫 등장만)
    seen, clean = set(), []
    for q_no, idx in boundaries:
        if q_no not in seen:
            seen.add(q_no)
            clean.append((q_no, idx))
    clean.sort(key=lambda x: x[0])
    return clean


# ─── 텍스트 재구성 ───────────────────────────────────────────────────────────────
def words_to_text(words) -> str:
    if not words:
        return ""
    lines, cur, prev_y, prev_page = [], [], words[0][1], words[0][5]
    for w in words:
        x, y, _, _, text, page = w[0], w[1], w[2], w[3], w[4], w[5]
        if page != prev_page or abs(y - prev_y) > 8:
            lines.append(" ".join(cur))
            cur = []
        cur.append(text)
        prev_y = y
        prev_page = page
    if cur:
        lines.append(" ".join(cur))
    return "\n".join(l for l in lines if l)


# ─── 문항 파싱 ────────────────────────────────────────────────────────────────────
def parse_block(q_no: int, block_words) -> dict:
    text = words_to_text(block_words)
    lines = [l.strip() for l in text.split("\n") if l.strip()]

    # 배점
    score = None
    for line in lines:
        sm = SCORE_PAT.search(line)
        if sm:
            score = int(sm.group(1))
            break

    # 선택지 시작 위치
    choice_idx = None
    for i, line in enumerate(lines):
        if any(line.startswith(s) for s in CHOICE_SYMS):
            choice_idx = i
            break

    pre   = lines[:choice_idx] if choice_idx is not None else lines
    post  = lines[choice_idx:] if choice_idx is not None else []

    # 선택지 파싱
    choices: dict[str, str] = {}
    cur_sym, cur_parts = None, []
    for line in post:
        sym = next((s for s in CHOICE_SYMS if line.startswith(s)), None)
        if sym:
            if cur_sym:
                choices[cur_sym] = " ".join(cur_parts).strip()
            cur_sym = sym
            cur_parts = [line[len(sym):].strip()]
        elif cur_sym:
            cur_parts.append(line)
    if cur_sym:
        choices[cur_sym] = " ".join(cur_parts).strip()

    # 질문 / 지문 분리
    question_text, source_parts = "", []
    for line in pre:
        cleaned = re.sub(r'^\d{1,2}\.\s*', '', line)
        cleaned = SCORE_PAT.sub("", cleaned).strip()
        if not cleaned or re.match(r'^\d+$', cleaned):
            continue
        if not question_text and ("것은" in cleaned or "?" in cleaned
                                  or "옳은" in cleaned or "적절한" in cleaned):
            question_text = cleaned
        else:
            source_parts.append(cleaned)

    source_material = " ".join(source_parts)
    has_image = len(source_material) < 40 or (choice_idx is not None and choice_idx < 3)

    return {
        "id":             f"77-{q_no:02d}",
        "exam_no":        77,
        "level":          "심화",
        "year":           2026,
        "question_no":    q_no,
        "score":          score,
        "question_text":  question_text,
        "source_material": source_material,
        "has_image":      has_image,
        "image_note":     "[역사 자료 이미지 포함]" if has_image else None,
        "choices":        choices,
        "correct_answer": None,
        "keywords":       [],
    }


def merge_answers(questions, path):
    if not path.exists():
        return questions
    with open(path, encoding="utf-8") as f:
        ans_map = {a["question_no"]: a for a in json.load(f)}
    for q in questions:
        a = ans_map.get(q["question_no"])
        if a:
            q["correct_answer"] = a["correct_answer"]
            if q["score"] is None:
                q["score"] = a["score"]
    return questions


def main():
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    print("📄 fitz 단어 추출 중...")
    doc = fitz.open(str(PDF_PATH))
    raw_words = extract_words_fitz(doc)
    print(f"   총 단어: {len(raw_words)}")

    words = sort_2col(raw_words)

    print("✂️  문항 경계 탐지 중...")
    boundaries = find_boundaries(words)
    found_nos = [b[0] for b in boundaries]
    missing   = [i for i in range(1, 51) if i not in found_nos]
    print(f"   감지: {len(boundaries)}개 → {found_nos}")
    if missing:
        print(f"   ⚠️ 미감지: {missing}")

    questions = []
    for i, (q_no, start) in enumerate(boundaries):
        end = boundaries[i + 1][1] if i + 1 < len(boundaries) else len(words)
        questions.append(parse_block(q_no, words[start:end]))

    print("🔗 정답 병합 중...")
    questions = merge_answers(questions, ANSWERS_PATH)

    c5  = sum(1 for q in questions if len(q["choices"]) == 5)
    img = sum(1 for q in questions if q["has_image"])
    print(f"\n📋 {len(questions)}문항 | 선택지5개: {c5} | 이미지표기: {img}\n")
    for q in questions:
        ic = "🖼️" if q["has_image"] else "  "
        print(f"  {ic} {q['question_no']:2d}번 ({q['score']}점)→{q['correct_answer']} "
              f"선:{len(q['choices'])} | {q['question_text'][:38]}")

    result = {
        "meta": {
            "exam_no": 77, "level": "심화", "year": 2026,
            "total_questions": len(questions),
            "source": "historyexam.go.kr",
        },
        "questions": questions,
    }
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"\n💾 저장: {OUT_PATH}")


if __name__ == "__main__":
    main()
