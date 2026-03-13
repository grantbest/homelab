# BettingApp Data Model (3NF)

## Tables
- **teams:** `team_id` (PK), `abbreviation`, `bullpen_era_rank`.
- **inning_logs:** `log_id` (PK), `game_id`, `inning_number`, `half`, `runs_scored`, `baserunners`. Unique on (game_id, inning_number, half).
- **bet_tracking:** `bet_id` (PK), `game_id`, `system_triggered`, `odds_taken`, `stake`, `result`, `ai_insight`.
- **betting_rules:** `rule_id` (PK), `name`, `description`, `status`, `conditions_json`, `action_config`.
