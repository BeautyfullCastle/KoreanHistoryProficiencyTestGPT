import json

with open("data/questions_77.json", encoding="utf-8") as f:
    data = json.load(f)

qs = data["questions"]
print(f"총 문항: {len(qs)}")

no_choice = [q for q in qs if len(q["choices"]) < 5]
print(f"선택지 5개 미만: {len(no_choice)}문항")

print("\n--- 샘플 1번 ---")
q = qs[0]
print(f"질문: {q['question_text']}")
print(f"지문: {q['source_material'][:100]}")
print(f"선택지 수: {len(q['choices'])}")
print(f"선택지: {list(q['choices'].keys())}")

print("\n--- 선택지 없는 문항 (5개 샘플) ---")
for q in no_choice[:5]:
    print(f"{q['question_no']}번 choices={q['choices']}, text={q['question_text'][:50]}")
