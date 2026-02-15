# Policy Presets (P1)

BreakPoint ships built-in policy presets for common use cases:

- `chatbot`: conversational responses with higher natural variance
- `support`: support-agent style answers with moderate variance
- `extraction`: structured extraction where drift is more suspicious

Presets are merged before any custom `--config` file, so your project config can override a preset.

## CLI Usage

Evaluate using a preset:

```bash
breakpoint evaluate baseline.json candidate.json --preset chatbot --json
```

Inspect the effective config for a preset:

```bash
breakpoint config print --preset extraction
```

List available presets:

```bash
breakpoint config presets
```

## Notes

- Presets only adjust thresholds; they do not change the output contract.
- You can also set `BREAKPOINT_PRESET` in CI environments instead of passing `--preset`.
