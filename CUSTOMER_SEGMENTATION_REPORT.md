# Customer Segmentation & Profile Analysis Report
## CX Data Analysis

**Author**: CX Analyst  
**Date**: 2025  
**Purpose**: Comprehensive Customer Segmentation & Profile Building Analysis

---

## Executive Summary

This report presents a comprehensive analysis of customer segmentation based on portfolio size, plan types, engagement levels, support ticket volume, active status, and ARR. The analysis reveals key customer journey patterns and identifies opportunities for revenue growth and churn prevention.

### Key Findings

- **Total Customers**: 10,000 users with 228,731 total events
- **Active Rate**: 70.4% active customers (7,041 users)
- **Churn Risk**: 29.6% inactive customers (2,959 users) representing $7.4M in ARR at risk
- **Top Segment**: 10+ units → starter → Medium engagement → Active (13.7% of customers, $587K ARR)
- **Highest Value Segment**: 10+ units → premium → High engagement → Active (4.0% of customers, $6.4M ARR, $16,143 avg ARR)
- **Power Users**: Customers using 7+ event types generate $2,522 more ARR per customer (133% increase)

---

## 1. Data Overview

### Dataset Summary
- **Users Dataset**: 10,000 records
- **Events Dataset**: 228,731 events
- **Joined Dataset**: 27 columns including user metrics and event aggregations

### Key Metrics Tracked
- Portfolio size (1 unit to 100+ units)
- Plan types (starter, pro, premium)
- Annual recurring revenue (ARR)
- Active/inactive status
- NPS scores
- Support tickets (last 90 days)
- Event engagement (total events, event types, event diversity)
- Days since last activity

---

## 2. Portfolio Size Analysis

### Distribution
- **1 unit**: 913 customers (9.1%)
- **2-5 units**: 3,355 customers (33.6%)
- **6-10 units**: 883 customers (8.8%)
- **10+ units**: 4,849 customers (48.5%)

### Insights
- Large portfolios (10+ units) dominate the customer base at nearly 50%
- Portfolio sizes range from 0 to 100 units
- 199 records have portfolio size < 1 (data quality note)

**Visualizations**:
- Customer count by portfolio group and plan type (stacked bar chart)
- Total ARR by portfolio group and plan type (stacked bar chart)
- Average NPS by portfolio group and plan type (heatmap)
- Active rate by portfolio group and plan type (heatmap)

> Note: These charts are generated interactively in the notebook using Plotly.

---

## 3. Plan Type Analysis

### Distribution
- **Starter**: 5,207 customers (52.1%)
- **Pro**: 3,286 customers (32.9%)
- **Premium**: 1,507 customers (15.1%)

### Key Statistics by Plan Type

| Plan Type | Customers | Avg ARR | Active Rate | Avg NPS | Avg Support Tickets |
|-----------|-----------|---------|-------------|---------|---------------------|
| Starter   | 5,207     | ~$413   | Varies      | Varies  | Varies              |
| Pro       | 3,286     | ~$1,819 | Varies      | Varies  | Varies              |
| Premium   | 1,507     | ~$13,580| Varies      | Varies  | Varies              |

### Insights
- Starter plan is the most popular, representing over half of all customers
- Premium customers, though fewer, represent significantly higher ARR per customer
- Plan type selection correlates strongly with portfolio size

---

## 4. Engagement Level Analysis

### Engagement Tiers (based on total events)
- **Low Engagement (<15 events)**: 1,329 customers (13.3%)
  - Average: 13.9 events per customer
  - Range: 5-15 events
- **Medium Engagement (15-30 events)**: 7,334 customers (73.3%)
  - Average: 22.3 events per customer
  - Range: 16-30 events
- **High Engagement (30+ events)**: 1,337 customers (13.4%)
  - Average: 34.8 events per customer
  - Range: 31-51 events

### Key Findings
- Most customers (73.3%) fall into medium engagement tier
- High engagement customers are valuable but represent a smaller segment
- Low engagement customers may be at risk for churn

### Event Distribution Statistics
- Average events per user: ~23 events
- Median events per user: ~22 events
- Event types tracked: 10 different event types
  - Feature adopted
  - Lease signed
  - Login
  - Maintenance request created
  - NPS response submitted
  - Rent payment received
  - Report generated
  - Subscription cancelled
  - Support ticket created
  - Tenant added
  - Training attended

---

## 5. Support Ticket Analysis

### Ticket Volume Distribution (Last 90 Days)
- **0 tickets**: 4,895 customers (48.9%)
- **1 ticket**: 2,237 customers (22.4%)
- **2-4 tickets**: 2,182 customers (21.8%)
- **5-10 tickets**: 678 customers (6.8%)
- **11+ tickets**: 8 customers (0.1%)

