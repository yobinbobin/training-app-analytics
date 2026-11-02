-- All queries use synthetic data, not real users.
-- Funnel by experiment group: JOIN + conditional aggregates + CTE.
WITH user_steps AS (
    SELECT u.user_id, u.variant,
           MAX(CASE WHEN e.event_name = 'plan_view' THEN 1 ELSE 0 END) AS plan_view,
           MAX(CASE WHEN e.event_name = 'workout_start' THEN 1 ELSE 0 END) AS workout_start,
           MAX(CASE WHEN e.event_name = 'workout_finish' THEN 1 ELSE 0 END) AS workout_finish
    FROM users u
    LEFT JOIN events e ON e.user_id = u.user_id
    GROUP BY u.user_id, u.variant
)
SELECT variant,
       COUNT(*) AS signups,
       SUM(plan_view) AS viewed_plan,
       SUM(workout_start) AS started_workout,
       SUM(workout_finish) AS finished_workout,
       ROUND(100.0 * SUM(workout_finish) / COUNT(*), 2) AS finish_rate_pct
FROM user_steps
GROUP BY variant
ORDER BY variant;

-- Conversion by acquisition channel.
SELECT u.channel,
       COUNT(DISTINCT u.user_id) AS signups,
       COUNT(DISTINCT CASE WHEN e.event_name = 'workout_finish' THEN u.user_id END) AS finishers,
       ROUND(100.0 * COUNT(DISTINCT CASE WHEN e.event_name = 'workout_finish' THEN u.user_id END) / COUNT(DISTINCT u.user_id), 2) AS finish_rate_pct
FROM users u
LEFT JOIN events e ON e.user_id = u.user_id
GROUP BY u.channel
ORDER BY signups DESC;
