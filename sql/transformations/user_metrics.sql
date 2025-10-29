-- User Metrics Aggregation
-- Calculates key user-level metrics from events data

WITH user_activity AS (
    SELECT
        user_id,
        COUNT(DISTINCT DATE(event_ts)) as active_days_total,
        COUNT(DISTINCT CASE
            WHEN event_ts >= DATEADD(day, -30, CURRENT_DATE())
            THEN DATE(event_ts)
        END) as active_days_30d,
        COUNT(DISTINCT CASE
            WHEN event_ts >= DATEADD(day, -60, CURRENT_DATE())
            THEN DATE(event_ts)
        END) as active_days_60d,
        COUNT(DISTINCT CASE
            WHEN event_ts >= DATEADD(day, -90, CURRENT_DATE())
            THEN DATE(event_ts)
        END) as active_days_90d,
        COUNT(*) as total_events,
        COUNT(CASE WHEN event_ts >= DATEADD(day, -30, CURRENT_DATE()) THEN 1 END) as events_30d,
        COUNT(CASE WHEN event_ts >= DATEADD(day, -60, CURRENT_DATE()) THEN 1 END) as events_60d,
        COUNT(CASE WHEN event_ts >= DATEADD(day, -90, CURRENT_DATE()) THEN 1 END) as events_90d,
        MAX(event_ts) as last_activity_date,
        MIN(event_ts) as first_activity_date,
        DATEDIFF(day, CURRENT_DATE(), MAX(event_ts)) as days_since_last_activity
    FROM events_cx_clean
    GROUP BY user_id
),

login_metrics AS (
    SELECT
        user_id,
        COUNT(*) as total_logins,
        COUNT(CASE WHEN event_ts >= DATEADD(day, -30, CURRENT_DATE()) THEN 1 END) as logins_30d,
        AVG(event_value_num) as avg_session_length_mins,
        AVG(CASE
            WHEN event_ts >= DATEADD(day, -30, CURRENT_DATE())
            THEN event_value_num
        END) as avg_session_length_30d
    FROM events_cx_clean
    WHERE event_type = 'login'
    GROUP BY user_id
),

core_actions AS (
    SELECT
        user_id,
        COUNT(CASE WHEN event_type = 'property_added' THEN 1 END) as properties_added,
        COUNT(CASE WHEN event_type = 'tenant_added' THEN 1 END) as tenants_added,
        COUNT(CASE WHEN event_type = 'lease_signed' THEN 1 END) as leases_signed,
        COUNT(CASE WHEN event_type = 'rent_payment_received' THEN 1 END) as payments_received,
        SUM(CASE WHEN event_type = 'rent_payment_received' THEN event_value_num ELSE 0 END) as total_rent_collected,
        COUNT(CASE WHEN event_type = 'maintenance_request_created' THEN 1 END) as maintenance_requests,
        COUNT(CASE WHEN event_type = 'report_generated' THEN 1 END) as reports_generated
    FROM events_cx_clean
    WHERE event_type IN (
        'property_added', 'tenant_added', 'lease_signed',
        'rent_payment_received', 'maintenance_request_created', 'report_generated'
    )
    GROUP BY user_id
),

feature_adoption AS (
    SELECT
        user_id,
        COUNT(DISTINCT event_value_txt) as unique_features_adopted,
        LISTAGG(DISTINCT event_value_txt, ', ') as adopted_features
    FROM events_cx_clean
    WHERE event_type = 'feature_adopted'
    GROUP BY user_id
),

training AS (
    SELECT
        user_id,
        COUNT(*) as trainings_attended,
        COUNT(DISTINCT event_value_txt) as unique_training_types
    FROM events_cx_clean
    WHERE event_type = 'training_attended'
    GROUP BY user_id
)

SELECT
    u.user_id,
    u.signup_date,
    u.plan_type,
    u.portfolio_size,
    u.annual_revenue,
    u.is_active,
    u.nps_score,
    u.support_tickets_last_90d,
    u.success_manager_assigned,
    u.csm_id,
    u.renewal_due_date,
    DATEDIFF(day, u.signup_date, CURRENT_DATE()) as account_age_days,
    DATEDIFF(day, CURRENT_DATE(), u.renewal_due_date) as days_to_renewal,

    -- Activity metrics
    COALESCE(ua.active_days_total, 0) as active_days_total,
    COALESCE(ua.active_days_30d, 0) as active_days_30d,
    COALESCE(ua.active_days_60d, 0) as active_days_60d,
    COALESCE(ua.active_days_90d, 0) as active_days_90d,
    COALESCE(ua.total_events, 0) as total_events,
    COALESCE(ua.events_30d, 0) as events_30d,
    COALESCE(ua.events_60d, 0) as events_60d,
    COALESCE(ua.events_90d, 0) as events_90d,
    ua.last_activity_date,
    ua.first_activity_date,
    COALESCE(ua.days_since_last_activity, 999) as days_since_last_activity,

    -- Login metrics
    COALESCE(lm.total_logins, 0) as total_logins,
    COALESCE(lm.logins_30d, 0) as logins_30d,
    COALESCE(lm.avg_session_length_mins, 0) as avg_session_length_mins,
    COALESCE(lm.avg_session_length_30d, 0) as avg_session_length_30d,

    -- Core actions
    COALESCE(ca.properties_added, 0) as properties_added,
    COALESCE(ca.tenants_added, 0) as tenants_added,
    COALESCE(ca.leases_signed, 0) as leases_signed,
    COALESCE(ca.payments_received, 0) as payments_received,
    COALESCE(ca.total_rent_collected, 0) as total_rent_collected,
    COALESCE(ca.maintenance_requests, 0) as maintenance_requests,
    COALESCE(ca.reports_generated, 0) as reports_generated,

    -- Feature adoption
    COALESCE(fa.unique_features_adopted, 0) as unique_features_adopted,
    fa.adopted_features,

    -- Training
    COALESCE(tr.trainings_attended, 0) as trainings_attended,
    COALESCE(tr.unique_training_types, 0) as unique_training_types

FROM users_cx u
LEFT JOIN user_activity ua ON u.user_id = ua.user_id
LEFT JOIN login_metrics lm ON u.user_id = lm.user_id
LEFT JOIN core_actions ca ON u.user_id = ca.user_id
LEFT JOIN feature_adoption fa ON u.user_id = fa.user_id
LEFT JOIN training tr ON u.user_id = tr.user_id;
