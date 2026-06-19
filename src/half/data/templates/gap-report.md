# Gap Report

**Generated:** {{timestamp}}
**Phase:** {{phase_name}}
**Gate ID:** {{gate_id}}
**Project:** {{project_name}}

## What Failed

{{description_of_failure}}

## What Was Tried

| Attempt | Timestamp | Approach | Result |
|---------|-----------|----------|--------|
| 1 | {{time}} | {{approach}} | {{result}} |
| 2 | {{time}} | {{approach}} | {{result}} |
| 3 | {{time}} | {{approach}} | {{result}} |

## Current Artifact State

- **File:** {{path}}
- **Size:** {{lines}} lines
- **Gate score:** {{score}}/{{max}}

## Diagnostic Data

```
{{relevant_logs_or_metrics}}
```

## Required Human Decision

{{specific_question}}

## Options

| Option | Description | Impact |
|--------|-------------|--------|
| A | {{description}} | {{impact}} |
| B | {{description}} | {{impact}} |
| C | {{description}} | {{impact}} |

## Pipeline Status

- **Phase:** {{phase_name}} (PAUSED)
- **Completed phases:** {{completed_phases}}
- **Pending phases:** {{pending_phases}}
- **Retries used:** {{retries_used}}/{{max_retries}}
