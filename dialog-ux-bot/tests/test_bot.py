import unittest
from bot import DialogueBot, detect_intent, load_data


class TestDialogueBot(unittest.TestCase):
    def setUp(self):
        self.content, self.orders = load_data()
        self.bot = DialogueBot(self.content, self.orders)

    def test_greeting(self):
        self.assertEqual(self.bot.handle("привет").intent, "greeting")

    def test_status_needs_order(self):
        self.assertEqual(self.bot.handle("где мой заказ").outcome, "need_order")

    def test_followup_order_number(self):
        self.bot.handle("где мой заказ")
        self.assertIn("A1001", self.bot.handle("a1001").text)

    def test_status_in_single_message(self):
        self.assertEqual(self.bot.handle("где мой заказ A1001").outcome, "resolved")

    def test_unknown_order(self):
        self.assertEqual(self.bot.handle("где заказ A9999").outcome, "not_found")

    def test_cancel_no_real_action(self):
        self.assertIn("Демо ничего не отменяет", self.bot.handle("отменить A1002").text)

    def test_cannot_cancel_delivered(self):
        self.assertIn("недоступна", self.bot.handle("отменить A1003").text)

    def test_return_delivered(self):
        self.assertIn("возврата", self.bot.handle("вернуть товар A1003").text)

    def test_return_in_transit(self):
        self.assertIn("ещё не доставлен", self.bot.handle("возврат A1001").text)

    def test_address_change_only_information(self):
        self.assertIn("ничего не меняет", self.bot.handle("изменить адрес A1002").text)

    def test_operator_clears_pending(self):
        self.bot.handle("где заказ")
        self.assertEqual(self.bot.handle("оператор").outcome, "handoff")
        self.assertIsNone(self.bot.pending_intent)

    def test_fallback(self):
        self.assertEqual(self.bot.handle("случайная фраза").outcome, "fallback")

    def test_telemetry_does_not_store_order_ids(self):
        self.bot.handle("где заказ A1001")
        self.assertNotIn("A1001", str(self.bot.events))

    def test_detect_status(self):
        self.assertEqual(detect_intent("где мой заказ A1001", self.content), "order_status")

    def test_phrase_recognition(self):
        self.assertEqual(detect_intent("посмотрите где мой заказ", self.content), "order_status")


if __name__ == "__main__":
    unittest.main()
