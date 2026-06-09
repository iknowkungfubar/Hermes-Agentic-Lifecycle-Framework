# CLI Reference

## Usage

```bash
half [--version] <command> [args...]
```

## Commands

### `half init`

Initialize a new HALF project.

```bash
half init [--project NAME] [--mode full|prototype|patch|audit] [--dir PATH]
```

### `half status`

Show current pipeline status: active phase, completed phases, error budget.

```bash
half status
```

### `half run-phase <phase>`

Execute a pipeline phase.

```bash
half run-phase phase-1
```

### `half gate-check <phase>`

Run quality gate checks for a phase.

```bash
half gate-check phase-1
```

### `half generate-mrp`

Generate the Merge-Readiness Pack for deployment approval.

```bash
half generate-mrp
```

### `half version`

Show HALF version and exit.

```bash
half version
```

### `half voice`

Voice commands.

```bash
half voice stt <audio-file>   # Transcribe audio to text
half voice tts <text>         # Convert text to speech
```

### `half focalboard`

Focalboard Kanban integration.

```bash
half focalboard create        # Create HALF pipeline board
```
