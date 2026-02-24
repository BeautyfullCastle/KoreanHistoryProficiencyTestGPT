import { useState, useEffect } from 'react';
import './index.css';
import { QuestionCard } from './QuestionCard';
import type { Question } from './types';

// 데이터 URL — 빌드 시 Cloudflare Pages에서 /data/questions_77.json 서빙
const DATA_URL = import.meta.env.VITE_DATA_URL ?? '/data/questions_77.json';
const IMAGE_BASE = import.meta.env.VITE_IMAGE_BASE ?? '/data';

export default function App() {
  const [allQuestions, setAllQuestions] = useState<Question[]>([]);
  const [displayed, setDisplayed] = useState<Question[]>([]);
  const [qNo, setQNo] = useState(0);     // 0 = 전체
  const [score, setScore] = useState(0);
  const [answered, setAnswered] = useState(0);
  const [correct, setCorrect] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // 데이터 로드
  useEffect(() => {
    setLoading(true);
    fetch(DATA_URL)
      .then(r => r.json())
      .then(d => {
        setAllQuestions(d.questions ?? []);
        setDisplayed(d.questions ?? []);
        setLoading(false);
      })
      .catch(() => {
        setError('문항 데이터를 불러오지 못했습니다.');
        setLoading(false);
      });
  }, []);

  const handleLoad = () => {
    let qs = allQuestions;
    if (qNo > 0) qs = qs.filter(q => q.question_no === qNo);
    setDisplayed(qs);
    setScore(0); setAnswered(0); setCorrect(0);
  };

  const handleRandom = () => {
    const shuffled = [...allQuestions].sort(() => Math.random() - 0.5).slice(0, 5);
    setDisplayed(shuffled);
    setScore(0); setAnswered(0); setCorrect(0);
  };

  const handleReset = () => {
    setDisplayed(allQuestions);
    setScore(0); setAnswered(0); setCorrect(0);
  };

  const handleGraded = (isCorrect: boolean, pts: number) => {
    setAnswered(p => p + 1);
    if (isCorrect) { setCorrect(p => p + 1); setScore(p => p + pts); }
  };

  const total = displayed.reduce((s, q) => s + (q.score ?? 0), 0);

  return (
    <div className="app">
      {/* 헤더 */}
      <header className="header">
        <h1>🏛 한국사능력검정시험 기출 마스터</h1>
        <p>심화 기출문제를 풀고 즉각 채점받으세요</p>
      </header>

      {/* 컨트롤 */}
      <div className="controls">
        <label>문항 번호</label>
        <input
          type="number" min={0} max={50} value={qNo}
          onChange={e => setQNo(Number(e.target.value))}
          placeholder="0=전체"
        />
        <button className="btn btn-primary" onClick={handleLoad}>불러오기</button>
        <button className="btn btn-secondary" onClick={handleRandom}>랜덤 5문항</button>
        <button className="btn btn-secondary" onClick={handleReset}>전체 초기화</button>
      </div>

      {/* 점수판 */}
      {answered > 0 && (
        <div className="scoreboard">
          <div className="score-item">
            <span className="score-label">획득 점수</span>
            <span className="score-value total">{score} / {total}점</span>
          </div>
          <div className="score-item">
            <span className="score-label">정답</span>
            <span className="score-value correct">{correct}</span>
          </div>
          <div className="score-item">
            <span className="score-label">오답</span>
            <span className="score-value wrong">{answered - correct}</span>
          </div>
          <div className="score-item">
            <span className="score-label">풀이 진행</span>
            <span className="score-value">{answered} / {displayed.length}</span>
          </div>
        </div>
      )}

      {/* 문항 목록 */}
      {loading && <p style={{ textAlign: 'center', color: 'var(--text-sub)' }}>로딩 중…</p>}
      {error && <p style={{ textAlign: 'center', color: 'var(--wrong)' }}>{error}</p>}

      {!loading && !error && displayed.length === 0 && (
        <div className="empty-state">
          <div className="icon">📭</div>
          <p>표시할 문항이 없습니다.</p>
        </div>
      )}

      {displayed.map(q => (
        <QuestionCard
          key={q.id}
          question={q}
          imageBase={IMAGE_BASE}
          onGraded={handleGraded}
        />
      ))}
    </div>
  );
}
