-- Cohort Retention Analysis
-- Analyzes user retention by signup cohort

WITH cohort_base AS (
    SELECT
        user_id,
        DATE_TRUNC('month', signup_date) as cohort_month,
        signup_date,
        is_active
    FROM users_cx
),

user_monthly_activity AS (
    SELECT
        e.user_id,
        DATE_TRUNC('month', e.event_ts) as activity_month,
        COUNT(*) as events_in_month
    FROM events_cx_clean e
    GROUP BY e.user_id, DATE_TRUNC('month', e.event_ts)
),

cohort_activity AS (
    SELECT
        cb.cohort_month,
        cb.user_id,
        uma.activity_month,
        DATEDIFF(month, cb.cohort_month, uma.activity_month) as months_since_signup
    FROM cohort_base cb
    LEFT JOIN user_monthly_activity uma ON cb.user_id = uma.user_id
    WHERE uma.activity_month IS NOT NULL
),

cohort_size AS (
    SELECT
        cohort_month,
        COUNT(DISTINCT user_id) as cohort_users
    FROM cohort_base
    GROUP BY cohort_month
),

cohort_retention AS (
    SELECT
        ca.cohort_month,
        ca.months_since_signup,
        COUNT(DISTINCT ca.user_id) as active_users,
        cs.cohort_users,
        (COUNT(DISTINCT ca.user_id)::FLOAT / cs.cohort_users) * 100 as retention_pct
    FROM cohort_activity ca
    JOIN cohort_size cs ON ca.cohort_month = cs.cohort_month
    GROUP BY ca.cohort_month, ca.months_since_signup, cs.cohort_users
)

SELECT
    TO_VARCHAR(cohort_month, 'YYYY-MM') as cohort,
    cohort_users,
    months_since_signup as month,
    active_users,
    ROUND(retention_pct, 2) as retention_rate
FROM cohort_retention
WHERE months_since_signup <= 12  -- Focus on first 12 months
ORDER BY cohort_month DESC, months_since_signup ASC;
