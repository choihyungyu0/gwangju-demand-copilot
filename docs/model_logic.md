# Demand Scoring Logic

## Why This Formula Exists

The MVP needs one explainable demand prediction score, not just separate public-data fields. The current formula combines supply, attraction, visitor flow, events, and weather risk into a single 0-100 score that small business owners can read quickly.

This is a rule-based baseline. It is intentionally simple, transparent, and safe to run without API keys.

## Components

- `commercial_score` (25%): Normalized commercial density from matched store counts. It represents base supply-side demand potential.
- `tourism_component_score` (20%): Tourism attraction strength from tourism spots, cultural facilities, and related tourism scoring.
- `visitor_component_score` (25%): Visitor demand flow. It is the strongest demand-side ingredient with commercial density.
- `event_component_score` (10%): Short-term uplift from events and festivals.
- `weather_component_score` (20%): Weather demand risk. Rain and poor weather reduce the score, while clear conditions support outdoor traffic.

## Interpretation

- 85-100: 매우 높음. Prepare for peak demand and stronger conversion tactics.
- 70-84: 높음. Keep staffing and inventory ready for growth opportunities.
- 55-69: 보통. Maintain baseline operations and watch local risks.
- 0-54: 낮음. Use conservative staffing, inventory, and promotion plans.

## Limitations

- Current visitor and weather features can be mock fallback data.
- The score does not yet learn from real sales, card spending, floating population, or observed foot traffic.
- Area-level scores may hide street-level differences inside the same district.
- Weather and event effects are simplified and may vary by business type.

## Future ML Plan

When enough real public and operating data is available, this formula can become a baseline model. Future versions can train and validate a machine learning model using observed demand targets, calibrate feature weights by business category, and generate confidence intervals for each area forecast.
