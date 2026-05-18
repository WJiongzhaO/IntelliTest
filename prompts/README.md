# Prompt Templates

All LLM prompt templates are stored here as **version-controlled JSON files**, independent of
application code. This follows Section 4.4 of the project spec:

> 所有 Prompt 模板存储为独立文件（`prompts/` 目录），纳入版本控制

Each template file contains the three required parts:
- **System Prompt** — sets the role and constraints
- **User Prompt Template** — the task, context, and `{placeholders}`
- **Output Schema** — expected JSON structure description

## Template Inventory

| File | Purpose | Engine | Status |
|---|---|---|---|
| `requirement_structure.json` | Parse natural-language requirements into structured JSON | `requirement_structurer` | Done (成员 A) |
| `risk_analysis.txt` | Assess risk impact & likelihood per requirement | `risk_analyzer` | Pending (成员 B) |
| `equivalence_partition.txt` | Identify input domains and generate EP test cases | `blackbox_generator` | Pending (成员 C) |
| `boundary_value.txt` | Generate BVA test cases from identified ranges | `blackbox_generator` | Pending (成员 C) |
| `decision_table.txt` | Generate decision-table test cases from conditions | `blackbox_generator` | Pending (成员 C) |
| `state_transition.txt` | Extract state-transition tuples from requirements | `whitebox_modeler` | Pending (成员 D) |
| `oracle_synthesis.txt` | Synthesize expected results from inputs and conditions | `oracle_synthesizer` | Pending (成员 D) |

## Format Convention

For machine-loadable prompts (JSON), the recommended structure is:

```json
{
  "description": "Brief purpose",
  "engine": "target_engine_name",
  "temperature": 0,
  "system_prompt": "...",
  "output_schema": "...",
  "user_prompt_template": "...",
  "few_shot_examples": [...]
}
```

For human-readable prompts (plain text), use clear section headers:

```
# SYSTEM PROMPT
...

# USER PROMPT TEMPLATE
...

# OUTPUT SCHEMA
...
```

## How Backend Loads

The backend engine loads its prompt from this directory at import time:

```python
# backend/app/engines/requirement_structurer/prompts.py
PROMPT_FILE = Path(__file__).resolve().parents[4] / "prompts" / "requirement_structure.json"
with open(PROMPT_FILE, encoding="utf-8") as fh:
    _data = json.load(fh)
```

Docker mounts this directory read-only into `/app/prompts`.
