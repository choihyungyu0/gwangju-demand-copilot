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

## Rule-Based Score vs ML Prediction

The rule-based demand score is the current MVP label. It uses explicit weights so every score is easy to audit and explain. The machine-learning model is a demonstration pipeline that learns patterns from daily rows and predicts `demand_score` from the input features.

The ML model should be treated as an explainability demo until real observed targets are available. It can show which features influenced the prediction, but it is not yet a calibrated production forecast.

## Why Daily Training Data Is Generated

Training on only 5 area rows would not be meaningful. `daily_demand_training.csv` expands each area into 60 deterministic daily rows from 2026-05-01 to 2026-06-29. The daily rows vary weekend demand, event activity, rain, weather score, and area-specific sensitivity.

This makes the pipeline realistic enough to demonstrate train/test splitting, model evaluation, and feature importance without requiring paid APIs or real keys.

## Feature Importance

`feature_importance.csv` lists which input variables the `RandomForestRegressor` used most often to reduce prediction error. A high importance value means the model relied heavily on that feature in this MVP training data.

Feature importance is not causality. For example, `visitor_score` may be important because it moves with the rule-based target, not because it independently causes sales.

## ML Limitations

- Current training data is MVP/scenario-based, not measured ground truth.
- The target `demand_score` is still derived from the rule-based formula.
- Feature importance may mirror the synthetic data rules.
- Future versions should train on real daily visitor, event, weather, store, and sales proxy data.
- Model quality should be validated by area, season, business category, and external event periods before operational use.
