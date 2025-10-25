# Analysis Page Redesign - Leader-Focused Decision Support

## Problem Statement

The original Analysis page was just "thrown together summary plots and graphs" with no context for non-data-science leaders. It showed:
- Raw tables of sourcing data
- Pie charts without interpretation
- Histograms without explanation
- No actionable recommendations

**User feedback:** "make it actually informative to a non-data-science leader"

---

## Solution: Complete Redesign

Transformed the Analysis page into a **decision brief** format that commanders and staff officers can actually use.

---

## New Structure

### 1. Executive Summary (Top Metrics)
**What:** Four key metrics displayed as cards at the top

**Metrics:**
- **Fill Rate** - with status indicator (GOOD/REVIEW/CRITICAL)
- **Total Cost** - with tooltip explaining components
- **Positions Filled** - shows filled/required and gap count
- **Units Sourced** - number of units providing personnel

**Status Assessment:**
- ✅ **MISSION CAPABLE** (≥95% fill) - "Recommend approval"
- ⚠️ **MARGINAL** (85-95% fill) - "Review critical positions"
- ❌ **NOT MISSION CAPABLE** (<85% fill) - "Recommend re-planning"

**Why This Matters:**
Leaders can see mission readiness status in 5 seconds without scrolling.

---

### 2. Critical Gaps & Risks
**What:** Automatically identifies and prioritizes unfilled positions

**Shows:**
- Which capabilities have gaps
- Gap size (absolute and percentage)
- Risk level (🔴 HIGH >15%, 🟡 MEDIUM 5-15%, 🟢 LOW <5%)
- Recommended actions for each gap

**Example Output:**
```
Capability          Required  Filled  Gap  Gap %  Risk
Infantry Squad      27        24      3    11.1%  🟡 MEDIUM
Fire Support Team   9         6       3    33.3%  🔴 HIGH

Recommended Actions:
1. Fire Support Team: Source 3 additional personnel or reduce requirement
2. Infantry Squad: Source 3 additional personnel or reduce requirement
```

**Why This Matters:**
Leaders know exactly what's missing and how serious it is, without interpreting raw numbers.

---

### 3. Sourcing Breakdown
**What:** Shows which units are providing personnel, with plain-language interpretation

**Features:**
- Table sorted by soldiers sourced (descending)
- Unit names (not just UICs)
- Cost per unit
- **Plain-language summary:**
  - "A/1-2 SBCT provides 45 soldiers (67% of total). This indicates good unit cohesion."
  - OR: "Personnel are cross-leveled from multiple units."

**Visualizations:**
- **Pie chart:** Soldiers by source unit (with percentages inside slices)
- **Bar chart:** Cost by source unit (color-coded by cost)

**Why This Matters:**
Leaders understand sourcing complexity and can plan coordination accordingly.

---

### 4. Capability Fill Status
**What:** Shows how well each required capability is filled

**Features:**
- Required vs Filled for each capability
- Fill percentage
- Status indicators (✅ Complete, ⚠️ Partial, ❌ Critical)
- **Grouped bar chart:** Visual comparison of required vs filled

**Example:**
```
Capability          Required  Filled  Fill %  Status
Infantry Squad      27        27      100%    ✅ Complete
Fire Support Team   9         6       66.7%   ❌ Critical
```

**Why This Matters:**
Leaders see mission capability status at the team/squad level, not just individual positions.

---

### 5. Cost Analysis
**What:** Cost breakdown with interpretation

**Left Panel - Statistics:**
- Average cost per assignment
- Median cost
- Highest single assignment
- **Automated interpretation:**
  - <$2000: "✅ Low average cost indicates good soldier-to-billet matching"
  - $2000-4000: "📊 Moderate costs - typical for cross-unit sourcing"
  - >$4000: "⚠️ High average costs suggest significant mismatches or penalties"

**Right Panel - Visualization:**
- Histogram of assignment costs
- Red dashed line showing average
- Annotation with average value

**Why This Matters:**
Leaders understand if costs are reasonable and where budget scrutiny is needed.

---

### 6. Key Insights & Recommendations
**What:** Auto-generated insights in plain language

**Insight Categories:**

**Fill Rate:**
- "✅ High fill rate achieved - Exercise can proceed with minimal gaps"
- "❌ Low fill rate - Recommend expanding sourcing pool or reducing requirements"

**Cost:**
- "⚠️ High cost per soldier ($6,200) - Consider adjusting MOS mismatch penalties"

**Cross-Leveling:**
- "⚠️ High cross-leveling - Sourcing from 8 units may complicate coordination"
- "✅ Good unit cohesion - Most personnel from 2 unit(s)"

**Critical Capabilities:**
- "✅ Infantry Squad (Priority 1) - Fully staffed"
- "🚨 Fire Support Team (Priority 1) - Gap of 3 soldiers"

**Why This Matters:**
Leaders get the "so what" without needing to interpret data themselves.

---

### 7. Recommended Actions
**What:** Specific next steps based on the analysis

**Conditional Actions:**

**If gaps exist:**
- "Review unfilled positions and determine if they can be left vacant or require backfill"

**If many units sourced:**
- "Coordinate with 8 source units for personnel release and administrative actions"

**If high costs:**
- "Budget approval required - Obtain funding authority for estimated TDY costs"

**If high fill:**
- "Initiate orders process - Begin drafting FRAGOs/WARNORDs for sourced units"
- "Validate training currency - Ensure assigned soldiers meet all readiness gates"

