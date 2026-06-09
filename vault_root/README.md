# HALF Obsidian RAG Storage Vault

## Structure

```
vault_root/
├── .harness/
│   ├── agents.md          # Continuous system context (injected every transaction)
│   └── skills/            # On-demand context (injected via slash commands)
├── 01_raw/                # Staging — unverified logs, transcripts
├── 02_wiki/               # Codified — architecture records, domain invariants
└── 03_output/             # Validated — reports, finalized code components
```

## Usage

This vault is the air-gapped organizational memory layer for HALF.
Mount it as read-only to the execution sandbox:

```bash
docker run -v $(pwd)/vault_root:/workspace/vault:ro ...
```

## Dual-Layer Context Engine

1. **Continuous System Context** (.harness/agents.md): Injected into every transaction.
   Contains immutable boundaries and repository routing strategies. Must stay lean.

2. **On-Demand Context** (.harness/skills/): Complex procedures stored as Markdown scripts.
   Only injected when called via slash commands.
