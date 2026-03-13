# Bot Dream (Agent 潜意识漫游与造梦模块)

A subconscious wandering module for OpenClaw agents. This skill triggers during periods of high "boredom" (system idleness) to randomly sample cold historical memory and generate divergent, associative thoughts (Aha Moments).

## Features

- **Boredom Index (无聊度跟踪)**: Monitors the agent's heartbeat cycle. If no tasks are executed, boredom increases.
- **Random Memory Sampling**: Extracts disconnected textual fragments from cold storage (`memory/distilled/`).
- **Low-Cost Dreaming**: Generates a high-temperature prompt forcing an absurd but logical connection between the fragments, logging it for later asynchronous processing.
- **Strict Isolation**: Does not consume the main agent's context window or execution time. Runs entirely in the background.

## Usage

This module is not intended to be called manually. It is integrated into the agent's `HEARTBEAT.md` file:
```bash
python3 scripts/dreamer.py
```

Generated dreams are stored in `AHA_MOMENTS.md`.
