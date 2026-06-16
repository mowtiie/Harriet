# Harriet

Just a simple and helpful Discord bot that productively wants to make you happy.

## Features

- Modular cog-based architecture
- Hybrid commands — every command works as both `!cmd` and `/cmd`
- Customizable presence and status (via `.env` or `/setpresence`)
- Logging to file and console, cleared on every restart
- Global error handling

## Requirements

- Python 3.10+
- A Discord application and bot token

## Installation

```
git clone https://github.com/mowtiie/Harriet.git
cd Harriet
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` and add your bot token.

## Running

```
python bot.py
```

## Discord Developer Portal Setup

1. Go to https://discord.com/developers/applications and click **New Application**.
2. Open the **Bot** tab. Click **Reset Token** and copy the value into `.env` as `DISCORD_TOKEN`.
3. Under **Privileged Gateway Intents**, enable:
   - Message Content Intent
   - Server Members Intent
4. Go to **OAuth2 → URL Generator**. Select scopes `bot` and `applications.commands`, then choose the permissions you need (at minimum: Send Messages, Read Message History; add Manage Messages for `clear`).
5. Open the generated URL in a browser and invite the bot to your server.

## Configuration

All settings live in `.env`:

| Variable | Description | Default           |
| --- | --- |-------------------|
| `DISCORD_TOKEN` | Bot token (required) | —                 |
| `COMMAND_PREFIX` | Prefix for text commands | `do `             |
| `LOG_LEVEL` | `DEBUG`, `INFO`, `WARNING`, `ERROR` | `INFO`            |
| `BOT_STATUS` | `online`, `idle`, `dnd`, `invisible` | `online`          |
| `BOT_ACTIVITY_TYPE` | `playing`, `listening`, `watching`, `competing` | `playing`         |
| `BOT_ACTIVITY_NAME` | Text shown after the activity type | `with discord.py` |

The bot owner can also change presence at runtime with `/setpresence`.

## Commands

| Command | Description | Permission |
| --- | --- | --- |
| `/ping`, `do ping` | Latency check | Anyone |
| `/hello`, `do hello` | Greeting | Anyone |
| `/clear <n>`, `do clear <n>` | Delete last n messages | Manage Messages |
| `/setpresence`, `do setpresence` | Change bot presence | Bot owner |

## Project Structure

```
discord-bot/
├── bot.py             Entry point
├── config.py          Settings loaded from .env
├── logger.py          Logging configuration
├── requirements.txt
├── cogs/              Feature modules (auto-loaded)
│   ├── general.py
│   ├── moderation.py
│   └── presence.py
└── logs/              Generated at runtime
```

## Adding Commands

Create a new file in `cogs/` following the pattern in `cogs/general.py`. Any `.py` file in that folder is loaded automatically on startup.

## Data & Privacy

This bot:

- **Does not** collect, store, or transmit user data to any external service
- **Does not** use analytics or telemetry
- Writes logs **only** to `logs/bot.log` on the host machine
- Truncates the log file on every startup (no long-term log accumulation)

Logged events include: bot lifecycle (login, presence changes), cog loads, errors with tracebacks, and moderation actions (who ran `clear`, where, how many messages). Logs stay on the host running the bot and are never sent anywhere.

The bot reads message content (for prefix commands) and member info (for permission checks) per the intents below, but does not store either.

## Why Each Permission and Intent

**Privileged Intents** (enabled in the Developer Portal):

- **Message Content Intent** — required for prefix commands (`!ping`, etc.) to read what users typed
- **Server Members Intent** — required to look up members and check their permissions

**Bot Permissions** (set when inviting):

- **Send Messages** — to respond to commands
- **Read Message History** — required by `clear` to find messages to delete
- **Manage Messages** — required by `clear` to delete them
- **Use Slash Commands** — for slash command invocations

## License

[MIT](LICENSE)

## Security

See [SECURITY.md](SECURITY.md) for vulnerability disclosure.
