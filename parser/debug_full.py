"""
debug_full.py - 전페이지에 걸쳐 문항번호 포함 토큰 찾기
"""
import pdfplumber, re

COL_SPLIT = 318.0
HEADER_Y = 100.0
Q_PAT = re.compile(r'^(\d{1,2})\.$')

with pdfplumber.open("pdfs/77회 한국사_문제지(심화).pdf") as pdf:
    print(f"총 {len(pdf.pages)}페이지\n")
    for p_idx, page in enumerate(pdf.pages):
        words = page.extract_words() or []
        words_filtered = [w for w in words if w["top"] > HEADER_Y]
        
        # 문항번호 토큰 탐지
        q_tokens = []
        for i, w in enumerate(words_filtered):
            if Q_PAT.match(w["text"].strip()):
                q_no = int(w["text"].strip()[:-1])
                if 1 <= q_no <= 50:
                    col = "L" if w["x0"] < COL_SPLIT else "R"
                    q_tokens.append((q_no, col, w["top"], w["x0"]))
        
        if q_tokens:
            print(f"P{p_idx+1}: {[(q, c) for q,c,y,x in q_tokens]}")
        
        # 전체 단어 중 숫자+점 패턴 전부 출력
        num_dot = [w for w in words_filtered if Q_PAT.match(w["text"].strip())]
        if num_dot:
            print(f"  숫자+점 토큰: {[(w['text'], round(w['top']), round(w['x0'])) for w in num_dot]}")
