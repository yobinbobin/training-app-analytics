# Dialogue UX Lab - support chatbot prototype

**Independent educational demo. Not connected with Ozon or real order data.**

A reproducible Python exercise in conversational UX: dialogue scenarios, JSON/YAML, mocked order lookup, user-friendly fallback and human-handoff flow. It is not a trained NLP model.

## Scenarios

- Delivery status
- Cancellation
- Returns
- Delivery address changes
- Escalation to an operator
- Greeting and unrecognized queries

The bot remembers a pending request when it needs an order number, then completes the dialogue when an ID arrives in the next message. It never changes orders and never collects addresses or phone numbers.

## Quick start

Python 3.10+

```bash
pip install -r requirements.txt
python bot.py --demo
python bot.py
python -m unittest discover -s tests -v
python evaluate.py
```

Test IDs: `A1001` (in transit), `A1002` (new), `A1003` (delivered). Try `где мой заказ` then `A1001`, `возврат A1003`, or `позови оператора`.

## Structure

- `scenarios.yaml`: editable content, phrases, statuses, messages
- `fixtures/orders.json`: fictitious order API data
- `fixtures/evaluation.json`: hand-written simulated utterances
- `bot.py`: rule-based intent recognition and conversation state
- `evaluate.py`: small intent test set and event outcomes
- `tests/test_bot.py`: automated tests for dialogue/error paths

## UX rationale

1. Keep onboarding short and action-oriented.
2. Ask for the minimal missing information while preserving context.
3. Offer examples when the request is not recognized.
4. Explain unavailable actions rather than pretending to cancel orders or contact an operator.
5. Separate copy/scenarios from code so support editors can change texts in YAML.
6. Record only intent/outcome in example telemetry, without raw user messages or order numbers.

## Results and limitations

Locally checked: **15 automated tests pass**; rule-based intent recognition matches **17 of 17 hand-written synthetic examples**. The set is small and biased by design, so this is **not** evidence of real-world NLP accuracy or production UX effectiveness.

Uses a deterministic keyword matcher and offline mock data, not machine learning, speech analytics or real APIs. It does not connect to any company systems. A production version would need authorization, schema validation, security reviews, analytics on opt-in anonymized data, human handoff and real-world evaluation.

Created for a student portfolio with AI assistance; the candidate should inspect and explain the code before claiming hands-on authorship.
