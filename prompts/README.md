# Prompt Templates

All LLM prompt templates are stored here as version-controlled files.  
Each template follows the structure specified in the project guidelines:

- **System Prompt** — sets the role and constraints
- **User Prompt** — contains the task, context, and placeholders
- **Output Schema** — defines the expected JSON structure

## Template Inventory

| File | Purpose | Engine |
|---|---|---|
| `requirement_structure.txt` | Parse natural-language requirements into structured JSON | requirement_structurer |
| `risk_analysis.txt` | Assess risk impact & likelihood per requirement | risk_analyzer |
| `equivalence_partition.txt` | Identify input domains and generate EP test cases | blackbox_generator |
| `boundary_value.txt` | Generate BVA test cases from identified ranges | blackbox_generator |
| `decision_table.txt` | Generate decision-table test cases from conditions | blackbox_generator |
| `state_transition.txt` | Extract state-transition tuples from requirements | whitebox_modeler |
| `oracle_synthesis.txt` | Synthesize expected results from inputs and conditions | oracle_synthesizer |