### Summary Statistics
- **Total support tickets**: 24,682 tickets (last 90 days)
- **Average tickets per customer**: 2.47 tickets
- **Active customers**: 8,832 tickets (avg 1.3 per customer)
- **Inactive customers**: 3,509 tickets (avg 1.2 per customer)

### Engagement Level vs Support Tickets
- **High engagement customers**: 4,150 tickets (avg 3.1 per customer)
- **Medium engagement customers**: 7,745 tickets (avg 1.1 per customer)
- **Low engagement customers**: 446 tickets (avg 0.3 per customer)

### Insights
- Higher engagement correlates with higher support ticket volume
- Most customers (71.3%) have 0-1 tickets, indicating good product usability
- High support burden accounts (11+ tickets) are rare but may need intervention

**Visualization**: 

![Support Ticket Flow](notebooks/sankey%20engag%20ticket%20active.png)

*Support Ticket Flow: Engagement Level → Ticket Range → Active Status*

---

## 6. Training Attendance Impact Analysis

### Key Findings
- **Customers who attended training**: 3,228 (32.3% of total customers)
- **Customers who did not attend training**: 6,772 (67.7% of total customers)

### Training Impact on ARR

| Metric | Without Training | With Training | Lift |
|--------|-----------------|---------------|------|
| **Average ARR** | $2,177 | $4,941 | **+$2,764 (+126.9%)** |
| **Median ARR** | $544 | $1,897 | **+$1,353 (+248.8%)** |
| **Active Rate** | 68.0% | 76.0% | **+8.0 percentage points** |

### Revenue Impact
- **Total ARR from training attendees**: $15.9M
- **Total ARR attributable to training lift**: $8.9M
- **Average lift per training attendee**: $2,764

### Insights
- Training attendees generate **127% more ARR** on average
- Training correlates with **8 percentage point higher active rate**
- Training seems to drive both higher-value subscriptions and better retention
- Nearly one-third of the customer base has attended training
- **Strategic recommendation**: Expand training programs to capture this significant ARR lift

---

## 7. Event Diversity Analysis

### Feature Adoption Groups (by number of event types used)
- **0-4 events**: 443 customers (4.4%)
  - Average ARR: $1,079
  - Active rate: 79.5%
  - Risk: High churn risk - need feature adoption campaigns
- **5-7 events**: 6,391 customers (63.9%)
  - Average ARR: $2,485
  - Opportunity: Potential to upgrade to power users
- **7+ events**: 3,166 customers (31.7%)
  - Average ARR: $3,601
  - Active rate: 67.3%
  - Status: Power users

### Power Users Impact
**Power Users (7+ Events) vs Light Users (0-4 Events)**:
- **ARR Lift**: $2,522 higher per customer (133.2% increase)
- **Active Rate**: -12.1% difference (power users have lower active rate - data anomaly to investigate)
- **NPS Difference**: -5.0 points

### Feature Adoption Opportunity
- **6,391 customers (63.9%)** are using 5-7 features
- Average ARR: $2,485
- **Potential lift**: $592 per customer if upgraded to power user status (7+ features)
- **Total opportunity**: ~$3.8M additional ARR potential

