# Harriet

A Discord bot built with `discord.py`. It's a hobby project I'm using to learn how Discord bots work.

## Features

- Music in voice channels, from YouTube, links or local files
- Moderation: kick, ban, timeout, warnings, channel lock and slowmode
- Games with buttons (tic-tac-toe, connect four, blackjack, minesweeper and more), with XP and a leaderboard
- Reminders, dice, member and server lookups
- Every command works as both `/command` and a prefix command like `do command`

See [COMMANDS.md](COMMANDS.md) for the full list of commands.

## Setup

Requires Python 3.10+, a Discord bot token, and [FFmpeg](https://ffmpeg.org/download.html) on your `PATH` for music.

```
git clone https://github.com/mowtiie/Harriet.git
cd Harriet
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

Add your bot token to `.env`, then start the bot:

```
python bot.py
```

Run the tests with `python -m unittest discover -s tests -t .`

## Discord Developer Portal

1. At https://discord.com/developers/applications, create an application and open its **Bot** tab.
2. Click **Reset Token** and put the value in `.env` as `DISCORD_TOKEN`.
3. Under **Privileged Gateway Intents**, enable **Message Content** and **Server Members**.
4. Under **OAuth2 → URL Generator**, select the scopes `bot` and `applications.commands`, plus these permissions: Send Messages, Read Message History, Manage Messages, Connect, Speak, Kick Members, Ban Members, Moderate Members, Manage Channels and Manage Roles.
5. Open the generated URL to invite the bot. When new features need more permissions, run `/invite` for an updated link.

## Configuration

Settings live in `.env`. Invalid values stop startup with an error naming the variable.

| Variable | Description | Default |
| --- | --- | --- |
| `DISCORD_TOKEN` | Bot token (required) | — |
| `COMMAND_PREFIX` | Prefix for text commands | `do ` |
| `LOG_LEVEL` | `DEBUG`, `INFO`, `WARNING`, `ERROR` | `INFO` |
| `BOT_STATUS` | `online`, `idle`, `dnd`, `invisible` | `online` |
| `BOT_ACTIVITY_TYPE` | `playing`, `listening`, `watching`, `competing` | `playing` |
| `BOT_ACTIVITY_NAME` | Text shown after the activity type | `with discord.py` |
| `MAX_CLEAR_AMOUNT` | Most messages `clear` can delete at once | `100` |
| `BOT_VERSION` | Version shown by `info` | `1.0.0` |
| `BOT_REPO_URL` | Source link shown by `info` (empty hides it) | `https://github.com/mowtiie/Harriet` |
| `BOT_SUPPORT_URL` | Support link shown by `info` (empty hides it) | — |
| `DATABASE_PATH` | SQLite file for settings, warnings, reminders and XP | `data/harriet.db` |
| `MUSIC_DIR` | Folder of local audio files `play` can use | `music` |
| `DEFAULT_VOLUME` | Music volume (0 to 100) for servers that haven't set one | `50` |
| `MAX_QUEUE_SIZE` | Most tracks a server can queue | `50` |
| `MUSIC_IDLE_TIMEOUT_SECONDS` | Seconds of silence before the bot leaves voice | `120` |
| `MAX_REMINDERS_PER_USER` | Most pending reminders one person can have | `10` |
| `MAX_REMINDER_DAYS` | Furthest ahead a reminder can be set, in days | `365` |
| `GAME_TIMEOUT_SECONDS` | Inactivity before a game expires | `60` |
| `COOKIE_CASE_TIMEOUT_SECONDS` | Inactivity before a `cookie` mystery goes cold (puzzles need more thinking time) | `300` |
| `XP_PER_WIN` | XP for winning a game against another member | `50` |
| `XP_PER_BOT_WIN` | XP for beating the bot at a game | `10` |

## Privacy

The bot sends no data anywhere and has no analytics. It keeps only per-server settings, warnings, pending reminders and XP totals, in the local SQLite file at `DATABASE_PATH`. Logs go to `logs/bot.log` on the host and are cleared on every startup.

## License

Released under the [MIT License](LICENSE).
