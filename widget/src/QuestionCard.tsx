import React, { useState } from 'react';
import type { Question } from './types';

const CHOICE_SYMS = ['①', '②', '③', '④', '⑤'];

// MCP 서버 base URL — 로컬 개발 시 http://localhost:8787, 배포 시 환경변수로 교체
const API_BASE = import.meta.env.VITE_API_BASE ?? 'http://localhost:8787';

interface Props {
    question: Question;
    /** data/images/ 경로의 base URL */
    imageBase: string;
    onGraded?: (isCorrect: boolean, score: number) => void;
}

type Status = 'idle' | 'correct' | 'wrong';

export const QuestionCard: React.FC<Props> = ({ question, imageBase, onGraded }) => {
    const [selected, setSelected] = useState<string | null>(null);
    const [status, setStatus] = useState<Status>('idle');
    const [grading, setGrading] = useState(false);

    const answered = status !== 'idle';

    const handleSelect = async (sym: string) => {
        if (answered || grading) return;
        setSelected(sym);
        setGrading(true);

        try {
            // MCP grade_answer 호출
            const res = await fetch(`${API_BASE}/grade`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    question_id: question.id,
                    user_answer: sym,
                }),
            });
            if (res.ok) {
                const result = await res.json();
                const correct = result.is_correct ?? sym === question.correct_answer;
                const newStatus: Status = correct ? 'correct' : 'wrong';
                setStatus(newStatus);
                onGraded?.(correct, correct ? (question.score ?? 0) : 0);
            } else {
                // API 없으면 로컬 답지로 채점
                fallbackGrade(sym);
            }
        } catch {
            fallbackGrade(sym);
        } finally {
            setGrading(false);
        }
    };

    const fallbackGrade = (sym: string) => {
        const correct = sym === question.correct_answer;
        const newStatus: Status = correct ? 'correct' : 'wrong';
        setStatus(newStatus);
        onGraded?.(correct, correct ? (question.score ?? 0) : 0);
    };

    const choiceClass = (sym: string) => {
        if (!answered) return '';
        if (sym === question.correct_answer && sym === selected) return 'selected-correct';
        if (sym === selected && status === 'wrong') return 'selected-wrong';
        if (sym === question.correct_answer) return 'reveal-correct';
        return '';
    };

    const cardClass = [
        'question-card',
        answered ? `answered-${status}` : '',
    ].filter(Boolean).join(' ');

    return (
        <div className={cardClass}>
            {/* 카드 헤더 */}
            <div className="card-header">
                <span className="q-badge">{question.exam_no}회 {question.question_no}번</span>
                {question.has_image && <span className="img-badge">🖼 이미지 포함</span>}
                <span className="q-score">{question.score ?? '?'}점</span>
            </div>

            {/* 카드 본문 */}
            <div className="card-body">
                {/* 문항 이미지 (PDF 스냅샷) */}
                {question.image_path && (
                    <img
                        className="question-image"
                        src={`${imageBase}/${question.image_path}`}
                        alt={`${question.exam_no}회 ${question.question_no}번 문항`}
                        loading="lazy"
                    />
                )}

                {/* 질문 텍스트 (이미지에 이미 있으면 보조용) */}
                {question.question_text && (
                    <p className="question-text">{question.question_text}</p>
                )}

                {/* 지문 */}
                {question.source_material && (
                    <div className="source-material">{question.source_material}</div>
                )}

                {/* 선택지 */}
                <div className="choices">
                    {CHOICE_SYMS.map((sym) => {
                        const text = question.choices[sym];
                        if (!text && !answered) return null;
                        return (
                            <button
                                key={sym}
                                className={`choice-btn ${choiceClass(sym)}`}
                                onClick={() => handleSelect(sym)}
                                disabled={answered || grading}
                            >
                                <span className="choice-sym">{sym}</span>
                                <span>{text ?? ''}</span>
                            </button>
                        );
                    })}
                </div>

                {/* 결과 배너 */}
                {answered && (
                    <div className={`result-banner ${status}`}>
                        {status === 'correct'
                            ? `✅ 정답! +${question.score ?? 0}점`
                            : `❌ 오답 — 정답은 ${question.correct_answer}`}
                    </div>
                )}
            </div>
        </div>
    );
};
