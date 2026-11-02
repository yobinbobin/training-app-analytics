"""Generate reproducible fictitious events for a training-app analytics exercise."""
import csv
import random
from datetime import datetime, timedelta
from pathlib import Path

SEED = 20261102
N_USERS = 4000
OUT = Path(__file__).resolve().parent / 'data'
OUT.mkdir(exist_ok=True)
rng = random.Random(SEED)
channels = ['organic', 'search', 'referral']
channel_weights = [0.48, 0.34, 0.18]
devices = ['android', 'ios']
users = []
events = []
start_day = datetime(2026, 10, 1, 9, 0, 0)
for i in range(N_USERS):
    user_id = f'u{i+1:05}'
    variant = 'A' if i % 2 == 0 else 'B'
    channel = rng.choices(channels, weights=channel_weights, k=1)[0]
    device = rng.choice(devices)
    created_at = start_day + timedelta(days=rng.randrange(28), seconds=rng.randrange(86400))
    users.append((user_id, variant, channel, device, created_at.isoformat(timespec='seconds')))
    events.append((user_id, 'signup', created_at.isoformat(timespec='seconds')))
    step_time = created_at
    # An illustrative funnel, not observed real user behaviour.
    for event, probability in [
        ('plan_view', 0.84),
        ('workout_start', 0.58 if variant == 'A' else 0.64),
        ('workout_finish', 0.70 if variant == 'A' else 0.75),
    ]:
        if rng.random() >= probability:
            break
        step_time += timedelta(minutes=rng.randrange(2, 70))
        events.append((user_id, event, step_time.isoformat(timespec='seconds')))

with (OUT / 'users.csv').open('w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['user_id', 'variant', 'channel', 'device', 'signup_at'])
    writer.writerows(users)
with (OUT / 'events.csv').open('w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['user_id', 'event_name', 'event_at'])
    writer.writerows(events)
print(f'Created {len(users)} users and {len(events)} events (synthetic).')
