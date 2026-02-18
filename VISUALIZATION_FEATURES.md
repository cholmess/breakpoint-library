# BreakPoint Library - Visualization Features

BreakPoint now includes built-in ASCII-based visualizations to make evaluation results easier to understand at a glance.

## Overview

The visualization feature adds three types of charts to the CLI output:

1. **Cost Comparison Chart** - Visual bar chart comparing baseline vs candidate costs
2. **Output Length Comparison Chart** - Visual comparison of output text lengths
3. **Policy Status Overview** - Color-coded visual summary of all policy checks

## Features

### 1. Cost Comparison Chart

Shows a side-by-side comparison of baseline and candidate costs using ASCII bars:

```
Cost Comparison:
  Baseline: $1.0000 █████████████████████
  Candidate: $1.4000 ██████████████████████████████
  Increase: +40.0%
  🔴 BLOCK threshold (40%) exceeded
```

**Features:**
- Proportional bar lengths based on cost values
- Shows percentage increase
- Displays threshold warnings (WARN at 20%, BLOCK at 40%)
- Color-coded indicators (🟡 for WARN, 🔴 for BLOCK)

### 2. Output Length Comparison Chart

Visualizes the difference in output text length:

```
Output Length Comparison:
  Baseline: 46 chars ███████████████████████████
  Candidate: 50 chars ██████████████████████████████
  Expanded: 8.7%
```

**Features:**
- Proportional bars showing relative lengths
- Direction indicator (expanded/compressed)
- Percentage delta calculation
- Threshold markers (WARN at 35%, BLOCK at 70%)

### 3. Policy Status Overview

Color-coded visual summary of all policy evaluation results:

```
Policy Status Overview:
  🔴 ✗ No PII detected      ██████████
  🟢 ✓ Response format      ██
  🔴 ✗ Cost                 ██████████
  🟢 ✓ Latency              ██
  🟢 ✓ Output drift         ██
```

**Features:**
- Color indicators:
  - 🟢 Green for ALLOW (passing policies)
  - 🟡 Yellow for WARN (risky but not blocking)
  - 🔴 Red for BLOCK (policy violations)
- Visual bar length indicates severity:
  - Short bar (██) for ALLOW
  - Medium bar (██████) for WARN
  - Long bar (██████████) for BLOCK
- Status symbols (✓, ⚠, ✗) for quick scanning

## Example Output

Here's a complete example showing all visualizations:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
BreakPoint Evaluation
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Mode: lite

Input Comparison:
  Output Length: 46 chars → 50 chars
  Cost: $1.0000 → $1.4000
  Latency: 100ms → 170ms
  Model: gpt-4.1-mini → gpt-4.1-mini

Final Decision: BLOCK

Policy Results:
✗ No PII detected: Detected 1 match(es). [Types: EMAIL(1)]
✓ Response format: No schema drift detected.
✗ Cost: Delta +40.00%. ($1.0000 → $1.4000, +$0.4000)
✓ Latency: No issues. (100ms → 170ms, +70ms)
✓ Output drift: No issues. (46 → 50 chars)

Detailed Metrics:
  Cost delta %: +40.00%
  Cost delta USD: +0.400000
  PII blocked total: 1
  PII blocked type count: 1

Visualizations:
  Cost Comparison:
    Baseline: $1.0000 █████████████████████
    Candidate: $1.4000 ██████████████████████████████
    Increase: +40.0%
    🔴 BLOCK threshold (40%) exceeded
  Output Length Comparison:
    Baseline: 46 chars ███████████████████████████
    Candidate: 50 chars ██████████████████████████████
    Expanded: 8.7%
  Policy Status Overview:
    🔴 ✗ No PII detected      ██████████
    🟢 ✓ Response format      ██
    🔴 ✗ Cost                 ██████████
    🟢 ✓ Latency              ██
    🟢 ✓ Output drift         ██

Summary:
- Cost increased by 40.0% (>=40%).
- PII detected: EMAIL(1). Total matches: 1.

Reason Codes:
  - COST_INCREASE_BLOCK
  - PII_EMAIL_BLOCK

Exit Code: 0
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## Benefits

1. **Quick Visual Scanning**: See problems at a glance with color-coded indicators
2. **Proportional Understanding**: Bar charts show relative differences clearly
3. **Threshold Awareness**: Visual markers show when thresholds are exceeded
4. **No Dependencies**: Pure ASCII/Unicode - works in any terminal
5. **CI/CD Friendly**: Works in automated environments without special requirements

## Technical Details

- **No External Dependencies**: Uses only standard Python and Unicode characters
- **Terminal Compatible**: Works in any terminal that supports Unicode
- **Proportional Scaling**: Bars are scaled to 30 characters max for readability
- **Automatic Detection**: Visualizations appear automatically when relevant data is available

## Future Enhancements (Optional)

For users who want richer visualizations, potential future additions could include:

1. **HTML Report Export**: Generate HTML files with interactive charts using libraries like Plotly
2. **SVG Visualization**: Export policy decision trees as SVG diagrams
3. **Image Export**: Generate PNG charts using matplotlib for reports
4. **Interactive Mode**: Terminal-based interactive exploration using libraries like `rich` or `plotext`

These would be optional features requiring additional dependencies, while the current ASCII visualizations remain the default zero-dependency solution.

---

*Visualizations are automatically included in all evaluation outputs when baseline and candidate data are available.*

