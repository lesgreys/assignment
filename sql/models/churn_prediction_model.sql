-- Churn Prediction Model Schema
-- Features and scoring logic for churn risk prediction

-- Model Purpose: Identify users at high risk of churning within next 90 days
-- Approach: Logistic Regression / Random Forest (implemented in Python)
-- Target: subscription_cancelled event or is_active = 0

-- FEATURE ENGINEERING
WITH churn_labels AS (
    -- Define churn: cancelled subscription or went inactive
    SELECT DISTINCT
        user_id,
        1 as churned
    FROM events_cx_clean
    WHERE event_type = 'subscription_cancelled'

    UNION

    SELECT
        user_id,
        1 as churned
    FROM users_cx
    WHERE is_active = 0
),

model_features AS (
    SELECT
        um.user_id,

        -- Demographics
        um.plan_type,
        um.account_age_days,
        um.portfolio_size,
        um.annual_revenue,
        um.success_manager_assigned,

        -- Usage Features (key predictors)
        um.active_days_30d,
        um.active_days_60d,
        um.active_days_90d,
        um.logins_30d,
        um.avg_session_length_30d,
        um.total_events,
        um.events_30d,
        um.events_60d,
        um.days_since_last_activity,

        -- Engagement declining trend
        CASE
            WHEN um.events_30d < um.events_60d THEN 1
            ELSE 0
        END as engagement_declining,

        -- Core product usage
        um.properties_added,
        um.tenants_added,
        um.leases_signed,
        um.payments_received,
        um.reports_generated,

        -- Feature adoption
        um.unique_features_adopted,
        um.trainings_attended,

        -- Sentiment indicators
        um.nps_score,
        um.support_tickets_last_90d,

        -- Health scores
        hs.health_score,
        hs.usage_component_score,
        hs.business_value_component_score,
        hs.sentiment_component_score,
        hs.engagement_component_score,

        -- Target variable
        COALESCE(cl.churned, 0) as churned

    FROM user_metrics_view um
    LEFT JOIN health_scores_view hs ON um.user_id = hs.user_id
    LEFT JOIN churn_labels cl ON um.user_id = cl.user_id
    WHERE um.account_age_days >= 30  -- Only users with at least 30 days tenure
)

SELECT
    user_id,

    -- Categorical features (to be one-hot encoded)
    plan_type,
    success_manager_assigned,

    -- Numerical features (to be normalized/scaled)
    account_age_days,
    portfolio_size,
    annual_revenue,
    active_days_30d,
    active_days_60d,
    active_days_90d,
    logins_30d,
    avg_session_length_30d,
    total_events,
    events_30d,
    events_60d,
    days_since_last_activity,
    engagement_declining,
    properties_added,
    tenants_added,
    leases_signed,
    payments_received,
    reports_generated,
    unique_features_adopted,
    trainings_attended,
    nps_score,
    support_tickets_last_90d,
    health_score,
    usage_component_score,
    business_value_component_score,
    sentiment_component_score,
    engagement_component_score,

    -- Target
    churned

FROM model_features;

-- KEY FEATURE IMPORTANCE (expected from model):
-- 1. days_since_last_activity (high impact)
-- 2. health_score (high impact)
-- 3. active_days_30d (high impact)
-- 4. nps_score (medium impact)
-- 5. engagement_declining (medium impact)
-- 6. support_tickets_last_90d (medium impact)
-- 7. unique_features_adopted (medium impact)
-- 8. logins_30d (medium impact)

-- MODEL EVALUATION METRICS:
-- - Precision: % of predicted churns that actually churned
-- - Recall: % of actual churns we caught
-- - F1 Score: Balance between precision and recall
-- - AUC-ROC: Model's ability to discriminate churners from non-churners
-- - Threshold tuning: Optimize for catching high-value at-risk accounts

-- SCORING LOGIC (for new predictions):
-- 1. Load user features (same schema as above)
-- 2. Apply trained model
-- 3. Output: churn_probability (0-1)
-- 4. Classify risk:
--    - High Risk: probability >= 0.7
--    - Medium Risk: 0.4 <= probability < 0.7
--    - Low Risk: probability < 0.4