**Always:**
- "Download assignment list (below) and distribute to source units for confirmation"

**Why This Matters:**
Leaders have a clear action plan, not just information.

---

### 8. Export Results
**What:** Two downloadable outputs

**CSV Download:**
- Detailed assignment list (soldier_id, billet_id, unit, MOS, cost, etc.)
- For unit coordinators to execute assignments

**Executive Summary Download:**
- Markdown-formatted summary report
- Includes status, metrics, insights, and recommended actions
- For briefings and records

**Example Summary:**
```markdown
# Manning Assignment Summary Report

## Exercise Details
- Fill Rate: 93.2%
- Total Cost: $182,400
- Positions Filled: 82 / 88
- Units Sourced: 4

## Status
✅ High fill rate achieved - Exercise can proceed with minimal gaps

## Recommended Actions
1. Review unfilled positions and determine if they can be left vacant
2. Coordinate with 4 source units for personnel release
3. Download assignment list and distribute to source units

## Key Metrics
- Average cost per assignment: $2,224
- Primary source unit: A/1-2 SBCT

Generated: 2025-10-23 14:30
```

**Why This Matters:**
Leaders can brief superiors and coordinate with subordinates using ready-made summaries.

---

## Key Improvements

| Before | After |
|--------|-------|
| "Sourcing by Unit" table | **Plain-language summary:** "A/1-2 SBCT provides 67% - good cohesion" |
| Pie chart (no context) | Pie chart + interpretation + cost bar chart |
| "Fill by Capability" table | Fill % with status (✅ Complete / ❌ Critical) + visual comparison |
| Cost histogram (raw) | Cost histogram + average line + interpretation of cost level |
| No insights | Auto-generated insights (fill, cost, cross-leveling, critical caps) |
| No actions | Specific recommended actions based on analysis |
| CSV download only | CSV + Executive Summary (markdown) |
| No status assessment | Clear MISSION CAPABLE / MARGINAL / NOT CAPABLE status |

---

## Design Principles

### 1. **Status First**
- Leaders see overall readiness status before diving into details
- Green/Yellow/Red indicators for quick assessment

### 2. **Plain Language**
- No data science jargon
- Every chart has an interpretation
- Insights written as if briefing a commander

### 3. **Actionable**
- Every section leads to a decision or action
- Specific recommendations, not vague suggestions

### 4. **Priority-Focused**
- Most important information at top
- Critical gaps highlighted before general stats
- Priority 1 capabilities called out specifically

### 5. **Context Always**
- Numbers never shown without explanation
- "This indicates..." or "This means..." for every metric
- Comparative context ("67% from one unit" not just "67%")

---

## Example Walkthrough

**Scenario:** Exercise requiring 3x Infantry Squads, 1x Fire Support Team

### Leader sees:

1. **Top metrics:**
   - Fill: 83.3% ⚠️ MARGINAL
   - Cost: $145,200
   - Filled: 30/36 positions
   - Units: 4

2. **Status:** "⚠️ STATUS: MARGINAL - Some gaps exist. Review critical positions below."

3. **Critical Gaps:**
   - Fire Support Team: 3 soldiers missing (33.3% gap, 🔴 HIGH risk)
   - Action: "Source 3 additional 13F or reduce requirement"

4. **Sourcing:**
   - "A/1-2 SBCT provides 18 soldiers (60% of total). This indicates good unit cohesion."
   - Chart shows most personnel from 1-2 units

5. **Insights:**
   - "✅ Infantry Squad (Priority 1) - Fully staffed"
   - "🚨 Fire Support Team (Priority 1) - Gap of 3 soldiers"

6. **Actions:**
   - "Review unfilled positions and determine if backfill required"
   - "Coordinate with 4 source units for personnel release"
   - "Download assignment list and distribute to source units"

### Leader's Decision:
"Fire Support Team is critical. I'll accept 2 partially-trained 13Fs as substitutes rather than reduce the requirement. Approve the plan."

**Total time to decision:** ~2 minutes (vs 15+ minutes interpreting raw tables)

---

## Implementation Details

**Code Changes:**
- `dashboard.py` lines 563-921 (358 lines)
- Replaced 4 simple functions with 8 comprehensive sections
- Added conditional logic for insights and recommendations
- Created downloadable executive summary

**Dependencies:**
- Uses existing `assignments` and `summary` from session state
- Leverages `capabilities` list for gap analysis
- Accesses `generator.units` for unit names

---

## Testing Checklist

- [ ] Executive summary shows correct status (CAPABLE/MARGINAL/NOT CAPABLE)
- [ ] Critical gaps section identifies all unfilled capabilities
- [ ] Sourcing summary shows primary unit and percentage
- [ ] Capability fill status shows all capabilities with fill %
- [ ] Cost interpretation matches cost ranges (<$2K, $2-4K, >$4K)
- [ ] Insights auto-generate based on fill rate, cost, cross-leveling
- [ ] Recommended actions are specific to the situation
- [ ] CSV download works
- [ ] Executive summary download includes all sections

---

## Future Enhancements

1. **Risk scoring** - Aggregate risk score across all gaps
2. **Timeline** - Suggested timeline for orders/coordination based on gaps
3. **Historical comparison** - Compare to past exercises
4. **Interactive drill-down** - Click capability to see individual assignments
5. **Email draft** - Auto-generate coordination emails to source units

---

**Date:** 2025-10-23
**Status:** ✅ Complete
**Impact:** Transforms raw data into actionable decision support for commanders
