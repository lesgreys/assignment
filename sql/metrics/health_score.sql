-- Customer Health Score Calculation
-- Composite score based on usage, business value, sentiment, and engagement

WITH user_metrics AS (
    -- This would reference the output from user_metrics.sql
    -- For now, assume this is a materialized view or temp table
    SELECT * FROM user_metrics_view
),

usage_score AS (
    SELECT
        user_id,
        -- Login frequency (0-100)
        LEAST(100, (logins_30d / 20.0) * 100) as login_score,
        -- Session quality (0-100)
        LEAST(100, (avg_session_length_30d / 30.0) * 100) as session_score,
        -- Core feature usage (0-100)
        CASE
            WHEN (properties_added + tenants_added + leases_signed) >= 10 THEN 100
            WHEN (properties_added + tenants_added + leases_signed) >= 5 THEN 75
            WHEN (properties_added + tenants_added + leases_signed) >= 1 THEN 50
            ELSE 25
        END as core_usage_score,
        -- Feature adoption (0-100)
        LEAST(100, (unique_features_adopted / 5.0) * 100) as adoption_score,
        -- Recency (0-100)
        CASE
            WHEN days_since_last_activity <= 7 THEN 100
            WHEN days_since_last_activity <= 14 THEN 80
            WHEN days_since_last_activity <= 30 THEN 60
            WHEN days_since_last_activity <= 60 THEN 40
            WHEN days_since_last_activity <= 90 THEN 20
            ELSE 0
        END as recency_score
    FROM user_metrics
),

business_value_score AS (
    SELECT
        user_id,
        -- ARR score (0-100) - normalized to max observed
        (annual_revenue / NULLIF((SELECT MAX(annual_revenue) FROM user_metrics), 0)) * 100 as arr_score,
        -- Portfolio size score (0-100)
        LEAST(100, (portfolio_size / 20.0) * 100) as portfolio_score,
        -- Plan tier score
        CASE plan_type
            WHEN 'premium' THEN 100
            WHEN 'pro' THEN 65
            WHEN 'starter' THEN 35
            ELSE 0
        END as plan_score,
        -- Payment activity (0-100)
        LEAST(100, (payments_received / 10.0) * 100) as payment_score
    FROM user_metrics
),

sentiment_score AS (
    SELECT
        user_id,
        -- NPS score normalized to 0-100
        ((nps_score + 100) / 2.0) as nps_normalized,
        -- Support ticket burden (inverted - fewer is better)
        CASE
            WHEN support_tickets_last_90d = 0 THEN 100
            WHEN support_tickets_last_90d <= 2 THEN 80
            WHEN support_tickets_last_90d <= 5 THEN 60
            WHEN support_tickets_last_90d <= 10 THEN 40
            WHEN support_tickets_last_90d <= 20 THEN 20
            ELSE 0
        END as support_health_score
    FROM user_metrics
),

engagement_score AS (
    SELECT
        user_id,
        -- Training completion (0-100)
        LEAST(100, (trainings_attended / 3.0) * 100) as training_score,
        -- Report usage (0-100)
        LEAST(100, (reports_generated / 10.0) * 100) as reporting_score,
        -- Active days ratio (0-100)
        (active_days_30d / 30.0) * 100 as activity_consistency_score
    FROM user_metrics
),

weighted_health AS (
    SELECT
        um.user_id,
        um.signup_date,
        um.plan_type,
        um.annual_revenue,
        um.is_active,
        um.csm_id,
        um.renewal_due_date,
        um.days_to_renewal,

        -- Component scores
        (us.login_score * 0.15 +
         us.session_score * 0.10 +
         us.core_usage_score * 0.30 +
         us.adoption_score * 0.25 +
         us.recency_score * 0.20) as usage_component_score,

        (bv.arr_score * 0.40 +
         bv.portfolio_score * 0.30 +
         bv.plan_score * 0.20 +
         bv.payment_score * 0.10) as business_value_component_score,

        (ss.nps_normalized * 0.60 +
         ss.support_health_score * 0.40) as sentiment_component_score,

        (eg.training_score * 0.30 +
         eg.reporting_score * 0.30 +
         eg.activity_consistency_score * 0.40) as engagement_component_score

    FROM user_metrics um
    LEFT JOIN usage_score us ON um.user_id = us.user_id
    LEFT JOIN business_value_score bv ON um.user_id = bv.user_id
    LEFT JOIN sentiment_score ss ON um.user_id = ss.user_id
    LEFT JOIN engagement_score eg ON um.user_id = eg.user_id
)

SELECT
    user_id,
    signup_date,
    plan_type,
    annual_revenue,
    is_active,
    csm_id,
    renewal_due_date,
    days_to_renewal,

    -- Component scores (0-100)
    ROUND(usage_component_score, 2) as usage_score,
    ROUND(business_value_component_score, 2) as business_value_score,
    ROUND(sentiment_component_score, 2) as sentiment_score,
    ROUND(engagement_component_score, 2) as engagement_score,

    -- Overall Health Score (weighted composite)
    ROUND(
        usage_component_score * 0.40 +
        business_value_component_score * 0.30 +
        sentiment_component_score * 0.20 +
        engagement_component_score * 0.10,
        2
    ) as health_score,

    -- Health tier categorization
    CASE
        WHEN (usage_component_score * 0.40 +
              business_value_component_score * 0.30 +
              sentiment_component_score * 0.20 +
              engagement_component_score * 0.10) >= 80 THEN 'Green'
        WHEN (usage_component_score * 0.40 +
              business_value_component_score * 0.30 +
              sentiment_component_score * 0.20 +
              engagement_component_score * 0.10) >= 60 THEN 'Yellow'
        ELSE 'Red'
    END as health_tier,

    -- Renewal risk flag
    CASE
        WHEN days_to_renewal <= 90
             AND (usage_component_score * 0.40 +
                  business_value_component_score * 0.30 +
                  sentiment_component_score * 0.20 +
                  engagement_component_score * 0.10) < 60
        THEN 1
        ELSE 0
    END as at_renewal_risk

FROM weighted_health
ORDER BY health_score DESC;
