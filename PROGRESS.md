# 📊 진행 상태 (Progress Tracker)

> 마지막 업데이트: 2026-02-24

## 전체 로드맵

| Phase | 내용 | 상태 |
|-------|------|------|
| **0** | 프로젝트 셋업 & Git 초기화 | ✅ 완료 |
| **1** | PDF 파싱 파이프라인 | ✅ 완료 |
| **1b** | 문항 이미지(PNG) 추출 | ✅ 완료 |
| **2** | MCP 서버 구현 | ✅ 완료 |
| **3** | React 위젯 UI | ✅ 완료 |
| **4** | ChatGPT 연결 & 배포 | ⏳ 대기 |

---

## Phase 0 ✅ — 프로젝트 셋업

`git init`, 폴더 구조, `.gitignore`, `PROGRESS.md`, `README.md`

**커밋:** `feat: initial project structure`

---

## Phase 1 ✅ — PDF 파싱 파이프라인

- `parser/parse_answers.py` — 답지 50문항 (정답·배점) 완벽 추출
- `parser/parse_exam.py` v5 — fitz 기반, 2컬럼 분리, **50/50 문항 완전 감지**
- `data/questions_77.json` — 구조화 JSON 생성

**주요 해결 포인트:**
- pdfplumber 한글 인코딩 `?` 문제 → fitz로 교체
- 2컬럼 페이지에서 오른쪽 컬럼 문항 헤더가 `HEADER_Y=100` 필터에 걸림 → `50`으로 조정

**커밋:** `feat: Phase 1 complete - PDF parsing pipeline (50/50 questions)`

---

## Phase 1b ✅ — 문항 이미지 추출

- `parser/extract_images.py` — fitz로 문항 영역 PNG 추출
- `data/images/77-{01~50}.png` — 50개 PNG 생성
- `data/questions_77.json`에 `image_path` 필드 추가

**주요 해결 포인트:**
- 초기 `COL_SPLIT=318` 고정값 → 왼쪽 문항 이미지 잘림
- 실제 페이지 너비 `728.5pt` 기준 `page_w/2 = 364.3pt`로 동적 계산

---

## Phase 2 ✅ — MCP 서버

- `mcp-server/server.py` — FastMCP, 5개 tool 구현
  - `list_exams`, `get_question`, `search_questions`, `grade_answer`, `random_quiz`
- `gpt/system_prompt.md` — System Prompt 작성
- 로컬 실행 확인: `uvicorn http://0.0.0.0:8787/mcp`

**커밋:** `feat: Phase 2 complete - MCP server (5 tools) + system prompt`

---

## Phase 3 ✅ — React 위젯 UI

- `widget/` — Vite + React + TypeScript 프로젝트
- `widget/src/QuestionCard.tsx` — PDF 이미지 + 선택지 + 정답/오답 피드백
- `widget/src/App.tsx` — 문항 로드/필터/랜덤/점수판
- `widget/src/index.css` — 다크 모드 프리미엄 디자인
- 로컬 브라우저 동작 완전 확인 (`http://localhost:5173`)

**커밋:** `feat: Phase 3 complete - React widget with PDF images + grading`

---

## Phase 4 ⏳ — ChatGPT 연결 & 배포

### 4-1. Cloudflare Pages (위젯 호스팅)
```bash
# widget/ 빌드
cd widget && npm run build

# Cloudflare Pages CLI 배포
npx wrangler pages deploy dist --project-name korean-history-widget
```

### 4-2. Cloudflare Workers (MCP 서버)
```bash
# Python Workers는 현재 베타. 대안: Vercel Serverless Function 무료 사용
# 또는 로컬 ngrok 터널로 개인 사용
pip install "mcp[cli]"
cd mcp-server && python server.py   # 포트 8787
ngrok http 8787                     # HTTPS 터널
```

### 4-3. ChatGPT 커넥터 등록
1. ChatGPT → Settings → Apps & Connectors → Advanced settings → **Developer mode ON**
2. 커넥터 추가 → `https://<ngrok-url>/mcp` 입력
3. 이름: "한국사능력검정시험"

---

## 아키텍처 요약

```
ChatGPT ──tool call──▶ MCP 서버 (/mcp)
                           │
              ┌────────────┴────────────┐
         JSON 문항 데이터          위젯 번들 URL
         (questions_77.json)    (Cloudflare Pages)
                                        │
                                 ChatGPT iframe
                                 React 위젯 렌더링
                                 (PDF 이미지 + 선택지)
```

**운영 비용: $0** — Cloudflare Workers/Pages 무료 + GitHub 무료
