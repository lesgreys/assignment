# CX Analytics Dashboard - Calculations Reference

**Document Version:** 1.0
**Last Updated:** 2025-10-29
**Reference Date for Calculations:** 2025-08-01

---

## Table of Contents

1. [Health Score Calculations](#1-health-score-calculations)
2. [Activity Metrics Calculations](#2-activity-metrics-calculations)
3. [Churn Prediction Calculations](#3-churn-prediction-calculations)
4. [Retention & Cohort Analysis](#4-retention--cohort-analysis)
5. [Revenue Retention Metrics](#5-revenue-retention-metrics)
6. [Revenue Analytics](#6-revenue-analytics)
7. [CSM Workload Calculations](#7-csm-workload-calculations)
8. [Adoption & Engagement Metrics](#8-adoption--engagement-metrics)
9. [User Flow & Timeline Calculations](#9-user-flow--timeline-calculations)
10. [Statistical Aggregations](#10-statistical-aggregations)
11. [Derived Fields & Transformations](#11-derived-fields--transformations)
12. [Reference Constants](#12-reference-constants)

---

## 1. Health Score Calculations

**Location:** `src/utils/data_processor.py` (lines 169-269)

### 1.1 Overall Health Score Formula

The Health Score is a weighted composite metric ranging from 0-100:

```
Health Score = (Usage Component × 40%) +
               (Business Value × 30%) +
               (Sentiment × 20%) +
               (Engagement × 10%)
```

### 1.2 Usage Component (40% weight)

Measures product usage patterns and engagement depth.

#### Sub-components:

**Login Score (15% of usage):**
```
Login Score = min(100, (logins_30d / 20) × 100)
```
- Benchmark: 20 logins per 30 days = 100 score
- Capped at 100 for users exceeding benchmark

**Session Score (10% of usage):**
```
Session Score = min(100, (avg_session_30d / 30) × 100)
```
- Benchmark: 30 minutes average session = 100 score
- Capped at 100 for longer sessions

**Core Usage Score (30% of usage):**
```
Core Actions = property_added_count + tenant_added_count + lease_signed_count

Score Bins:
- 0 actions → 0 points
- 1 action → 25 points
- 2-5 actions → 50 points
- 6-10 actions → 75 points
- 11+ actions → 100 points
```

**Adoption Score (25% of usage):**
```
Adoption Score = min(100, (unique_features / 5) × 100)
```
- Benchmark: 5 unique features adopted = 100 score
- Measures breadth of platform utilization

**Recency Score (20% of usage):**
```
Score by Days Since Last Activity:
- ≤7 days → 100 points
- 8-14 days → 80 points
- 15-30 days → 60 points
- 31-60 days → 40 points
- 61-90 days → 20 points
- >90 days → 0 points
```

**Final Usage Component:**
```
Usage Component = (Login Score × 0.15) +
                  (Session Score × 0.10) +
                  (Core Usage Score × 0.30) +
                  (Adoption Score × 0.25) +
                  (Recency Score × 0.20)
```

### 1.3 Business Value Component (30% weight)

Measures customer revenue potential and account value.

**ARR Score (40% of business value):**
```
ARR Score = (user_annual_revenue / max_arr_in_dataset) × 100
```
- Relative scoring based on portfolio maximum
- Higher revenue = higher score

**Portfolio Score (30% of business value):**
```
Portfolio Score = min(100, (portfolio_size / 20) × 100)
```
- Benchmark: 20 properties = 100 score
- Measures customer scale

**Plan Score (30% of business value):**
```
Plan Scoring:
- Premium → 100 points
- Pro → 65 points
- Starter → 35 points
```

**Final Business Value Component:**
```
Business Value = (ARR Score × 0.40) +
                 (Portfolio Score × 0.30) +
                 (Plan Score × 0.30)
```

### 1.4 Sentiment Component (20% weight)

Measures customer satisfaction and support interactions.

**NPS Normalized (60% of sentiment):**
```
NPS Normalized = (nps_score + 100) / 2
```
- Converts NPS range (-100 to 100) → (0 to 100)
- Example: NPS of 50 → Normalized score of 75

**Support Health (40% of sentiment):**
```
Score by Support Tickets (Last 90 Days):
- 0 tickets → 100 points
- 1-2 tickets → 80 points
- 3-5 tickets → 60 points
- 6-10 tickets → 40 points
- 11-20 tickets → 20 points
- 21+ tickets → 0 points
```
- More tickets = lower health (indicates issues)

**Final Sentiment Component:**
```
Sentiment Component = (NPS Normalized × 0.60) + (Support Health × 0.40)
```

### 1.5 Engagement Component (10% weight)

Measures proactive engagement with platform.

**Training Score (30% of engagement):**
```
Training Score = min(100, (trainings_attended / 3) × 100)
```
- Benchmark: 3 trainings = 100 score

**Reporting Score (30% of engagement):**
```
Reporting Score = min(100, (report_generated_count / 10) × 100)
```
- Benchmark: 10 reports = 100 score

**Consistency Score (40% of engagement):**
```
Consistency Score = (active_days_30d / 30) × 100
```
- Daily activity = 100 score
- Measures usage regularity

**Final Engagement Component:**
```
Engagement Component = (Training Score × 0.30) +
                       (Reporting Score × 0.30) +
                       (Consistency Score × 0.40)
```

### 1.6 Health Tier Classification

```
Health Tier Assignment:
- Red: Health Score < 60
- Yellow: 60 ≤ Health Score < 80
- Green: 80 ≤ Health Score ≤ 100
```

### 1.7 Renewal Risk Flag

```
At Renewal Risk = (days_to_renewal ≤ 90) AND (health_score < 60)
```
- Flags accounts within 90 days of renewal with poor health

---

## 2. Activity Metrics Calculations

**Location:** `src/utils/data_processor.py` (lines 43-72)

### 2.1 User Activity Metrics

**Total Events:**
```
total_events = COUNT(all events per user)
```

**Days Since Last Activity:**
```
days_since_last_activity = reference_date - max(event_ts)
Reference Date: 2025-08-01
```

**Time-Windowed Activity:**
```
events_30d = COUNT(events WHERE event_ts >= reference_date - 30 days)
events_60d = COUNT(events WHERE event_ts >= reference_date - 60 days)
events_90d = COUNT(events WHERE event_ts >= reference_date - 90 days)

active_days_30d = COUNT(DISTINCT event_date WHERE event_ts >= reference_date - 30 days)
active_days_60d = COUNT(DISTINCT event_date WHERE event_ts >= reference_date - 60 days)
active_days_90d = COUNT(DISTINCT event_date WHERE event_ts >= reference_date - 90 days)
```

### 2.2 Login Metrics

**Location:** Lines 74-101

```
total_logins = COUNT(events WHERE event_type = 'login')
avg_session_length = MEAN(event_value_num WHERE event_type = 'login')
logins_30d = COUNT(logins WHERE event_ts >= reference_date - 30 days)
avg_session_30d = MEAN(session_length WHERE event_ts >= reference_date - 30 days)
```
- Session length measured in minutes
- Recent activity (30d) weighted more heavily than lifetime

### 2.3 Core Actions Metrics

**Location:** Lines 103-135

Counts of business-critical events:

```
property_added_count = COUNT(events WHERE event_type = 'property_added')
tenant_added_count = COUNT(events WHERE event_type = 'tenant_added')
lease_signed_count = COUNT(events WHERE event_type = 'lease_signed')
payments_received = COUNT(events WHERE event_type = 'rent_payment_received')
maintenance_requests = COUNT(events WHERE event_type = 'maintenance_request_created')
report_generated_count = COUNT(events WHERE event_type = 'report_generated')

total_rent_collected = SUM(event_value_num WHERE event_type = 'rent_payment_received')
```

### 2.4 Feature Adoption Metrics

**Location:** Lines 137-151

```
features_adopted = COUNT(events WHERE event_type = 'feature_adopted')
unique_features = COUNT(DISTINCT event_value_txt WHERE event_type = 'feature_adopted')
```
- Tracks both volume and breadth of feature usage

### 2.5 Training Metrics

**Location:** Lines 153-167

```
trainings_attended = COUNT(events WHERE event_type = 'training_attended')
unique_training_types = COUNT(DISTINCT event_value_txt WHERE event_type = 'training_attended')
```

---

## 3. Churn Prediction Calculations

### 3.1 Machine Learning Model (Random Forest)

**Location:** `src/utils/churn_model.py`

#### Model Configuration:
```python
RandomForestClassifier(
    n_estimators=100,
    max_depth=10,
    min_samples_split=20,
    random_state=42,
    class_weight='balanced'
)
```

#### Features Used (29 total):

**Demographics:**
- account_age_days
- portfolio_size
- annual_revenue
- success_manager_assigned

**Usage Metrics:**
- active_days_30d, active_days_60d, active_days_90d
- logins_30d
- avg_session_30d
- total_events
- events_30d, events_60d
- days_since_last_activity

**Core Actions:**
- property_added_count
- tenant_added_count
- lease_signed_count
- payments_received
- report_generated_count

**Engagement:**
- unique_features
- trainings_attended

**Sentiment:**
- nps_score
- support_tickets_last_90d

**Health Scores:**
- health_score
- usage_component
- business_value_component
- sentiment_component
- engagement_component

**Plan Type (One-Hot Encoded):**
- plan_starter
- plan_pro
- plan_premium

**Derived Features:**
- engagement_declining = (events_30d < events_60d)

#### Target Variable:
```
churned = (is_active == 0)
```

#### Risk Tier Classification:
```
Churn Risk Tier:
- Low: churn_probability < 0.4
- Medium: 0.4 ≤ churn_probability < 0.7
- High: churn_probability ≥ 0.7
```

#### Model Evaluation Metrics:
- ROC-AUC Score
- Accuracy
- Precision, Recall, F1-Score
- Confusion Matrix
- Feature Importance Rankings

### 3.2 Rule-Based Churn Model (Simplified)

**Location:** `src/utils/churn_model_simple.py`

#### Risk Score Formula:
```
Risk Score = (Low Engagement Factor × 0.30) +
             (Low Usage Factor × 0.25) +
             (Declining Activity Factor × 0.20) +
             (Near Renewal Factor × 0.15) +
             (Low Feature Adoption Factor × 0.10)
```

#### Factor Calculations:

**Low Engagement (30%):**
```
Low Engagement = days_since_last_activity / max(days_since_last_activity)
```
- Normalized 0-1, higher = worse engagement

**Low Usage (25%):**
```
avg_events_per_day = total_events / account_age_days
Low Usage = 1 - (avg_events_per_day / max(avg_events_per_day))
```
- Normalized 0-1, higher = less usage

**Declining Activity (20%):**
```
activity_trend = (events_30d - events_60d) / max(1, events_60d)
Declining Activity = IF activity_trend < 0 THEN |activity_trend| × 0.2 ELSE 0
```
- Only penalizes declining trends

**Near Renewal (15%):**
```
Near Renewal = IF days_to_renewal < 30
               THEN (30 - days_to_renewal) / 30 × 0.15
               ELSE 0
```
- Higher risk as renewal approaches

**Low Feature Adoption (10%):**
```
Low Feature Adoption = 1 - (unique_events / max(unique_events))
```
- Normalized 0-1, higher = fewer features used

#### Final Calculation:
```
Churn Probability = CLIP(Risk Score, 0, 1)
```

#### Risk Tier Classification:
```
- Low: probability < 0.3
- Medium: 0.3 ≤ probability < 0.6
- High: probability ≥ 0.6
```

---

## 4. Retention & Cohort Analysis

**Location:** `src/utils/data_processor.py` (lines 304-336)

### 4.1 Cohort Definition

```
cohort_month = YEAR-MONTH of signup_date
```
- Users grouped by signup month

### 4.2 Cohort Retention Rate

```
months_since_signup = MONTHS_BETWEEN(activity_month, cohort_month)

cohort_size = COUNT(DISTINCT users WHERE cohort_month = X)
active_users_month_N = COUNT(DISTINCT users active in month N since signup)

retention_rate = (active_users_month_N / cohort_size) × 100
```

**Active Definition:**
```
active_in_month = user had at least 1 event during that month
```

### 4.3 Overall Churn Rate

```
total_users = COUNT(all users)
inactive_users = COUNT(users WHERE is_active = 0)

churn_rate = (inactive_users / total_users) × 100
```

---

## 5. Revenue Retention Metrics

**Location:** `src/utils/data_processor.py` (lines 338-430)

### 5.1 Monthly Recurring Revenue (MRR)

```
MRR = annual_revenue / 12
```

### 5.2 Gross Revenue Retention (GRR)

```
Starting MRR (for cohort) = SUM(MRR of all users who signed up in cohort month)
Current MRR (for cohort) = SUM(MRR of retained users from cohort, as of current month)
Churned MRR (for cohort) = SUM(MRR of churned users from cohort)

GRR = (Current MRR / Starting MRR) × 100
```

**Key Points:**
- GRR excludes expansion revenue
- Only includes retained customers' original MRR
- Value ≤ 100%

### 5.3 Net Revenue Retention (NRR)

```
NRR = (Current MRR / Starting MRR) × 100
```

**Note:** In this implementation, NRR = GRR as expansion/contraction MRR is not tracked separately.

### 5.4 Weighted Average GRR/NRR

```
Overall GRR = (SUM(Current MRR across all cohorts) /
               SUM(Starting MRR across all cohorts)) × 100

Overall NRR = (SUM(Current MRR across all cohorts) /
               SUM(Starting MRR across all cohorts)) × 100
```

### 5.5 Plan-Level Retention

```
Plan GRR = (Retained MRR for specific plan / Starting MRR for plan) × 100
Plan NRR = (Retained MRR for specific plan / Starting MRR for plan) × 100
```
- Calculated separately for Starter, Pro, Premium

---

## 6. Revenue Analytics

**Location:** `src/layouts/revenue_analytics.py`

### 6.1 ARR Aggregations

```
Total ARR by Plan = SUM(annual_revenue) GROUP BY plan_type
Average ARR by Plan = MEAN(annual_revenue) GROUP BY plan_type
User Count by Plan = COUNT(users) GROUP BY plan_type
```

### 6.2 Revenue at Risk

```
Revenue at Risk = SUM(annual_revenue WHERE health_tier IN ('Red', 'Yellow'))
```
- Total ARR from unhealthy accounts

### 6.3 Expansion Opportunity

```
Expansion ARR = SUM(annual_revenue WHERE health_tier = 'Green'
                                    AND plan_type IN ('starter', 'pro'))
```
- Healthy customers on lower-tier plans = upsell candidates

### 6.4 Revenue per Property

```
Revenue per Property = annual_revenue / MAX(portfolio_size, 1)
```
- Division by zero prevented with MAX(portfolio_size, 1)
- Measures unit economics

### 6.5 ARR Bucketing

```
ARR Buckets:
- <$1K: ARR < 1,000
- $1-5K: 1,000 ≤ ARR < 5,000
- $5-10K: 5,000 ≤ ARR < 10,000
- $10-25K: 10,000 ≤ ARR < 25,000
- $25-50K: 25,000 ≤ ARR < 50,000
- $50-100K: 50,000 ≤ ARR < 100,000
- >$100K: ARR ≥ 100,000
```

### 6.6 Revenue Distribution Metrics

```
Median ARR = 50th percentile of annual_revenue
Mean ARR = SUM(annual_revenue) / COUNT(users)
```

---

## 7. CSM Workload Calculations

**Location:** `src/layouts/csm_workload.py`

### 7.1 CSM Assignment Metrics

```
Accounts per CSM = COUNT(users) GROUP BY csm_id
Total ARR per CSM = SUM(annual_revenue) GROUP BY csm_id
Average Health Score per CSM = MEAN(health_score) GROUP BY csm_id
Average NPS per CSM = MEAN(nps_score) GROUP BY csm_id
```

### 7.2 At-Risk Account Tracking

```
Renewal Risk Count = SUM(at_renewal_risk) GROUP BY csm_id
Red Health Count = COUNT(users WHERE health_tier = 'Red') GROUP BY csm_id
Yellow Health Count = COUNT(users WHERE health_tier = 'Yellow') GROUP BY csm_id
```

### 7.3 Portfolio Mix by CSM

```
Account Mix = COUNT(users) GROUP BY csm_id, plan_type
ARR Mix = SUM(annual_revenue) GROUP BY csm_id, plan_type
```
- Shows distribution of Starter/Pro/Premium accounts per CSM

### 7.4 Unassigned High-Value Accounts

```
Median ARR = MEDIAN(annual_revenue)
High-Value No CSM = COUNT(users WHERE success_manager_assigned = 0
                                 AND annual_revenue > Median ARR)
```
- Identifies coverage gaps

### 7.5 CSM Efficiency Metrics

```
ARR per Account = (Total ARR per CSM) / (Accounts per CSM)
Health Score Variance = STDDEV(health_score) GROUP BY csm_id
```

---

## 8. Adoption & Engagement Metrics

**Location:** `src/layouts/adoption_engagement.py`

### 8.1 Feature Adoption Funnel

```
Step 1: Logged In Users = COUNT(users WHERE total_logins > 0)
Step 2: Added Property = COUNT(users WHERE property_added_count > 0)
Step 3: Added Tenant = COUNT(users WHERE tenant_added_count > 0)
Step 4: Signed Lease = COUNT(users WHERE lease_signed_count > 0)
Step 5: Received Payment = COUNT(users WHERE payments_received > 0)

Conversion Rate (Step N) = (Step N / Step 1) × 100
Drop-off Rate (Step N to N+1) = ((Step N - Step N+1) / Step N) × 100
```

### 8.2 Engagement by Recency

```
Active Last 7 Days = COUNT(users WHERE days_since_last_activity ≤ 7)
Active Last 30 Days = COUNT(users WHERE days_since_last_activity ≤ 30)
Active Last 90 Days = COUNT(users WHERE days_since_last_activity ≤ 90)
Inactive (>90 Days) = COUNT(users WHERE days_since_last_activity > 90)

Percentage Distribution = (Count in Bucket / Total Users) × 100
```

### 8.3 Average Activity Metrics

```
Avg Logins (30d) = MEAN(logins_30d)
Avg Session Length = MEAN(avg_session_30d)
Avg Events per User = MEAN(events_30d)
Avg Active Days = MEAN(active_days_30d)
```

### 8.4 Training Engagement

```
Training Attendees = COUNT(users WHERE trainings_attended > 0)
Avg Trainings per Attendee = MEAN(trainings_attended WHERE trainings_attended > 0)
Training Participation Rate = (Training Attendees / Total Users) × 100
```

### 8.5 Feature Depth

```
Avg Unique Features = MEAN(unique_features)
Feature Power Users = COUNT(users WHERE unique_features >= 5)
```

---

## 9. User Flow & Timeline Calculations

**Location:** `src/layouts/user_flow.py`

### 9.1 Event Statistics

```
Total Events = COUNT(events) [filtered by user/segment]
Unique Users = COUNT(DISTINCT user_id)
Average Events per User = Total Events / Unique Users
Unique Event Types = COUNT(DISTINCT event_type)
```

### 9.2 Date Range Calculation

```
First Event Date = MIN(event_ts)
Last Event Date = MAX(event_ts)
Date Range = Last Event Date - First Event Date (in days)
```

### 9.3 Daily Event Volume

```
Events per Day = COUNT(events) GROUP BY DATE(event_ts)
```

### 9.4 Journey Flow (Sankey Diagram)

```
For each user:
  Step 1: Extract first 3 events chronologically (ordered by event_ts)
  Step 2: Create transitions:
          - Event 1 → Event 2
          - Event 2 → Event 3

Flow Weight = COUNT(user journeys with same transition pattern)
```

**Example:**
```
User A: login → property_added → tenant_added
User B: login → property_added → lease_signed
User C: login → property_added → tenant_added

Flow Weights:
login → property_added: 3
property_added → tenant_added: 2
property_added → lease_signed: 1
```

### 9.5 Activity Patterns

**By Day of Week:**
```
Events by Day = COUNT(events) GROUP BY DAYNAME(event_ts)
Days: Monday, Tuesday, Wednesday, Thursday, Friday, Saturday, Sunday
```

**By Hour of Day:**
```
Events by Hour = COUNT(events) GROUP BY HOUR(event_ts)
Hours: 0-23 (24-hour format)
```

### 9.6 Lifecycle Metrics

```
Signups per Day = COUNT(users) GROUP BY DATE(signup_date)
Cancellations per Day = COUNT(events WHERE event_type = 'subscription_cancelled')
                        GROUP BY DATE(event_ts)
Net Growth = Signups - Cancellations (per day)
```

---

## 10. Statistical Aggregations

**Location:** Multiple files in `src/layouts/`

### 10.1 Summary Statistics

```
Total Users = COUNT(*)
Active Users = COUNT(* WHERE is_active = 1)
Inactive Users = COUNT(* WHERE is_active = 0)
Active Rate = (Active Users / Total Users) × 100

Total ARR = SUM(annual_revenue)
Average ARR = MEAN(annual_revenue)
Median ARR = 50th PERCENTILE(annual_revenue)

Average NPS = MEAN(nps_score)
Average Health Score = MEAN(health_score)
```

### 10.2 Distribution Counts

**Health Distribution:**
```
Red Count = COUNT(users WHERE health_tier = 'Red')
Yellow Count = COUNT(users WHERE health_tier = 'Yellow')
Green Count = COUNT(users WHERE health_tier = 'Green')

Percentages = (Count / Total Users) × 100
```

**Plan Distribution:**
```
Starter = COUNT(users WHERE plan_type = 'starter')
Pro = COUNT(users WHERE plan_type = 'pro')
Premium = COUNT(users WHERE plan_type = 'premium')

Percentages = (Count / Total Users) × 100
```

**Churn Risk Distribution:**
```
Low Risk = COUNT(users WHERE churn_risk_tier = 'Low')
Medium Risk = COUNT(users WHERE churn_risk_tier = 'Medium')
High Risk = COUNT(users WHERE churn_risk_tier = 'High')

Percentages = (Count / Total Users) × 100
```

### 10.3 Comparative Analysis (Churned vs Active)

```
Metric Comparison:
- Avg Health Score (Churned) = MEAN(health_score WHERE is_active = 0)
- Avg Health Score (Active) = MEAN(health_score WHERE is_active = 1)
- Difference = Active - Churned

- Avg NPS (Churned) = MEAN(nps_score WHERE is_active = 0)
- Avg NPS (Active) = MEAN(nps_score WHERE is_active = 1)
- Difference = Active - Churned

- Avg Logins (Churned) = MEAN(logins_30d WHERE is_active = 0)
- Avg Logins (Active) = MEAN(logins_30d WHERE is_active = 1)
- Difference = Active - Churned

- Avg Features (Churned) = MEAN(unique_features WHERE is_active = 0)
- Avg Features (Active) = MEAN(unique_features WHERE is_active = 1)
- Difference = Active - Churned

- Avg Support Tickets (Churned) = MEAN(support_tickets_last_90d WHERE is_active = 0)
- Avg Support Tickets (Active) = MEAN(support_tickets_last_90d WHERE is_active = 1)
- Difference = Churned - Active (higher is worse)
```

### 10.4 Percentile Analysis

```
ARR Percentiles:
- 25th Percentile (Q1) = 25th PERCENTILE(annual_revenue)
- 50th Percentile (Median) = 50th PERCENTILE(annual_revenue)
- 75th Percentile (Q3) = 75th PERCENTILE(annual_revenue)
- 90th Percentile = 90th PERCENTILE(annual_revenue)

Health Score Percentiles:
- 25th Percentile = 25th PERCENTILE(health_score)
- 50th Percentile = 50th PERCENTILE(health_score)
- 75th Percentile = 75th PERCENTILE(health_score)
```

---

## 11. Derived Fields & Transformations

### 11.1 Account Age

```
account_age_days = reference_date - signup_date (in days)
Reference Date: 2025-08-01

account_age_months = account_age_days / 30.44 (average days per month)
account_age_years = account_age_days / 365.25 (average days per year)
```

### 11.2 Days to Renewal

```
days_to_renewal = renewal_due_date - reference_date (in days)
Reference Date: 2025-08-01

Renewal Proximity:
- Immediate: days_to_renewal ≤ 30
- Near-term: 30 < days_to_renewal ≤ 90
- Mid-term: 90 < days_to_renewal ≤ 180
- Long-term: days_to_renewal > 180
```

### 11.3 Engagement Trend Indicators

```
engagement_declining = IF events_30d < events_60d THEN 1 ELSE 0

activity_trend = (events_30d - events_60d) / MAX(events_60d, 1)
Interpretation:
- Positive trend: Growing activity
- Negative trend: Declining activity
- Near zero: Stable activity
```

### 11.4 NPS Categorization

```
NPS Category:
- Detractors: nps_score < 0
- Passives: 0 ≤ nps_score ≤ 50
- Promoters: nps_score > 50

NPS Net Score = % Promoters - % Detractors
```

### 11.5 Usage Intensity Classification

```
Based on events_30d:
- Power User: events_30d >= 75th percentile
- Regular User: 25th percentile ≤ events_30d < 75th percentile
- Light User: events_30d < 25th percentile
```

### 11.6 Customer Lifetime Value (CLV) Proxy

```
CLV Proxy = annual_revenue × (1 / estimated_churn_rate)
Where estimated_churn_rate = churn_probability from ML model

Simplified:
Expected Lifetime Value = annual_revenue × (1 - churn_probability) × expected_lifetime_years
```

---

## 12. Reference Constants

### 12.1 Date References

```
Reference Date: 2025-08-01
```
- All time-based calculations use this as the "current date"
- Ensures consistency across dashboard loads
- Represents the data snapshot timestamp

### 12.2 Activity Thresholds

```
Active User Definition:
- Last activity within 90 days
- days_since_last_activity ≤ 90

Engagement Recency Thresholds:
- Recent: ≤ 7 days
- Active: 8-30 days
- At Risk: 31-90 days
- Inactive: > 90 days

High Churn Risk Thresholds:
- ML Model: churn_probability ≥ 0.7
- Rule-Based Model: churn_probability ≥ 0.6

Renewal Risk Definition:
- Within 90 days of renewal AND health_score < 60
```

### 12.3 Normalization Benchmarks

```
Usage Benchmarks:
- Max Logins: 20 per 30 days
- Max Session Length: 30 minutes
- Max Features Adopted: 5 unique features
- Max Trainings: 3 attended
- Max Reports: 10 generated
- Max Portfolio: 20 properties
```

### 12.4 Health Score Weights

```
Component Weights:
- Usage: 40%
  - Login: 15% of usage (6% of total)
  - Session: 10% of usage (4% of total)
  - Core Usage: 30% of usage (12% of total)
  - Adoption: 25% of usage (10% of total)
  - Recency: 20% of usage (8% of total)

- Business Value: 30%
  - ARR: 40% of business (12% of total)
  - Portfolio: 30% of business (9% of total)
  - Plan: 30% of business (9% of total)

- Sentiment: 20%
  - NPS: 60% of sentiment (12% of total)
  - Support: 40% of sentiment (8% of total)

- Engagement: 10%
  - Training: 30% of engagement (3% of total)
  - Reporting: 30% of engagement (3% of total)
  - Consistency: 40% of engagement (4% of total)
```

### 12.5 Plan Tier Values

```
Plan Scoring:
- Premium: 100 points
- Pro: 65 points
- Starter: 35 points

Relative Weights: 100:65:35 = 2.86:1.86:1
```

### 12.6 Data Handling Rules

```
Missing Data:
- All calculations use .fillna(0) for missing values
- Numeric fields default to 0
- String fields default to empty string

Division by Zero Prevention:
- .replace(0, 1) for denominators
- MAX(value, 1) for safety
- Conditional checks before division

Capping Rules:
- All scores capped at 100
- Health score range: [0, 100]
- Percentages capped at 100%
- CLIP functions used for probability bounds [0, 1]
```

---

## Technical Implementation Notes

### Data Processing Pipeline

```
Raw Data Sources
    ↓
CXDataProcessor.load_and_process()
    ↓
Feature Engineering (activity, usage, health metrics)
    ↓
Master Table (comprehensive user-level dataset)
    ↓
Caching (24-hour validity, pickle format)
    ↓
Dashboard Views (filtered, aggregated)
```

### Performance Optimizations

1. **Caching Strategy:**
   - Master table cached as pickle file
   - Cache validity: 24 hours
   - Refresh triggered if cache older than validity period

2. **Vectorized Operations:**
   - All calculations use pandas vectorized operations
   - No row-by-row iteration (loops avoided)
   - Numpy functions for mathematical operations

3. **Pre-Aggregated Statistics:**
   - Summary statistics computed once
   - Stored in summary_stats dictionary
   - Reused across multiple dashboard views

### Scaling & Standardization

**For Machine Learning:**
```
StandardScaler applied to all features:
- Mean = 0
- Standard Deviation = 1
- Formula: scaled_value = (value - mean) / std_dev
```

**For Display:**
```
- Health scores normalized to 0-100 range
- Percentages displayed with % symbol
- Currency formatted with $ and comma separators
- Dates formatted as YYYY-MM-DD
```

### Data Quality Checks

```
Validation Rules:
- Health score: 0 ≤ value ≤ 100
- Churn probability: 0 ≤ value ≤ 1
- NPS: -100 ≤ value ≤ 100
- Days since activity: value ≥ 0
- Event counts: value ≥ 0
- ARR: value ≥ 0
```

---

## File Location Quick Reference

| Calculation Area | File Path | Line Range |
|-----------------|-----------|------------|
| Health Score | `src/utils/data_processor.py` | 169-269 |
| Activity Metrics | `src/utils/data_processor.py` | 43-167 |
| Churn Model (ML) | `src/utils/churn_model.py` | Full file |
| Churn Model (Simple) | `src/utils/churn_model_simple.py` | Full file |
| Cohort Analysis | `src/utils/data_processor.py` | 304-336 |
| Revenue Retention | `src/utils/data_processor.py` | 338-430 |
| Revenue Analytics | `src/layouts/revenue_analytics.py` | Full file |
| CSM Workload | `src/layouts/csm_workload.py` | Full file |
| Adoption Metrics | `src/layouts/adoption_engagement.py` | Full file |
| User Flow | `src/layouts/user_flow.py` | Full file |
| Health Dashboard | `src/layouts/health_dashboard.py` | Full file |
| Churn Dashboard | `src/layouts/churn_prediction.py` | Full file |

---

## Glossary

**ARR:** Annual Recurring Revenue - Total contracted revenue per year

**Churn:** Customer attrition - when a user becomes inactive or cancels

**Cohort:** Group of users who signed up in the same time period

**CSM:** Customer Success Manager

**GRR:** Gross Revenue Retention - Revenue retained excluding expansion

**MRR:** Monthly Recurring Revenue - ARR divided by 12

**NPS:** Net Promoter Score - Customer satisfaction metric (-100 to 100)

**NRR:** Net Revenue Retention - Revenue retained including expansion/contraction

**Retention Rate:** Percentage of users/revenue retained over time

---

**End of Document**

For questions or clarifications about any calculation, refer to the specific file path and line numbers provided above.
