# 📊 진행 상태 (Progress Tracker)

> 마지막 업데이트: 2026-02-23

## 전체 로드맵

| Phase | 내용 | 상태 |
|-------|------|------|
| **0** | 프로젝트 셋업 & Git 초기화 | ✅ 완료 |
| **1** | PDF 파싱 파이프라인 | ✅ 완료 |
| **2** | MCP 서버 구현 | 🔄 진행 중 |
| **3** | React 위젯 UI | ⏳ 대기 |
| **4** | ChatGPT 연결 & 배포 | ⏳ 대기 |

---

## Phase 0 — 프로젝트 셋업 ✅

- [x] `git init`
- [x] 폴더 구조 생성 (`parser/`, `data/`, `mcp-server/`, `widget/`, `pdfs/`)
- [x] `.gitignore`, `PROGRESS.md`, `README.md`

**커밋:** `feat: initial project structure`

---

## Phase 1 — PDF 파싱 파이프라인 ✅

- [x] `parser/parse_answers.py` — 답지 파싱 (50문항 / 정답 / 배점 완벽 추출)
- [x] `parser/parse_exam.py` — 문제지 파싱 (v5 fitz 기반, 2컬럼 처리, **50/50 문항 완전 감지**)
- [x] `data/questions_77.json` — 50문항 구조화 JSON 생성

**해결 포인트:**
- PDF 2컬럼 레이아웃 → 좌/우 컬럼 분리 후 y순 정렬
- pdfplumber 한글 인코딩 문제 → fitz `get_text("words")` 로 대체
- 문항 HEADER_Y=100 필터 오탐 → 50으로 조정 (Q5 등이 y=67 위치)

**커밋:** `feat: Phase 1 complete - PDF parsing pipeline (50/50 questions)`

---

## Phase 2 — MCP 서버 ⏳

- [ ] `mcp-server/server.py` — FastMCP 서버
- [ ] Tools: `get_question`, `search_questions`, `grade_answer`, `random_quiz`, `list_exams`
- [ ] Cloudflare Workers 배포

---

## Phase 3 — React 위젯 ⏳

- [ ] `widget/src/App.tsx` — 문항 카드 컴포넌트
- [ ] Vite 빌드 → `widget/dist/`
- [ ] Cloudflare Pages 배포

---

## Phase 4 — ChatGPT 연결 ⏳

- [ ] ngrok 터널로 로컬 테스트
- [ ] ChatGPT 커넥터 등록
- [ ] 최종 배포

---

## 아키텍처 요약

```
ChatGPT ──tool call──▶ MCP 서버 (Cloudflare Workers)
                           │
                ┌──────────┴──────────┐
           JSON 문항 데이터        위젯 URL 반환
           (GitHub 정적 파일)    (Cloudflare Pages)
                                       │
                                 ChatGPT iframe
                                 React 위젯 렌더링
```

**비용: $0** — Cloudflare Workers (무료) + Pages (무료) + GitHub (무료)
