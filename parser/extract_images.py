"""
extract_images.py
각 문항의 이미지 영역(소스 자료 박스)을 PNG로 추출하여 저장.

원리:
  - PDF의 모든 내장 이미지를 좌표와 함께 추출
  - 각 이미지를 questions_77.json의 문항 번호와 매핑
    (이미지가 속한 페이지 x,y 위치 → 해당 문항 영역 판별)
  - data/images/77-{qno:02d}.png 로 저장
  - questions_77.json의 image_path 필드 업데이트
"""
import json
import fitz
from pathlib import Path

PDF_PATH    = Path(__file__).parent.parent / "pdfs" / "77회 한국사_문제지(심화).pdf"
JSON_PATH   = Path(__file__).parent.parent / "data" / "questions_77.json"
IMG_DIR     = Path(__file__).parent.parent / "data" / "images"
HEADER_Y    = 50.0
# COL_SPLIT: 실제 페이지 너비의 절반 (동적 계산)
# fitz로 열면 728.5pt → 중앙 ≈ 364pt
# 고정값 대신 main()에서 doc[0].rect.width / 2 로 설정
COL_SPLIT: float = 364.0  # 초기값 (main에서 덮어씀)


def get_question_bbox_map(questions: list[dict], doc: fitz.Document) -> dict:
    """
    각 문항 번호 → 해당 문항이 차지하는 (page_idx, y_top, y_bottom, col) 매핑.
    문항 번호 토큰의 좌표를 기준으로 문항 영역을 추정.
    """
    import re
    Q_PAT = re.compile(r"^(\d{1,2})\.$")

    # 문항 번호 토큰 수집
    q_positions = []
    for p_idx, page in enumerate(doc):
        for w in page.get_text("words"):
            x0, y0, _, _, text, *_ = w
            if y0 < HEADER_Y:
                continue
            m = Q_PAT.match(text.strip())
            if m:
                q_no = int(m.group(1))
                if 1 <= q_no <= 50:
                    col = 0 if x0 < COL_SPLIT else 1
                    q_positions.append({
                        "q_no": q_no, "page": p_idx,
                        "y": y0, "x": x0, "col": col
                    })

    # 중복 제거 (첫 등장)
    seen, clean = set(), []
    for qp in q_positions:
        if qp["q_no"] not in seen:
            seen.add(qp["q_no"]); clean.append(qp)
    clean.sort(key=lambda x: x["q_no"])

    # 각 문항의 y_bottom = 같은 컬럼 다음 문항의 y (또는 페이지 하단)
    bbox_map = {}
    for i, qp in enumerate(clean):
        # 다음 문항 찾기 (같은 페이지 같은 컬럼 우선)
        y_bottom = None
        for nxt in clean[i+1:]:
            if nxt["page"] == qp["page"] and nxt["col"] == qp["col"]:
                y_bottom = nxt["y"] - 2
                break
        if y_bottom is None:
            # 다음 페이지 첫 문항까지
            page_h = doc[qp["page"]].rect.height
            y_bottom = page_h - 20

        bbox_map[qp["q_no"]] = {
            "page": qp["page"],
            "y_top": qp["y"] - 4,
            "y_bottom": y_bottom,
            "col": qp["col"],
        }
    return bbox_map


def extract_question_image(page: fitz.Page, y_top: float, y_bottom: float,
                            col: int, scale: float = 2.0) -> fitz.Pixmap | None:
    """문항 영역을 PNG 픽스맵으로 반환."""
    page_w = page.rect.width
    if col == 0:
        x0, x1 = 0, COL_SPLIT
    else:
        x0, x1 = COL_SPLIT, page_w

    rect = fitz.Rect(x0, y_top, x1, y_bottom)
    mat  = fitz.Matrix(scale, scale)   # 2× 해상도
    clip = rect & page.rect             # 페이지 경계 내로 제한
    if clip.is_empty:
        return None
    return page.get_pixmap(matrix=mat, clip=clip)


def main():
    global COL_SPLIT

    IMG_DIR.mkdir(parents=True, exist_ok=True)

    with open(JSON_PATH, encoding="utf-8") as f:
        data = json.load(f)

    questions = data["questions"]
    doc = fitz.open(str(PDF_PATH))

    # 🔑 실제 페이지 너비 기준으로 COL_SPLIT 동적 계산
    page_w = doc[0].rect.width
    COL_SPLIT = page_w / 2
    print(f"📏 페이지 너비: {page_w:.1f}pt  →  COL_SPLIT: {COL_SPLIT:.1f}pt")

    print("📐 문항 위치 매핑 중...")
    bbox_map = get_question_bbox_map(questions, doc)
    print(f"   매핑 완료: {len(bbox_map)}문항\n")


    updated = 0
    for q in questions:
        q_no = q["question_no"]
        bx   = bbox_map.get(q_no)
        if not bx:
            print(f"  ⚠️  Q{q_no:02d}: 위치 정보 없음 — 건너뜀")
            continue

        page = doc[bx["page"]]
        pix  = extract_question_image(
            page, bx["y_top"], bx["y_bottom"], bx["col"]
        )
        if pix is None:
            print(f"  ⚠️  Q{q_no:02d}: 이미지 영역 비어있음")
            continue

        img_filename = f"77-{q_no:02d}.png"
        img_path     = IMG_DIR / img_filename
        pix.save(str(img_path))

        # JSON 업데이트
        q["image_path"] = f"images/{img_filename}"
        updated += 1
        print(f"  ✅ Q{q_no:02d}: {img_filename} ({pix.width}×{pix.height}px)")

    # JSON 저장
    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"\n💾 완료: {updated}/{len(questions)}문항 이미지 추출 → {IMG_DIR}")
    print(f"   questions_77.json 에 image_path 필드 추가됨")


if __name__ == "__main__":
    main()
