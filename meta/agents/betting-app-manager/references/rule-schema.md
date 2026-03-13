# JSON Rule Schema

## Example Structure
{
  "logic": "AND",
  "conditions": [
    {"attribute": "inning", "operator": "==", "value": 2},
    {"attribute": "runs_scored_half", "operator": "==", "value": 0}
  ]
}

## Valid Attributes
- `inning` (int)
- `runs_scored_half` (int)
- `baserunners` (int)
- `pitching_team_bullpen_rank` (int)
- `score_diff` (int)
