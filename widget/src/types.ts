// Types for question data from questions_77.json
export interface Question {
    id: string;
    exam_no: number;
    question_no: number;
    score: number | null;
    question_text: string;
    source_material: string;
    has_image: boolean;
    image_note: string | null;
    image_path: string | null;
    choices: Record<string, string>;
    correct_answer: string | null;
    keywords: string[];
}
