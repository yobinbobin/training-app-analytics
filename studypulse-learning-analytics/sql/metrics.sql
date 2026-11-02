-- 1. Multi-step user funnel by acquisition channel.
-- Distinct user aggregation avoids event-join fanout.
WITH user_flags AS (
 SELECT s.student_id, s.channel,
  MAX(CASE WHEN e.event_name = 'course_open' THEN 1 ELSE 0 END) AS opened,
  MAX(CASE WHEN e.event_name = 'lesson_start' THEN 1 ELSE 0 END) AS started,
  MAX(CASE WHEN e.event_name = 'lesson_complete' THEN 1 ELSE 0 END) AS completed,
  MAX(CASE WHEN e.event_name = 'quiz_pass' THEN 1 ELSE 0 END) AS passed
 FROM students AS s LEFT JOIN events e ON e.student_id=s.student_id
 GROUP BY s.student_id, s.channel
)
SELECT channel, COUNT(*) AS enrolled, SUM(opened) AS opened, SUM(started) AS started,
       SUM(completed) AS completed, SUM(passed) AS passed,
       ROUND(100.0 * SUM(completed) / COUNT(*), 2) AS completion_pct
FROM user_flags GROUP BY channel ORDER BY enrolled DESC;

-- 2. Activation cohorts, D7 return window and a right-censoring safeguard.
WITH first_week AS (
 SELECT s.student_id, s.course,
        date(s.enrolled_at, printf('-%d days', (CAST(strftime('%w', s.enrolled_at) AS INTEGER) + 6) % 7)) AS cohort_week,
        s.enrolled_at,
        MAX(CASE WHEN e.event_name='lesson_complete' AND
         julianday(e.occurred_at)-julianday(s.enrolled_at) < 7 THEN 1 ELSE 0 END) AS activated,
        MAX(CASE WHEN julianday(e.occurred_at)-julianday(s.enrolled_at) >= 7
                  AND julianday(e.occurred_at)-julianday(s.enrolled_at) < 14 THEN 1 ELSE 0 END) AS returned_d7
 FROM students s LEFT JOIN events e ON s.student_id=e.student_id
 GROUP BY s.student_id, s.course, s.enrolled_at
)
SELECT cohort_week, course,
       COUNT(*) AS enrolled,
       ROUND(100.0*SUM(activated)/COUNT(*), 2) AS activation_pct,
       COUNT(CASE WHEN julianday('2026-11-01 23:59:59')-julianday(enrolled_at)>=14 THEN 1 END) AS d7_eligible,
       ROUND(100.0*SUM(CASE WHEN julianday('2026-11-01 23:59:59')-julianday(enrolled_at)>=14
         THEN returned_d7 ELSE 0 END) / NULLIF(COUNT(CASE WHEN julianday('2026-11-01 23:59:59')-julianday(enrolled_at)>=14 THEN 1 END),0),2) AS d7_pct
FROM first_week GROUP BY cohort_week, course ORDER BY cohort_week, course;

-- 3. Weekly active learners (WAU), excluding synthetic data duplication after cleanup.
SELECT strftime('%Y-%W', occurred_at) AS calendar_week, COUNT(DISTINCT student_id) AS active_learners
FROM events GROUP BY strftime('%Y-%W', occurred_at) ORDER BY calendar_week;


-- 4. Week-over-week active learners using an analytic window function.
WITH weekly AS (
 SELECT strftime('%Y-%W', occurred_at) AS calendar_week,
        COUNT(DISTINCT student_id) AS wau
 FROM events GROUP BY strftime('%Y-%W', occurred_at)
)
SELECT calendar_week, wau,
       LAG(wau) OVER (ORDER BY calendar_week) AS previous_wau,
       ROUND(100.0 * (wau - LAG(wau) OVER (ORDER BY calendar_week)) /
         NULLIF(LAG(wau) OVER (ORDER BY calendar_week), 0), 2) AS wow_change_pct
FROM weekly ORDER BY calendar_week;
