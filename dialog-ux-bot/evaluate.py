"""Evaluate rule-based intent matching on hand-written synthetic phrases."""
import json
from pathlib import Path
from bot import DialogueBot, detect_intent, load_data

ROOT = Path(__file__).resolve().parent


def main():
    content, orders = load_data()
    dataset = json.loads((ROOT / "fixtures" / "evaluation.json").read_text(encoding="utf-8"))
    passed = 0
    for item in dataset:
        predicted = detect_intent(item["message"], content)
        if predicted == item["expected_intent"]:
            passed += 1
        else:
            print("Mismatch:", item["message"], predicted, item["expected_intent"])
    print(f"Hand-written synthetic phrase accuracy: {passed}/{len(dataset)} = {passed/len(dataset):.1%}")
    bot = DialogueBot(content, orders)
    for message in ["где мой заказ", "A1001", "моя кошка грустит", "оператор"]:
        turn = bot.handle(message)
        print(repr(message), turn.intent, turn.outcome)
    print("Privacy-aware events:", json.dumps(bot.events, ensure_ascii=False))


if __name__ == "__main__":
    main()
