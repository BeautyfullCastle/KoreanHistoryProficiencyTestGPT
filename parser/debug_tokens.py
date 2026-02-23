import pdfplumber

COL_SPLIT = 318.0
HEADER_Y = 100.0

with pdfplumber.open("pdfs/77회 한국사_문제지(심화).pdf") as pdf:
    for p_idx, page in enumerate(pdf.pages[:3]):
        words = page.extract_words() or []
        right_col = [w for w in words if w["x0"] >= COL_SPLIT and w["top"] > HEADER_Y]
        right_col.sort(key=lambda w: (round(w["top"] / 5) * 5, w["x0"]))
        if right_col:
            print(f"--- PAGE {p_idx+1} RIGHT COLUMN (first 25) ---")
            for w in right_col[:25]:
                print(f"  y={w['top']:.0f} x={w['x0']:.0f}: {repr(w['text'])}")
