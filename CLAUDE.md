# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Development
```bash
# Install in editable mode (from source)
pip install -e .

# Run linter
ruff check nanobot/

# Run tests
pytest

# Run specific test
pytest tests/test_tool_validation.py -v
```

### CLI Usage
```bash
# Initialize config and workspace
nanobot onboard

# Chat with agent (single message)
nanobot agent -m "Hello"

# Interactive mode
nanobot agent

# Start gateway (connects chat channels)
nanobot gateway

# Show status
nanobot status

# Scheduled tasks
nanobot cron list
nanobot cron add --name "daily" --message "Check status" --every 3600
nanobot cron add --name "morning" --message "Good morning!" --cron "0 9 * * *"
nanobot cron remove <job_id>

# WhatsApp linking
nanobot channels login
nanobot channels status
```

### WhatsApp Bridge (Node.js)
The WhatsApp bridge is in `bridge/` and uses Node.js:
```bash
cd bridge
npm install
npm run build    # Compile TypeScript
npm start        # Run QR login flow
```

## Architecture

### Core Components

**Agent Loop** (`nanobot/agent/loop.py`)
- Central processing engine: receives messages from bus → builds context → calls LLM → executes tools → sends responses
- Runs in an async loop, consuming from `MessageBus` and publishing `OutboundMessage`
- Handles both user messages and system messages (from subagents)
- Supports up to `max_tool_iterations` (default 20) for multi-step tool use

**Context Builder** (`nanobot/agent/context.py`)
- Assembles system prompt from:
  - Identity (current time, runtime, workspace path)
  - Bootstrap files (AGENTS.md, SOUL.md, USER.md, TOOLS.md, IDENTITY.md)
  - Memory (MEMORY.md)
  - Skills (always-loaded and available skills)
- Builds message list for LLM with history, current message, and optional media (images)

**Tool Registry** (`nanobot/agent/tools/registry.py`)
- Dynamic tool registration and execution
- Tools inherit from `Tool` base class with `name`, `description`, `parameters` (JSON Schema), `execute()` async method
- Built-in tools: read_file, write_file, edit_file, list_dir, exec, web_search, web_fetch, message, spawn, cron

**Message Bus** (`nanobot/bus/queue.py`)
- Async queue-based message routing between channels, agent, and services
- `InboundMessage`: from chat channels to agent
- `OutboundMessage`: from agent to chat channels

**LLM Provider** (`nanobot/providers/litellm_provider.py`)
- Uses LiteLLM for multi-provider support (OpenRouter, Anthropic, OpenAI, Gemini, DeepSeek, vLLM, etc.)
- Auto-detects provider by API key prefix or model name
- Returns `LLMResponse` with content, tool_calls, finish_reason, usage

**Channel Manager** (`nanobot/channels/manager.py`)
- Initializes and manages chat channels (Telegram, WhatsApp, Feishu)
- Each channel inherits from `BaseChannel` with `start()`, `stop()`, `send()` methods
- WhatsApp bridge communicates via WebSocket to `bridge/` Node.js process

**Session Manager** (`nanobot/session/manager.py`)
- Persists conversation history per `channel:chat_id` key
- History in LLM message format (role: user/assistant/tool, content)

**Skills System** (`nanobot/agent/skills.py`)
- Bundled skills in `nanobot/skills/`: github, weather, summarize, tmux, skill-creator, cron
- Custom skills in `~/.nanobot/workspace/skills/{skill-name}/SKILL.md`
- Skills have YAML frontmatter (name, description, always: bool, available: bool, deps)
- "Always" skills are included in system prompt; "available" skills are loaded on-demand via read_file

**Subagents** (`nanobot/agent/subagent.py`)
- Spawn tool creates background tasks via `SubagentManager`
- Subagents run independently and announce results via system channel

**Cron Service** (`nanobot/cron/service.py`)
- Scheduled tasks with three modes: `every` (interval), `cron` (cron expression), `at` (one-time)
- Jobs stored in `~/.nanobot/data/cron/jobs.json`
- CronTool allows agent to manage jobs from within conversations

**Heartbeat Service** (`nanobot/heartbeat/service.py`)
- Every 30 minutes, checks `~/.nanobot/workspace/HEARTBEAT.md`
- If tasks present, sends them to agent for processing

### Configuration

Config file: `~/.nanobot/config.json`

Key sections:
- `providers`: API keys for openrouter, anthropic, openai, deepseek, groq, gemini, vllm
- `agents.defaults.model`: Default LLM model (e.g., "anthropic/claude-opus-4-5")
- `agents.defaults.max_tool_iterations`: Max tool calls per message
- `channels.telegram`: Token, allowFrom (user IDs)
- `channels.whatsapp`: enabled, bridge_url, allowFrom (phone numbers)
- `channels.feishu`: appId, appSecret, encryptKey, verificationToken, allowFrom
- `tools.web.search.api_key`: Brave Search API key (optional)
- `tools.exec`: timeout, restrict_to_workspace

### Workspace

`~/.nanobot/workspace/` contains:
- `AGENTS.md`: Agent instructions and guidelines
- `SOUL.md`: Personality and values
- `USER.md`: User preferences and information
- `TOOLS.md`: Tool documentation
- `HEARTBEAT.md`: Periodic tasks (checked every 30 min)
- `memory/MEMORY.md`: Long-term memory
- `memory/YYYY-MM-DD.md`: Daily notes
- `skills/{skill-name}/SKILL.md`: Custom skills

### Key Patterns

1. **Tool Parameter Validation**: Tools use JSON Schema for parameters. The `Tool` base class provides `validate_params()` which validates before execution.

2. **System Message Routing**: Subagents send results via system channel with `chat_id` format `"original_channel:original_chat_id"` to route responses back correctly.

3. **Tool Context Injection**: Some tools (`message`, `spawn`, `cron`) need current channel/chat_id context. AgentLoop injects this before each message.

4. **Progressive Skill Loading**: "Always" skills are fully included in system prompt. "Available" skills are only summarized to reduce tokens; agent uses `read_file` to load them when needed.

5. **Provider Auto-Detection**: LiteLLMProvider detects provider by API key prefix (`sk-or-` for OpenRouter) or model name, setting appropriate environment variables.

6. **WhatsApp Bridge Communication**: Channel speaks WebSocket to Node.js bridge at `ws://localhost:18790/ws`. Bridge handles Baileys WhatsApp library connection.
