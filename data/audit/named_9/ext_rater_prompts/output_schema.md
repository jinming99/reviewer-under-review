# Output Schema

## CSV Columns

Each batch output CSV should contain one row per review (18 per batch for batches 1-9, 6 for batch 10).

| Column | Type | Description |
|--------|------|-------------|
| review_id | string | `EXT2-{batch}{seq}` e.g., EXT2-01A through EXT2-01R |
| paper_slug | string | Paper identifier |
| system | string | L, A, O, or M |
| model | string | Opus or GPT4o |
| official_decision | string | ACCEPTED or REJECTED |
| tone_verdict | string | ACCEPT, REJECT, or AMBIGUOUS |
| tone_confidence | string | high, medium, or low |
| tone_signal | string | One sentence explaining tone verdict |
| gate_verdict | string | ACCEPT, REJECT, or AMBIGUOUS |
| gate_reason | string | One sentence explaining gate verdict |
| triggered_gates | string | Comma-separated gates, e.g., "G1, G2, G4" |
| fundamental_gate_hits | integer | Count of major/fatal concerns in G1/G2/G4/G5 |
| fatal_concern_present | boolean | true/false |
| num_concerns | integer | Total concerns in the sheet |
| num_decisive_concerns | integer | Concerns with decisive=true |
| num_major_fatal_concerns | integer | Concerns with severity fatal or major |
| has_accept_signal | boolean | true if decision_drivers contains pro_accept |
| per_concern_gates_json | string | JSON: `[{"id":"A1","gates":["G1"]},...]` |
| structural_unreliable_flag | string | YES or empty |
| positive_tone_missed_flaws_flag | string | YES or empty |

## Notes

- Use the `EXT2-` prefix to distinguish from the first 20-paper audit (`EXT-` prefix).
- `per_concern_gates_json` should include ALL concerns (major/fatal with gates, moderate/minor with empty gates list).
- For structural_unreliable_flag: set YES for System M reviews with agent coordination artifacts, repeated fragments, or incoherent structure. Also set YES for any other system's reviews that are clearly broken.
- For positive_tone_missed_flaws_flag: set YES when tone_verdict=ACCEPT but gate_verdict=REJECT. This indicates the review sounds positive but identifies (or should identify) fundamental issues.
