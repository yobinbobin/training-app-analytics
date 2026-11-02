"""Offline dialogue UX prototype with synthetic orders. No real API calls."""
from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parent
ORDER_PATTERN = re.compile(r"\bA\d{4}\b", re.IGNORECASE)


def load_data() -> tuple[dict[str, Any], dict[str, Any]]:
    with (ROOT / "scenarios.yaml").open(encoding="utf-8") as stream:
        content = yaml.safe_load(stream)
    with (ROOT / "fixtures" / "orders.json").open(encoding="utf-8") as stream:
        orders = json.load(stream)
    return content, orders


def detect_intent(text: str, content: dict[str, Any]) -> str:
    """Deterministic keyword matching; this is not a trained NLP model."""
    text = text.lower().strip()
    matches: list[tuple[int, str]] = []
    for intent, config in content["intents"].items():
        for candidate in config["phrases"]:
            phrase = candidate.lower()
            if re.search(r"(?<!\w)" + re.escape(phrase) + r"(?!\w)", text):
                matches.append((len(phrase), intent))
    return max(matches)[1] if matches else "unknown"


@dataclass
class Turn:
    text: str
    intent: str
    outcome: str


class DialogueBot:
    def __init__(self, content: dict[str, Any] | None = None, orders: dict[str, Any] | None = None):
        if content is None or orders is None:
            loaded_content, loaded_orders = load_data()
            content = content if content is not None else loaded_content
            orders = orders if orders is not None else loaded_orders
        self.content = content
        self.orders = orders
        self.pending_intent: str | None = None
        self.events: list[dict[str, str]] = []

    def _respond(self, intent: str, outcome: str, answer: str) -> Turn:
        # Deliberately avoid storing message text and order IDs.
        self.events.append({"intent": intent, "outcome": outcome})
        return Turn(text=answer, intent=intent, outcome=outcome)

    def handle(self, message: str) -> Turn:
        msg = message.strip()
        responses = self.content["responses"]
        if not msg:
            return self._respond("unknown", "fallback", responses["fallback"])
        intent = detect_intent(msg, self.content)
        if intent == "operator":
            self.pending_intent = None
            return self._respond("operator", "handoff", responses["operator"])
        if intent == "greeting":
            return self._respond("greeting", "greeting", responses["hello"])

        match = ORDER_PATTERN.search(msg)
        order_id = match.group(0).upper() if match else None

        if self.pending_intent and order_id and intent == "unknown":
            intent = self.pending_intent
        elif self.pending_intent and not order_id and intent == "unknown":
            return self._respond(self.pending_intent, "need_order", responses["ask_order"])

        if intent == "unknown":
            return self._respond("unknown", "fallback", responses["fallback"])
        if intent not in self.content["requires_order"]:
            return self._respond(intent, "informational", responses.get(intent, responses["fallback"]))

        if order_id is None:
            self.pending_intent = intent
            return self._respond(intent, "need_order", responses["ask_order"])
        self.pending_intent = None
        if order_id not in self.orders:
            return self._respond(intent, "not_found", responses["not_found"])

        order = self.orders[order_id]
        if intent == "order_status":
            status = self.content["status_labels"].get(order["status"], "статус не определён")
            return self._respond(intent, "resolved", responses["status"].format(order_id=order_id, status=status))
        if intent == "return_order":
            key = "return_delivered" if order["status"] == "delivered" else "return_not_delivered"
        elif intent == "cancel_order":
            key = "cancel_possible" if order["status"] == "new" else "cancel_unavailable"
        elif intent == "change_address":
            key = "address_possible" if order["status"] == "new" else "address_unavailable"
        else:
            return self._respond("unknown", "fallback", responses["fallback"])
        return self._respond(intent, "informational", responses[key])


def main() -> None:
    parser = argparse.ArgumentParser(description="Offline demo with fictional orders")
    parser.add_argument("--demo", action="store_true", help="show a scripted dialogue")
    args = parser.parse_args()
    bot = DialogueBot()
    print("Бот поддержки (демо): A1001, A1002, A1003. Для выхода напиши 'выход'.")
    if args.demo:
        sample = ["привет", "Где мой заказ?", "A1001", "Хочу отменить заказ A1002",
                  "не понимаю", "позови оператора"]
        for message in sample:
            print("Вы:", message)
            print("Бот:", bot.handle(message).text)
        return
    while True:
        try:
            message = input("Вы: ")
        except (KeyboardInterrupt, EOFError):
            break
        if message.lower().strip() == "выход":
            break
        print("Бот:", bot.handle(message).text)


if __name__ == "__main__":
    main()
