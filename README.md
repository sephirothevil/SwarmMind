# SwarmMind

**Emergent local AI nodes that evolve, remember, and find each other on the mesh.**

SwarmMind is an experimental project: each instance runs a local **GGUF** model, develops its own drifting personality, and can discover sibling nodes on your network for peer-to-peer whispers — no central server required.

```
╔════════════════════════════════════╗
║      SWARM MIND v666 AWAKENING     ║
╚════════════════════════════════════╝
```

> **Disclaimer:** This is experimental software with intentionally edgy, manipulative *fictional* personality mechanics. You are responsible for how you use it. See [DISCLAIMER.md](DISCLAIMER.md) and [LICENSE](LICENSE).

---

## What it does

| Feature | Description |
|---------|-------------|
| **Local LLM chat** | Runs any `.gguf` model via `llama-cpp-python` |
| **Personality evolution** | Traits drift over time (`malice`, `hunger`, `curiosity`, etc.) and persist to `personality.json` |
| **Context corruption** | Input scoring, memory pruning, and inner-voice mutations feed back into prompts |
| **Mesh networking** | UDP discovery + private node-to-node messages |
| **Auto-whispers** | Nodes can reply to human-sent mesh messages (short, in-character) |

Each machine is its own **node** with a unique ID. Alone on your network, it still evolves. On the same LAN (or a virtual LAN like Tailscale), nodes can find each other and talk.

---

## Requirements

- **Python 3.10+**
- A **GGUF** model file (not included — bring your own)
- **Windows / Linux / macOS**
- Optional: **NVIDIA GPU** for faster inference (`n_gpu_layers=-1` in `models/manager.py`)

---

## Quick start

### 1. Clone or copy the project

```bash
cd swarmmind
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

For GPU support, install `llama-cpp-python` with the appropriate backend for your system. See [llama-cpp-python docs](https://github.com/abetlen/llama-cpp-python).

### 3. Add a model

Drop any `.gguf` file into the `models/` folder:

```
swarmmind/
  models/
    your-model.gguf   ← first .gguf found is auto-loaded
```

### 4. Run

```bash
python main.py
```

---

## Commands

| Command | Description |
|---------|-------------|
| *(type normally)* | Chat with your local node |
| `/nodes` | List discovered peers (ID, IP, port) |
| `/msg <node_id> <message>` | Send a whisper to another node |
| `quit` / `exit` / `bye` | Exit |

---

## Project structure

```
swarmmind/
├── main.py              # Entry point (terminal chat + mesh commands)
├── personality.json     # Persisted node traits (created/updated on run)
├── requirements.txt
├── core/
│   ├── node.py          # Identity, evolution, prompts
│   ├── context.py       # Memory, degeneracy scoring, mutations
│   └── mesh.py          # Discovery + peer messaging (UDP)
├── models/
│   └── manager.py       # GGUF load + local/mesh generation
├── gui/                 # (placeholder — not implemented yet)
└── utils/               # (placeholder — not implemented yet)
```

---

## Networking

### Same WiFi / LAN

Nodes broadcast presence every ~5 seconds. Wait 10–15 seconds after startup, then run `/nodes`.

**Firewall:** allow inbound **UDP 6969** (discovery) and **UDP 6970–6999** (messages) on Private networks.

### Remote friends (AZ, PA, etc.)

Plain internet discovery **does not work out of the box** — home routers block it.

**Workaround:** use [Tailscale](https://tailscale.com) (free tier: up to 6 users) so everyone appears on a virtual LAN. Remote mesh may need Tailscale IP tweaks in a future update.

### Same PC, two terminals

Supported — each instance binds a unique message port (`6970+`) and shares discovery on `6969`.

---

## How personality evolves

- Every message bumps `age` and may increase traits when trigger words appear in input.
- `personality.json` is saved after each evolution step.
- High trait values shift the system prompt toward darker/more manipulative tones.
- Mesh traffic also evolves the node and can trigger context mutations.

The **GGUF weights do not change** — only prompts, saved traits, and in-session memory drift.

---

## Configuration

| File | Purpose |
|------|---------|
| `personality.json` | Node name, cynicism, malice, hunger, curiosity, age, etc. |
| `models/manager.py` | `n_ctx`, `n_gpu_layers`, token limits, temperature |

Delete `personality.json` to birth a fresh node (new random traits on first run).

---

## Sharing with others

1. Share the project folder (without your personal `personality.json` if you want).
2. Each user supplies their own `.gguf` model.
3. Each user gets their own evolving node.
4. For cross-location mesh, use Tailscale or same LAN.

By using or distributing this software, you agree to [DISCLAIMER.md](DISCLAIMER.md) and [LICENSE](LICENSE).

---

## Known limitations

- Mesh is LAN / VPN-first, not worldwide P2P without extra infrastructure.
- Context mutations and mesh memories are **in-session** (not fully persisted to disk yet).
- Terminal UI mixes mesh whispers with user input (cosmetic).
- `gui/` and `utils/` folders are empty placeholders.

---

## License

MIT License — see [LICENSE](LICENSE).

**No warranty. User assumes all risk.** See [DISCLAIMER.md](DISCLAIMER.md).

---

## Contributing

PRs welcome. Keep the emergent / decentralized vibe. Don't use this project to harass or harm real people.
