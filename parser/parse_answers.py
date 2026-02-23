"""
parse_answers.py
77회 한국사능력검정시험 심화 정답표 PDF → JSON 파싱
"""
import re
import json
import pdfplumber
from pathlib import Path

PDF_PATH  = Path(__file__).parent.parent / "pdfs" / "77회 한국사_답지(심화).pdf"
OUT_PATH  = Path(__file__).parent.parent / "data" / "answers_77.json"


def parse_answers(pdf_path: Path) -> list[dict]:
    """정답표에서 문항번호, 정답, 배점을 추출."""
    answers = []
    with pdfplumber.open(pdf_path) as pdf:
        text = pdf.pages[0].extract_text()

    # 패턴: "번호 정답기호 배점" (예: "1 ③ 1", "12 ① 3")
    pattern = re.compile(
        r'\b(\d{1,2})\s+([①②③④⑤])\s+(\d)\b'
    )
    for m in pattern.finditer(text):
        answers.append({
            "question_no": int(m.group(1)),
            "correct_answer": m.group(2),
            "score": int(m.group(3)),
        })

    # 중복 제거 후 번호 순 정렬
    seen = set()
    unique = []
    for a in answers:
        if a["question_no"] not in seen:
            seen.add(a["question_no"])
            unique.append(a)
    unique.sort(key=lambda x: x["question_no"])
    return unique


def main():
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    answers = parse_answers(PDF_PATH)

    print(f"✅ 파싱 완료: {len(answers)}문항")
    for a in answers:
        print(f"  {a['question_no']:2d}번 → {a['correct_answer']} ({a['score']}점)")

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(answers, f, ensure_ascii=False, indent=2)
    print(f"\n💾 저장: {OUT_PATH}")


if __name__ == "__main__":
    main()
