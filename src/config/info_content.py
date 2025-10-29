"""
Info Content Repository
Centralized storage for all code snippets, SQL queries, and formula explanations
used in the dashboard information icons.
"""

INFO_CONTENT = {
    # KPI Cards
    "total_arr": {
        "tooltip": "Total Annual Recurring Revenue across all active accounts",
        "title": "Total ARR Calculation",
        "formula": """
### Total Annual Recurring Revenue (ARR)

**Definition:** The sum of all annual recurring revenue across all users in the system.

**Formula:**
```
Total ARR = SUM(annual_revenue)
Avg ARR = MEAN(annual_revenue)
```

**Purpose:** Measures the total predictable revenue stream from all active subscriptions. This is a key financial metric for SaaS businesses.

**Business Impact:** Primary indicator of company revenue health and growth trajectory.
        """,
        "python_code": """# From: src/utils/load_data.py (lines 104-109)

def get_summary_stats(self) -> dict:
    df = self.master_df

    return {
        'total_arr': df['annual_revenue'].sum(),
        'avg_arr': df['annual_revenue'].mean(),
        # ... other metrics
    }""",
        "sql_code": """-- Total ARR Calculation

SELECT
    SUM(annual_revenue) as total_arr,
    AVG(annual_revenue) as avg_arr,
    COUNT(*) as total_users
FROM user_metrics_view;"""
    },

    "active_users": {
        "tooltip": "Number of users with activity in the last 90 days",
        "title": "Active Users Calculation",
        "formula": """
### Active Users

**Definition:** Users who have logged in or performed any activity within the last 90 days.

**Formula:**
```
Active Users = COUNT(users WHERE is_active = 1)
Total Users = COUNT(all users)
```

**Activity Criteria:**
- At least one login in the past 90 days
- Days since last activity ≤ 90

**Purpose:** Measures user engagement and platform adoption. High active user percentage indicates healthy product usage.
        """,
        "python_code": """# From: src/utils/load_data.py (lines 104-107)

def get_summary_stats(self) -> dict:
    df = self.master_df

    return {
        'active_users': df[df['is_active'] == 1].shape[0],
        'total_users': len(df),
        # ... other metrics
    }

# Activity flag is set in data_processor.py based on:
# - days_since_last_activity <= 90""",
        "sql_code": """-- Active Users Calculation

SELECT
    COUNT(CASE WHEN is_active = 1 THEN 1 END) as active_users,
    COUNT(*) as total_users,
    ROUND(100.0 * COUNT(CASE WHEN is_active = 1 THEN 1 END) / COUNT(*), 2) as active_percentage
FROM user_metrics_view
WHERE days_since_last_activity <= 90;"""
    },

    "churn_rate": {
        "tooltip": "Percentage of users with no activity in the last 90 days",
        "title": "Churn Rate Calculation",
        "formula": """
### Churn Rate

**Definition:** The percentage of users who have become inactive (no activity in 90+ days).

**Formula:**
```
Inactive Users = COUNT(users WHERE is_active = 0)
Churn Rate = (Inactive Users / Total Users) × 100
```

**Churn Criteria:**
- No activity in the past 90 days
- is_active = 0

**Purpose:** Measures customer attrition. Lower churn rate indicates better customer retention and product stickiness.

**Industry Benchmark:** SaaS companies typically aim for <5% monthly churn or <20% annual churn.
        """,
        "python_code": """# From: src/layouts/executive_overview.py (lines 45-46)

def create_executive_overview(data_loader):
    stats = data_loader.get_summary_stats()

    # Calculate churn rate
    churn_rate = (stats['inactive_users'] / stats['total_users']) * 100

# Inactive users count from: src/utils/load_data.py
def get_summary_stats(self) -> dict:
    return {
        'inactive_users': df[df['is_active'] == 0].shape[0],
        # ...
    }""",
        "sql_code": """-- Churn Rate Calculation

SELECT
    COUNT(CASE WHEN is_active = 0 THEN 1 END) as inactive_users,
    COUNT(*) as total_users,
    ROUND(100.0 * COUNT(CASE WHEN is_active = 0 THEN 1 END) / COUNT(*), 2) as churn_rate_percentage
FROM user_metrics_view;"""
    },

    "avg_nps": {
        "tooltip": "Average Net Promoter Score across all customers (-100 to +100)",
        "title": "Average NPS Calculation",
        "formula": """
### Average Net Promoter Score (NPS)

**Definition:** The average NPS score across all customers, measuring overall customer satisfaction and loyalty.

**Formula:**
```
Avg NPS = MEAN(nps_score)
```

**NPS Scale:**
- **-100 to -1:** Negative sentiment (more detractors than promoters)
- **0 to +30:** Neutral (mixed sentiment)
- **+30 to +70:** Good (healthy customer base)
- **+70 to +100:** Excellent (exceptional customer loyalty)

**NPS Categories:**
- **Promoters (9-10):** Loyal enthusiasts who will refer others
- **Passives (7-8):** Satisfied but unenthusiastic customers
- **Detractors (0-6):** Unhappy customers who may damage brand through negative word-of-mouth

**Purpose:** Key indicator of customer satisfaction and likelihood to recommend your product.
        """,
        "python_code": """# From: src/utils/load_data.py (lines 110)

def get_summary_stats(self) -> dict:
    df = self.master_df

    return {
        'avg_nps': df['nps_score'].mean(),
        # ... other metrics
    }""",
        "sql_code": """-- Average NPS Calculation

SELECT
    AVG(nps_score) as avg_nps,
    MIN(nps_score) as min_nps,
    MAX(nps_score) as max_nps,
    COUNT(*) as total_responses,
    -- NPS Category Distribution
    COUNT(CASE WHEN nps_score >= 9 THEN 1 END) as promoters,
    COUNT(CASE WHEN nps_score BETWEEN 7 AND 8 THEN 1 END) as passives,
    COUNT(CASE WHEN nps_score <= 6 THEN 1 END) as detractors
FROM user_metrics_view;"""
    },

    # Charts
    "health_distribution": {
        "tooltip": "Distribution of customers by health score tier (Red: <60, Yellow: 60-80, Green: >80)",
        "title": "Customer Health Distribution",
        "formula": """
### Customer Health Score Distribution

**Definition:** Segmentation of customers into health tiers based on their composite health score.

**Health Tiers:**
- 🔴 **Red (At-Risk):** Health Score < 60
  - High churn risk, requires immediate attention
  - Low usage, engagement, or satisfaction

- 🟡 **Yellow (Stable):** Health Score 60-80
  - Moderate health, monitor closely
  - Opportunities for improvement

- 🟢 **Green (Healthy):** Health Score > 80
  - Strong engagement and satisfaction
  - Ideal customer state

**Health Score Components:**
1. **Usage (40%):** Login frequency, session quality, feature adoption
2. **Business Value (30%):** ARR, portfolio size, plan tier
3. **Sentiment (20%):** NPS score, support ticket volume
4. **Engagement (10%):** Training completion, reporting usage

**Purpose:** Provides a quick snapshot of overall customer health distribution for strategic planning.
        """,
        "python_code": """# From: src/utils/load_data.py (lines 111)
# And src/utils/data_processor.py (lines 253-258)

def get_summary_stats(self) -> dict:
    df = self.master_df
    return {
        'health_distribution': df['health_tier'].value_counts().to_dict(),
        # ... other metrics
    }

# Health tier assignment from data_processor.py:
def calculate_health_scores(self, user_metrics: pd.DataFrame):
    # ... health score calculation ...

    # Health Tier
    df['health_tier'] = pd.cut(df['health_score'],
                               bins=[-0.01, 60, 80, 100.01],
                               labels=['Red', 'Yellow', 'Green'])

    return df""",
        "sql_code": """-- Customer Health Distribution

WITH health_tiers AS (
    SELECT
        user_id,
        health_score,
        CASE
            WHEN health_score < 60 THEN 'Red'
            WHEN health_score BETWEEN 60 AND 80 THEN 'Yellow'
            WHEN health_score > 80 THEN 'Green'
        END as health_tier
    FROM user_health_scores
)
SELECT
    health_tier,
    COUNT(*) as customer_count,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 2) as percentage
FROM health_tiers
GROUP BY health_tier
ORDER BY health_tier;"""
    },

    "churn_risk_distribution": {
        "tooltip": "Distribution of customers by churn risk level (Low, Medium, High)",
        "title": "Churn Risk Distribution",
        "formula": """
### Churn Risk Distribution

**Definition:** Segmentation of customers by their predicted churn risk level.

**Churn Risk Tiers:**
- 🔴 **High Risk:** Health score < 60 AND/OR days to renewal < 30
  - Immediate intervention required
  - High probability of cancellation

- 🟡 **Medium Risk:** Health score 60-80 OR days to renewal 30-90
  - Monitor closely
  - Proactive engagement recommended

- 🟢 **Low Risk:** Health score > 80 AND days to renewal > 90
  - Stable, engaged customers
  - Focus on upsell opportunities

**Purpose:** Prioritize customer success efforts and resource allocation.
        """,
        "python_code": """# From: src/utils/data_processor.py

def calculate_churn_risk(self, df: pd.DataFrame) -> pd.DataFrame:
    # Churn risk logic based on health score and renewal timing

    conditions = [
        (df['health_score'] < 60) | (df['days_to_renewal'] < 30),
        ((df['health_score'] >= 60) & (df['health_score'] < 80)) |
        ((df['days_to_renewal'] >= 30) & (df['days_to_renewal'] < 90)),
    ]
    choices = ['High', 'Medium']
    df['churn_risk_tier'] = np.select(conditions, choices, default='Low')

    return df""",
        "sql_code": """-- Churn Risk Distribution

SELECT
    CASE
        WHEN health_score < 60 OR days_to_renewal < 30 THEN 'High'
        WHEN (health_score BETWEEN 60 AND 80) OR (days_to_renewal BETWEEN 30 AND 90) THEN 'Medium'
        ELSE 'Low'
    END as churn_risk_tier,
    COUNT(*) as customer_count,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 2) as percentage
FROM user_metrics_view
GROUP BY churn_risk_tier
ORDER BY churn_risk_tier;"""
    },

    "users_by_plan": {
        "tooltip": "Number of customers on each subscription plan tier",
        "title": "Users by Plan Type",
        "formula": """
### Users by Plan Type

**Definition:** Distribution of customers across different subscription tiers.

**Plan Types:**
- **Starter:** Entry-level plan, basic features
- **Pro:** Mid-tier plan, advanced features
- **Premium:** Enterprise plan, full feature set

**Purpose:**
- Understand product mix and revenue distribution
- Identify upsell opportunities
- Track tier migration patterns

**Business Impact:**
- Higher-tier plans typically have better retention and higher LTV
- Balance between acquisition (starter) and revenue (premium)
        """,
        "python_code": """# From: src/utils/load_data.py (lines 112)
# And src/layouts/executive_overview.py (lines 96-106)

def get_summary_stats(self) -> dict:
    df = self.master_df
    return {
        'plan_distribution': df['plan_type'].value_counts().to_dict(),
        # ... other metrics
    }

# Visualization code:
plan_data = pd.DataFrame.from_dict(stats['plan_distribution'], orient='index', columns=['count'])
plan_fig = px.bar(
    plan_data,
    x=plan_data.index,
    y='count',
    title='Users by Plan Type',
    color=plan_data.index,
    color_discrete_map={'starter': '#3498DB', 'pro': '#9B59B6', 'premium': '#E67E22'}
)""",
        "sql_code": """-- Users by Plan Type

SELECT
    plan_type,
    COUNT(*) as user_count,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 2) as percentage_of_users,
    SUM(annual_revenue) as total_arr_by_plan,
    AVG(annual_revenue) as avg_arr_by_plan
FROM user_metrics_view
GROUP BY plan_type
ORDER BY
    CASE plan_type
        WHEN 'premium' THEN 1
        WHEN 'pro' THEN 2
        WHEN 'starter' THEN 3
    END;"""
    },

    "arr_by_plan": {
        "tooltip": "Total Annual Recurring Revenue broken down by subscription plan",
        "title": "ARR by Plan Type",
        "formula": """
### ARR by Plan Type

**Definition:** Total annual recurring revenue segmented by subscription tier.

**Formula:**
```
ARR by Plan = SUM(annual_revenue) GROUP BY plan_type
```

**Purpose:**
- Identify which tiers drive the most revenue
- Evaluate pricing strategy effectiveness
- Forecast revenue impact of tier migrations

**Analysis Insights:**
- Premium plans typically contribute 60-80% of total ARR
- Pro plans provide steady mid-market revenue
- Starter plans drive customer acquisition with upsell potential
        """,
        "python_code": """# From: src/layouts/executive_overview.py (lines 108-119)

def create_executive_overview(data_loader):
    df = data_loader.get_master_data()

    # ARR by plan type
    arr_by_plan = df.groupby('plan_type')['annual_revenue'].sum().reset_index()
    arr_fig = px.bar(
        arr_by_plan,
        x='plan_type',
        y='annual_revenue',
        title='ARR by Plan Type',
        color='plan_type',
        color_discrete_map={'starter': '#3498DB', 'pro': '#9B59B6', 'premium': '#E67E22'}
    )
    arr_fig.update_yaxes(tickprefix='$', tickformat=',.0f')""",
        "sql_code": """-- ARR by Plan Type

SELECT
    plan_type,
    SUM(annual_revenue) as total_arr,
    COUNT(*) as user_count,
    AVG(annual_revenue) as avg_arr,
    MIN(annual_revenue) as min_arr,
    MAX(annual_revenue) as max_arr
FROM user_metrics_view
GROUP BY plan_type
ORDER BY total_arr DESC;"""
    },

    "nps_distribution": {
        "tooltip": "Histogram showing the distribution of NPS scores across all customers",
        "title": "NPS Score Distribution",
        "formula": """
### NPS Score Distribution

**Definition:** Frequency distribution of Net Promoter Scores across the customer base.

**NPS Scoring:**
- Score range: -100 to +100
- Based on: "How likely are you to recommend our product?" (0-10 scale)

**Distribution Analysis:**
- **Left-skewed:** More detractors than promoters (concerning)
- **Right-skewed:** More promoters than detractors (healthy)
- **Bimodal:** Mixed population, requires segmentation analysis

**Purpose:**
- Identify concentration of sentiment
- Spot outliers and anomalies
- Track changes in customer satisfaction over time

**Action Items:**
- Scores < 0: Focus on reducing detractors
- Scores 0-30: Balance retention and improvement
- Scores > 30: Leverage promoters for referrals
        """,
        "python_code": """# From: src/layouts/executive_overview.py (lines 121-134)

def create_executive_overview(data_loader):
    df = data_loader.get_master_data()

    # NPS distribution
    nps_fig = go.Figure()
    nps_fig.add_trace(go.Histogram(
        x=df['nps_score'],
        nbinsx=20,  # 20 bins for granular view
        marker_color='#4A90E2',
        name='NPS Distribution'
    ))
    nps_fig.update_layout(
        title='NPS Score Distribution',
        xaxis_title='NPS Score',
        yaxis_title='Number of Users',
        showlegend=False
    )""",
        "sql_code": """-- NPS Score Distribution

SELECT
    FLOOR(nps_score / 10) * 10 as nps_bucket,
    COUNT(*) as customer_count,
    AVG(nps_score) as avg_nps_in_bucket,
    -- Categorization
    CASE
        WHEN nps_score >= 9 THEN 'Promoter'
        WHEN nps_score >= 7 THEN 'Passive'
        ELSE 'Detractor'
    END as nps_category
FROM user_metrics_view
GROUP BY nps_bucket, nps_category
ORDER BY nps_bucket;"""
    },

    "at_risk_table": {
        "tooltip": "Top 10 highest-value accounts at risk of churn (renewal < 90 days AND health score < 60)",
        "title": "At-Risk Accounts Calculation",
        "formula": """
### At-Risk Accounts

**Definition:** Customers who are both approaching renewal and showing signs of poor health.

**Risk Criteria:**
```
at_renewal_risk = (days_to_renewal <= 90) AND (health_score < 60)
```

**Why Both Conditions Matter:**
1. **Days to Renewal ≤ 90:** Limited time window to intervene before decision point
2. **Health Score < 60:** Indicates disengagement, low usage, or dissatisfaction

**Table Columns:**
- **user_id:** Unique customer identifier
- **plan_type:** Subscription tier (premium = highest priority)
- **annual_revenue:** ARR contribution (sorted by this descending)
- **health_score:** Composite health metric (0-100)
- **days_to_renewal:** Days until contract renewal decision
- **nps_score:** Customer satisfaction indicator

**Purpose:**
- Prioritize customer success interventions
- Focus on highest-value at-risk accounts first
- Proactive outreach before churn occurs

**Action Playbook:**
1. Premium accounts: Immediate executive engagement
2. Pro accounts: CSM intervention within 48 hours
3. Starter accounts: Automated intervention + monitoring
        """,
        "python_code": """# From: src/utils/data_processor.py (lines 260-264)

def calculate_health_scores(self, user_metrics: pd.DataFrame) -> pd.DataFrame:
    df = user_metrics.copy()

    # ... health score calculation ...

    # Renewal Risk
    df['at_renewal_risk'] = (
        (df['days_to_renewal'] <= 90) &
        (df['health_score'] < 60)
    ).astype(int)

    return df

# From: src/layouts/executive_overview.py (lines 136-146)
def create_executive_overview(data_loader):
    df = data_loader.get_master_data()

    # At-risk accounts table - sorted by ARR descending
    at_risk = df[df['at_renewal_risk'] == 1].sort_values('annual_revenue', ascending=False).head(10)
    at_risk_table = dbc.Table.from_dataframe(
        at_risk[['user_id', 'plan_type', 'annual_revenue', 'health_score',
                'days_to_renewal', 'nps_score']].round(2),
        striped=True,
        bordered=True,
        hover=True
    )""",
        "sql_code": """-- At-Risk Accounts

SELECT
    user_id,
    plan_type,
    annual_revenue,
    health_score,
    days_to_renewal,
    nps_score,
    -- Additional context
    health_tier,
    churn_risk_tier,
    is_active
FROM user_metrics_view
WHERE days_to_renewal <= 90
  AND health_score < 60
ORDER BY annual_revenue DESC
LIMIT 10;

-- Alternative: Weighted priority score
SELECT
    user_id,
    plan_type,
    annual_revenue,
    health_score,
    days_to_renewal,
    nps_score,
    -- Priority score: combines ARR and urgency
    (annual_revenue / 1000) * (90 - days_to_renewal) / 90 as priority_score
FROM user_metrics_view
WHERE days_to_renewal <= 90
  AND health_score < 60
ORDER BY priority_score DESC
LIMIT 10;"""
    },

    "health_score_formula": {
        "tooltip": "Complete health score calculation methodology",
        "title": "Health Score Formula - Complete Breakdown",
        "formula": """
### Composite Health Score Formula

**Overall Formula:**
```
Health Score = (Usage × 0.40) + (Business Value × 0.30) + (Sentiment × 0.20) + (Engagement × 0.10)
```

---

## Component 1: Usage Score (40% weight)

**Sub-components:**
- **Login Score (15%):** `min(100, (logins_30d / 20) × 100)`
- **Session Score (10%):** `min(100, (avg_session_30d / 30) × 100)`
- **Core Usage Score (30%):**
  - 0-1 actions: 25 points
  - 1-5 actions: 50 points
  - 5-10 actions: 75 points
  - 10+ actions: 100 points
- **Adoption Score (25%):** `min(100, (unique_features / 5) × 100)`
- **Recency Score (20%):**
  - ≤ 7 days: 100 points
  - ≤ 14 days: 80 points
  - ≤ 30 days: 60 points
  - ≤ 60 days: 40 points
  - ≤ 90 days: 20 points
  - > 90 days: 0 points

```
usage_component = (login_score × 0.15) + (session_score × 0.10) +
                  (core_usage_score × 0.30) + (adoption_score × 0.25) +
                  (recency_score × 0.20)
```

---

## Component 2: Business Value Score (30% weight)

**Sub-components:**
- **ARR Score (40%):** `(annual_revenue / max_arr) × 100`
- **Portfolio Score (30%):** `min(100, (portfolio_size / 20) × 100)`
- **Plan Score (30%):**
  - Premium: 100 points
  - Pro: 65 points
  - Starter: 35 points

```
business_value_component = (arr_score × 0.40) + (portfolio_score × 0.30) +
                           (plan_score × 0.30)
```

---

## Component 3: Sentiment Score (20% weight)

**Sub-components:**
- **NPS Normalized (60%):** `(nps_score + 100) / 2`
  - Converts -100 to +100 scale into 0-100 scale
- **Support Health (40%):**
  - 0 tickets: 100 points
  - ≤ 2 tickets: 80 points
  - ≤ 5 tickets: 60 points
  - ≤ 10 tickets: 40 points
  - ≤ 20 tickets: 20 points
  - > 20 tickets: 0 points

```
sentiment_component = (nps_normalized × 0.60) + (support_health × 0.40)
```

---

## Component 4: Engagement Score (10% weight)

**Sub-components:**
- **Training Score (30%):** `min(100, (trainings_attended / 3) × 100)`
- **Reporting Score (30%):** `min(100, (reports_generated / 10) × 100)`
- **Consistency Score (40%):** `(active_days_30d / 30) × 100`

```
engagement_component = (training_score × 0.30) + (reporting_score × 0.30) +
                       (consistency_score × 0.40)
```

---

## Final Calculation

```
health_score = (usage_component × 0.40) +
               (business_value_component × 0.30) +
               (sentiment_component × 0.20) +
               (engagement_component × 0.10)

# Ensure bounds
health_score = clip(health_score, 0, 100)
```

**Result Range:** 0-100 (higher is healthier)
        """,
        "python_code": """# From: src/utils/data_processor.py (lines 166-266)

def calculate_health_scores(self, user_metrics: pd.DataFrame) -> pd.DataFrame:
    df = user_metrics.copy()

    # Usage Score (0-100) - 40% weight
    df['login_score'] = np.minimum(100, (df.get('logins_30d', 0) / 20) * 100)
    df['session_score'] = np.minimum(100, (df.get('avg_session_30d', 0) / 30) * 100)

    core_actions = (df.get('property_added_count', 0) +
                   df.get('tenant_added_count', 0) +
                   df.get('lease_signed_count', 0))
    df['core_usage_score'] = pd.cut(core_actions, bins=[-1, 0, 1, 5, 10, np.inf],
                                    labels=[0, 25, 50, 75, 100]).astype(float)

    df['adoption_score'] = np.minimum(100, (df.get('unique_features', 0) / 5) * 100)

    recency_bins = [-1, 7, 14, 30, 60, 90, np.inf]
    recency_labels = [100, 80, 60, 40, 20, 0]
    df['recency_score'] = pd.cut(df.get('days_since_last_activity', 999),
                                 bins=recency_bins, labels=recency_labels).astype(float)

    df['usage_component'] = (
        df['login_score'] * 0.15 +
        df['session_score'] * 0.10 +
        df['core_usage_score'] * 0.30 +
        df['adoption_score'] * 0.25 +
        df['recency_score'] * 0.20
    )

    # Business Value Score (0-100) - 30% weight
    max_arr = df['annual_revenue'].max() if df['annual_revenue'].max() > 0 else 1
    df['arr_score'] = (df['annual_revenue'] / max_arr) * 100
    df['portfolio_score'] = np.minimum(100, (df['portfolio_size'] / 20) * 100)
    df['plan_score'] = df['plan_type'].map({
        'premium': 100, 'pro': 65, 'starter': 35
    }).fillna(0)

    df['business_value_component'] = (
        df['arr_score'] * 0.40 +
        df['portfolio_score'] * 0.30 +
        df['plan_score'] * 0.30
    )

    # Sentiment Score (0-100) - 20% weight
    df['nps_normalized'] = (df['nps_score'] + 100) / 2

    support_bins = [-1, 0, 2, 5, 10, 20, np.inf]
    support_labels = [100, 80, 60, 40, 20, 0]
    df['support_health'] = pd.cut(df['support_tickets_last_90d'],
                                  bins=support_bins, labels=support_labels).astype(float)

    df['sentiment_component'] = (
        df['nps_normalized'] * 0.60 +
        df['support_health'] * 0.40
    )

    # Engagement Score (0-100) - 10% weight
    df['training_score'] = np.minimum(100, (df.get('trainings_attended', 0) / 3) * 100)
    df['reporting_score'] = np.minimum(100, (df.get('report_generated_count', 0) / 10) * 100)
    df['consistency_score'] = (df.get('active_days_30d', 0) / 30) * 100

    df['engagement_component'] = (
        df['training_score'] * 0.30 +
        df['reporting_score'] * 0.30 +
        df['consistency_score'] * 0.40
    )

    # Overall Health Score
    df['health_score'] = (
        df['usage_component'] * 0.40 +
        df['business_value_component'] * 0.30 +
        df['sentiment_component'] * 0.20 +
        df['engagement_component'] * 0.10
    )

    # Ensure health score is within bounds and handle NaN
    df['health_score'] = df['health_score'].fillna(0).clip(0, 100)

    # Health Tier
    df['health_tier'] = pd.cut(df['health_score'],
                               bins=[-0.01, 60, 80, 100.01],
                               labels=['Red', 'Yellow', 'Green'])

    return df""",
        "sql_code": """-- From: sql/metrics/health_score.sql

WITH usage_score AS (
    SELECT
        user_id,
        LEAST(100, (logins_30d / 20.0) * 100) as login_score,
        LEAST(100, (avg_session_length_30d / 30.0) * 100) as session_score,
        CASE
            WHEN (properties_added + tenants_added + leases_signed) >= 10 THEN 100
            WHEN (properties_added + tenants_added + leases_signed) >= 5 THEN 75
            WHEN (properties_added + tenants_added + leases_signed) >= 1 THEN 50
            ELSE 25
        END as core_usage_score,
        LEAST(100, (unique_features_adopted / 5.0) * 100) as adoption_score,
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
        (annual_revenue / NULLIF((SELECT MAX(annual_revenue) FROM user_metrics), 0)) * 100 as arr_score,
        LEAST(100, (portfolio_size / 20.0) * 100) as portfolio_score,
        CASE plan_type
            WHEN 'premium' THEN 100
            WHEN 'pro' THEN 65
            WHEN 'starter' THEN 35
            ELSE 0
        END as plan_score
    FROM user_metrics
),

sentiment_score AS (
    SELECT
        user_id,
        ((nps_score + 100) / 2.0) as nps_normalized,
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
        LEAST(100, (trainings_attended / 3.0) * 100) as training_score,
        LEAST(100, (reports_generated / 10.0) * 100) as reporting_score,
        (active_days_in_month / 30.0) * 100 as consistency_score
    FROM user_metrics
),

component_scores AS (
    SELECT
        u.user_id,
        -- Usage Component (40%)
        (us.login_score * 0.15 +
         us.session_score * 0.10 +
         us.core_usage_score * 0.30 +
         us.adoption_score * 0.25 +
         us.recency_score * 0.20) as usage_component,

        -- Business Value Component (30%)
        (bv.arr_score * 0.40 +
         bv.portfolio_score * 0.30 +
         bv.plan_score * 0.30) as business_value_component,

        -- Sentiment Component (20%)
        (s.nps_normalized * 0.60 +
         s.support_health_score * 0.40) as sentiment_component,

        -- Engagement Component (10%)
        (e.training_score * 0.30 +
         e.reporting_score * 0.30 +
         e.consistency_score * 0.40) as engagement_component
    FROM user_metrics u
    LEFT JOIN usage_score us ON u.user_id = us.user_id
    LEFT JOIN business_value_score bv ON u.user_id = bv.user_id
    LEFT JOIN sentiment_score s ON u.user_id = s.user_id
    LEFT JOIN engagement_score e ON u.user_id = e.user_id
)

SELECT
    user_id,
    -- Final Health Score
    LEAST(100, GREATEST(0,
        usage_component * 0.40 +
        business_value_component * 0.30 +
        sentiment_component * 0.20 +
        engagement_component * 0.10
    )) as health_score,
    -- Health Tier
    CASE
        WHEN (usage_component * 0.40 + business_value_component * 0.30 +
              sentiment_component * 0.20 + engagement_component * 0.10) < 60 THEN 'Red'
        WHEN (usage_component * 0.40 + business_value_component * 0.30 +
              sentiment_component * 0.20 + engagement_component * 0.10) < 80 THEN 'Yellow'
        ELSE 'Green'
    END as health_tier
FROM component_scores;"""
    }
}