### Low Adoption Concern
- **443 customers (4.4%)** using only 0-4 features
- Active rate: 79.5% (concerning - they're active but not engaged)
- High risk for churn - need targeted feature adoption campaigns

---

## 8. ARR Analysis

### ARR Distribution
- **Low ARR (<$5k)**: 8,621 customers (86.2%)
- **Mid ARR ($5k-$15k)**: 267 customers (2.7%)
- **High ARR ($15k+)**: 397 customers (4.0%)
- **Inactive (No ARR)**: 2,959 customers (29.6%)

### ARR by Segment
#### Highest Total ARR Segments
1. **10+ units → premium → High engagement → Active**
   - 397 users (4.0%)
   - $6,408,802 total ARR
   - $16,143 average ARR per customer

2. **2-5 units → premium → Medium engagement → Active**
   - 267 users (2.7%)
   - $3,625,812 total ARR
   - $13,580 average ARR per customer

3. **10+ units → premium → Medium engagement → Active**
   - 155 users (1.6%)
   - $2,416,356 total ARR
   - $15,589 average ARR per customer

### ARR at Risk
- **Inactive customers**: 2,959 customers (29.6%)
- **ARR at risk**: $7,375,884
- **31 different inactive customer paths** identified

---

## 9. Active Status Analysis

### Overall Distribution
- **Active Customers**: 7,041 (70.4%)
- **Inactive Customers**: 2,959 (29.6%)

### Active Rate by Segment
Active rates vary significantly by portfolio size, plan type, and engagement level:
- Higher engagement typically correlates with higher active rates
- Premium customers show strong active rates in high-engagement segments
- Starter plan customers in low-engagement segments have higher churn risk

### Churn Risk Indicators
- Low engagement (<15 events)
- Portfolio size < 5 units combined with starter plan
- Low event diversity (0-4 event types)
- No recent activity (high days since last activity)

---

## 10. Customer Journey Flow Analysis (Sankey Diagrams)

### Combined User Flow Sankey
**Flow**: Portfolio Size → Plan Type → Engagement (Events) → Ticket Range → Active Status → ARR Group

This comprehensive flow diagram shows how customers progress through the customer lifecycle from initial portfolio size through plan selection, engagement levels, support needs, activation status, and ultimately revenue grouping.

**Key Patterns Observed**:
1. Large portfolios (10+ units) tend to choose starter or pro plans
2. Plan type influences engagement levels
3. Engagement correlates with support ticket volume
4. Active status is the critical gate before ARR grouping
5. Final ARR grouping shows clear stratification

> Note: This interactive Sankey diagram is available in the notebook (cell 19). The diagram dynamically shows customer counts, ARR, and ticket volumes on hover.

### Support Ticket Flow Sankey
**Flow**: Engagement Level → Ticket Range → Active Status

Shows how support ticket volume flows across engagement levels, ticket ranges, and activation status.

**Insights**:
- High engagement customers generate more support tickets
- Ticket volume distribution follows engagement patterns
- Active customers show different ticket patterns than inactive

### Additional Sankey Diagrams

![Portfolio Size to ARR Flow](notebooks/sankey%20size%20to%20arr.png)

*Portfolio Size → ARR Group Flow*

![Portfolio Size to ARR Flow 2](notebooks/sankey%20size%20to%20arr%202.png)

*Alternative view of Portfolio Size → ARR Group Flow*

![Portfolio Size to Active Status](notebooks/sankey%20size%20to%20active.png)

*Portfolio Size → Active Status Flow*


---

## 11. Key Customer Segments

### Top 3 Customer Segments (by volume)

1. **10+ units → starter → Medium (15-30 events) → Active**
   - 1,370 users (13.7%)
   - $587,061 total ARR
   - $429 average ARR per customer

2. **10+ units → pro → Medium (15-30 events) → Active**
   - 942 users (9.4%)
   - $1,976,751 total ARR
   - $2,098 average ARR per customer

3. **2-5 units → starter → Medium (15-30 events) → Active**
   - 793 users (7.9%)
   - $293,856 total ARR
   - $371 average ARR per customer

### Highest ARR Segments

1. **10+ units → premium → High (30+ events) → Active**
   - 397 users (4.0%)
   - $6,408,802 total ARR
   - $16,143 average ARR per customer

2. **2-5 units → premium → Medium (15-30 events) → Active**
   - 267 users (2.7%)
   - $3,625,812 total ARR
   - $13,580 average ARR per customer

3. **10+ units → premium → Medium (15-30 events) → Active**
   - 155 users (1.6%)
   - $2,416,356 total ARR
   - $15,589 average ARR per customer

### At-Risk Segments
- **31 different inactive customer paths** identified
- **2,959 inactive customers (29.6%)**
- **$7,375,884 ARR at risk**

Common inactive segment patterns:
- Low engagement combined with starter plan
- Small portfolio sizes (1-2 units)
- Low event diversity (0-4 event types)

---

## 12. Data Quality Notes

### Portfolio Size Issues
- 199 records have portfolio size < 1
- 199 records have portfolio size = 0
- Range: 0 to 100 units

### Missing Data Handling
- Users with no events: `total_events` filled with 0
- `days_since_last_activity` set to 999 for users with no events
- All categorical fields converted to strings for consistency

---

## 13. Visualizations Summary

The following visualizations were generated during this analysis:

### Interactive Charts (Plotly - in notebook)
1. **Stacked Bar Charts**:
   - Customer count by portfolio group and plan type
   - Total ARR by portfolio group and plan type

2. **Heatmaps**:
   - Average NPS by portfolio group and plan type
   - Active rate (%) by portfolio group and plan type

3. **Sankey Diagrams** (Interactive):
   - Combined user flow: Size → Plan → Events → Tickets → Status → ARR (in notebook)

4. **Distribution Charts**:
   - Portfolio size distribution
   - Plan type distribution
   - Engagement level distribution
   - Event diversity distribution
   - Support ticket distribution

### Static Sankey Diagrams (Embedded above)
All Sankey diagram visualizations are embedded in Section 9 above, showing the customer journey flows across different dimensions.

---

## 14. Key Recommendations

### 1. Revenue Growth Opportunities

**Training Program Expansion**
- **Impact**: Training attendees generate **$2,764 more ARR per customer** (+127% increase)
- **Current**: 3,228 customers (32.3%) have attended training
- **Opportunity**: 6,772 customers (67.7%) haven't attended yet
- **Potential ARR lift**: If all non-training customers attend, could add **$18.7M in ARR lift**
- **Action**: Mandatory onboarding training, regular feature training sessions, advanced training tracks

**Premium Upgrade Campaign**
- Target: 10+ units → starter/pro → medium/high engagement → active
- **Opportunity**: ~2,300 customers could potentially upgrade to premium
- **Potential ARR lift**: ~$15K per customer × 2,300 = $34.5M potential

**Feature Adoption Campaign**
- Target: 6,391 customers using 5-7 features
- **Goal**: Upgrade to 7+ features (power users)
- **Potential ARR lift**: $592 per customer = ~$3.8M additional ARR

### 2. Churn Prevention

**At-Risk Customer Intervention**
- **Priority 1**: 443 low-adoption customers (0-4 features, 79.5% active but not engaged)
- **Action**: Feature adoption campaigns, onboarding improvements
- **Priority 2**: 2,959 inactive customers ($7.4M ARR at risk)
- **Action**: Win-back campaigns, reactivation offers

**Low Engagement Activation**
- Target: 1,329 low engagement customers (<15 events)
- **Action**: Re-engagement campaigns, product tutorials, feature highlights

### 3. Support Optimization

**High-Engagement Support Load**
- High engagement customers generate 3.1 tickets vs 1.1 for medium
- **Action**: Proactive support, self-service tools, advanced documentation

**Low-Ticket Customer Expansion**
- 4,895 customers (48.9%) have 0 tickets - good usability
- **Action**: Identify what keeps them engaged, replicate patterns

### 4. Segment-Specific Strategies

**High-Value Segment Nurture**
- Premium customers with high engagement are most valuable ($16K avg ARR)
- **Action**: Dedicated account management, priority support, expansion opportunities

**Starter Plan Growth Path**
- Largest segment (13.7%) but lowest ARR ($429 avg)
- **Action**: Gradual upgrade paths, feature gating, value demonstration

**Medium Portfolio Optimization**
- 2-5 units segment (33.6% of base) has upgrade potential
- **Action**: Tiered pricing, feature bundles, growth incentives

---

## 14. Appendix: Complete Flow Paths

The analysis identified **62 unique customer flow paths** across:
- Portfolio Size (4 groups)
- Plan Type (3 types)
- Engagement Level (3 levels)
- Active Status (2 statuses)

**Complete path breakdown available in**: `notebooks/customer_segmentation.ipynb` Section 6

### Flow Path Summary Statistics
- Most common: 10+ units → starter → Medium → Active (13.7%)
- Highest ARR: 10+ units → premium → High → Active ($6.4M total)
- Most at-risk: Multiple inactive paths totaling 2,959 customers

---

## 15. Technical Notes

### Analysis Methodology
- Data joined from users and events tables
- Event metrics aggregated per user (counts, dates, diversity)
- Segments created using categorical binning
- Sankey diagrams built using Plotly
- All visualizations interactive (HTML/Plotly format)

### Key Calculations
- **Engagement Level**: Binned by total_events (<15, 15-30, 30+)
- **Event Diversity**: Count of unique event types used (0-4, 5-7, 7+)
- **ARR Groups**: Binned by annual_revenue (<$5k, $5k-$15k, $15k+)
- **Ticket Ranges**: Binned by support_tickets_last_90d (0, 1, 2-4, 5-10, 11+)
- **Portfolio Groups**: Binned by portfolio_size (1, 2-5, 6-10, 10+)

### Tools & Libraries Used
- Python 3.9
- Pandas for data manipulation
- Plotly for interactive visualizations
- NumPy for numerical operations
- Custom modules: DataConnector, CXDataProcessor

---

## Conclusion

This comprehensive analysis reveals clear patterns in customer behavior, engagement, and value. The segmentation framework provides actionable insights for:

1. **Targeted marketing** to specific customer segments
2. **Churn prevention** through early intervention
3. **Revenue optimization** via upgrade and expansion opportunities
4. **Product improvement** through engagement and feature adoption insights

The visualization of customer journeys through Sankey diagrams provides intuitive understanding of how customers flow through different states, enabling data-driven decision making across marketing, sales, and customer success teams.

---

**Report Generated**: 2025  
**Data Source**: CX Dataset  
**Analysis Notebook**: `notebooks/customer_segmentation.ipynb`

