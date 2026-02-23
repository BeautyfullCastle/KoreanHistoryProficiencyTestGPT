"""
debug_spans.py - fitz JSON으로 Q5 주변 span 정보 확인
"""
import fitz, json, re

doc = fitz.open("pdfs/77회 한국사_문제지(심화).pdf")

# Look for 5. pattern in all pages using fitz json
Q_PAT = re.compile(r'\b5\b')

for p_idx in range(4):
    page = doc[p_idx]
    data = json.loads(page.get_text("json"))
    
    for block in data.get("blocks", []):
        if block.get("type") != 0:  # text block only
            continue
        for line in block.get("lines", []):
            spans = line.get("spans", [])
            full_line = "".join(s["text"] for s in spans)
            # Check if line starts with "5" or contains "5."
            stripped = full_line.strip()
            if re.match(r'^5[\.\s]', stripped) or stripped == "5":
                bbox = line.get("bbox", [])
                print(f"P{p_idx+1} y={bbox[1]:.0f} x={bbox[0]:.0f}: {repr(full_line[:80])}")
                # Show individual spans
                for s in spans[:5]:
                    print(f"  span: {repr(s['text'])} font={s.get('font','?')} size={s.get('size',0):.1f}")
