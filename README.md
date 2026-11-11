# Harriet

Just a simple and helpful Discord bot that productively wants to make you happy.

## Features

- Modular cog-based architecture, loaded automatically from `cogs/`
- Hybrid commands: every command works as both `do cmd` and `/cmd`
- Customizable presence (via `.env` or `/setpresence`)
- Logging to file and console, cleared on every restart

## Setup

Requires Python 3.10+ and a Discord bot token (see the next section).

```
git clone https://github.com/mowtiie/Harriet.git
cd Harriet
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` and add your bot token, then start the bot:

```
python bot.py
```

To run the tests: `python -m unittest discover -s tests -t .`

## Discord Developer Portal Setup

1. Go to https://discord.com/developers/applications and click **New Application**.
2. Open the **Bot** tab. Click **Reset Token** and copy the value into `.env` as `DISCORD_TOKEN`.
3. Under **Privileged Gateway Intents**, enable:
   - **Message Content Intent**: lets prefix commands read what users type
   - **Server Members Intent**: lets the bot look up members and check their permissions
4. Go to **OAuth2 → URL Generator**. Select the scopes `bot` and `applications.commands`, and these bot permissions:
   - **Send Messages**: to respond to commands
   - **Read Message History** and **Manage Messages**: used by `clear` to find and delete messages
5. Open the generated URL in a browser and invite the bot to your server.

When the bot gains features that need more permissions, run `/invite` for an updated link and re-authorize it. No need to remove the bot first.

## Configuration

All settings live in `.env`. Invalid values stop startup with an error naming the variable.

| Variable | Description | Default           |
| --- | --- |-------------------|
| `DISCORD_TOKEN` | Bot token (required) | —                 |
| `COMMAND_PREFIX` | Prefix for text commands | `do `             |
| `LOG_LEVEL` | `DEBUG`, `INFO`, `WARNING`, `ERROR` | `INFO`            |
| `BOT_STATUS` | `online`, `idle`, `dnd`, `invisible` | `online`          |
| `BOT_ACTIVITY_TYPE` | `playing`, `listening`, `watching`, `competing` | `playing`         |
| `BOT_ACTIVITY_NAME` | Text shown after the activity type | `with discord.py` |
| `MAX_CLEAR_AMOUNT` | Most messages `clear` can delete at once | `100`             |
| `BOT_VERSION` | Version shown by `info` | `1.0.0` |
| `BOT_REPO_URL` | Source link shown by `info` (empty hides it) | `https://github.com/mowtiie/Harriet` |
| `BOT_SUPPORT_URL` | Support link shown by `info` (empty hides it) | — |

## Commands

| Command | Description | Permission |
| --- | --- | --- |
| `/help [command]`, `do help [command]` | Browse commands by category, or get usage and examples for one | Anyone |
| `/info`, `do info` | About the bot and how to use it | Anyone |
| `/ping`, `do ping` | Latency check | Anyone |
| `/hello`, `do hello` | Greeting | Anyone |
| `/clear [n]`, `do clear [n]` | Delete the last n messages (1 to `MAX_CLEAR_AMOUNT`, default 5) | Manage Messages |
| `/setpresence`, `do setpresence` | Change bot presence | Bot owner |
| `/invite`, `do invite` | Get the bot's invite link | Bot owner |

## Security & Privacy

The bot does not collect, store or send user data anywhere, and has no analytics or telemetry. It reads message content and member info only to run commands.

Logs are written only to `logs/bot.log` on the host machine and are cleared on every startup. They record bot lifecycle events, cog loads, errors with tracebacks, and moderation actions (who ran `clear`, where, and how many messages).
## License

Released under the [MIT License](LICENSE). You're free to use, modify and distribute Harriet, including commercially, as long as the copyright notice and license text are kept with any copies. It comes with no warranty.
