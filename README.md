# Harriet

Just a simple and helpful Discord bot that productively wants to make you happy.

## Features

- Modular cog-based architecture, loaded automatically from `cogs/`
- Hybrid commands: every command works as both `do cmd` and `/cmd`
- Music in voice channels from YouTube, links, or local files
- Moderation: kick, ban, timeout, warnings, channel lock and slowmode, with an optional mod-log channel
- Fun: 8-ball and coin flip
- Games: button-based rock paper scissors, tic-tac-toe, connect four, blackjack and hangman
- XP and levels earned by winning games, with a server leaderboard
- Utilities: member, server and role lookups, reminders, dice and random picks
- Per-server settings stored in SQLite
- Customizable presence (via `.env` or `/setpresence`)
- Logging to file and console, cleared on every restart

## Setup

Requires Python 3.10+, a Discord bot token (see the next section), and [FFmpeg](https://ffmpeg.org/download.html) on your `PATH` for music.

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
   - **Connect** and **Speak**: used by the music commands
   - **Kick Members**, **Ban Members**, **Moderate Members**: used by the discipline commands
   - **Manage Channels** and **Manage Roles**: used by `slowmode`, `lock` and `unlock` (changing a channel's permissions needs Manage Roles)
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
| `DATABASE_PATH` | SQLite file for per-server settings | `data/harriet.db` |
| `MUSIC_DIR` | Folder of local audio files `play` can use | `music` |
| `DEFAULT_VOLUME` | Music volume (0 to 100) for servers that haven't set one | `50` |
| `MAX_QUEUE_SIZE` | Most tracks a server can queue | `50` |
| `MUSIC_IDLE_TIMEOUT_SECONDS` | Seconds of silence before the bot leaves voice | `120` |
| `MAX_REMINDERS_PER_USER` | Most pending reminders one person can have | `10` |
| `MAX_REMINDER_DAYS` | Furthest ahead a reminder can be set, in days | `365` |
| `GAME_TIMEOUT_SECONDS` | Inactivity before a game of `rps`, `tictactoe`, `connectfour`, `blackjack` or `hangman` expires | `60` |
| `XP_PER_WIN` | XP for winning a game against another member | `50` |
| `XP_PER_BOT_WIN` | XP for beating the bot at `rps`, `tictactoe`, `connectfour`, `blackjack` or `hangman` | `10` |

## Commands

| Command | Description | Permission |
| --- | --- | --- |
| `/help [command]`, `do help [command]` | Browse commands by category, or get usage and examples for one | Anyone |
| `/info`, `do info` | About the bot and how to use it | Anyone |
| `/ping`, `do ping` | Latency check | Anyone |
| `/hello`, `do hello` | Greeting | Anyone |
| `/play <query>`, `do play <query>` | Play a link, search YouTube, or play a file from `MUSIC_DIR` | Anyone in voice |
| `/skip`, `/pause`, `/resume`, `/stop`, `/leave` | Control playback (`stop` also clears the queue) | Anyone in the bot's voice channel |
| `/join`, `/queue`, `/nowplaying` | Join your channel, show the queue, show the current track | Anyone |
| `/settings`, `do settings` | Show this server's settings | Anyone |
| `/setvolume <0-100>`, `do setvolume <0-100>` | Set the music volume for this server | Manage Server |
| `/setmodlog [channel]`, `do setmodlog [channel]` | Set the channel moderation actions are logged to (empty turns it off) | Manage Server |
| `/kick <member> [reason]` | Kick a member | Kick Members |
| `/ban <user> [reason]`, `/unban <user> [reason]` | Ban or unban a user | Ban Members |
| `/timeout <member> <duration> [reason]` | Time a member out (`30m`, `2h`, `3d`, `1h30m`, up to 28 days) | Moderate Members |
| `/untimeout <member> [reason]` | End a timeout early | Moderate Members |
| `/warn <member> <reason>` | Warn a member and record it | Moderate Members |
| `/warnings <member>`, `/clearwarnings <member>` | Show or remove a member's warnings | Moderate Members |
| `/slowmode <seconds>` | Set channel slowmode (0 turns it off) | Manage Channels |
| `/lock`, `/unlock` | Stop or allow `@everyone` sending in the channel | Manage Channels |
| `/userinfo [member]`, `/avatar [member]` | Member details, or their avatar at full size | Anyone |
| `/serverinfo`, `/roleinfo <role>` | Details about the server or a role | Anyone |
| `/remind <duration> <text>` | Get a reminder after `30m`, `2h`, `1d`, `1h30m`, etc. | Anyone |
| `/reminders`, `/unremind <id>` | List or cancel your pending reminders | Anyone |
| `/roll [dice]` | Roll dice like `d20`, `2d6` or `4d8+3` | Anyone |
| `/choose <a, b, c>` | Pick one option at random | Anyone |
| `/8ball <question>` | Ask the magic 8-ball | Anyone |
| `/coinflip` | Flip a coin | Anyone |
| `/rps [member]` | Rock paper scissors against the bot, or a member (picks stay hidden until both choose) | Anyone |
| `/tictactoe [member]` | Tic-tac-toe against the bot, or a member | Anyone |
| `/connectfour [member]` | Connect four against the bot, or a member | Anyone |
| `/blackjack` | Blackjack against the bot as the dealer (hit or stand; the dealer stands on 17) | Anyone |
| `/hangman` | Guess a random word one letter at a time before the drawing is finished | Anyone |
| `/rank [member]` | Show a member's level, XP and server rank | Anyone |
| `/leaderboard` | Show the server's XP leaderboard | Anyone |
| `/setxp <member> <amount>`, `/resetxp <member>` | Set or clear a member's XP | Manage Server |
| `/clear [n]`, `do clear [n]` | Delete the last n messages (1 to `MAX_CLEAR_AMOUNT`, default 5) | Manage Messages |
| `/setpresence`, `do setpresence` | Change bot presence | Bot owner |
| `/invite`, `do invite` | Get the bot's invite link | Bot owner |

## Games

`rps`, `tictactoe`, `connectfour`, `blackjack` and `hangman` are played with buttons (or letter menus for `hangman`) and only the players can use them. Games live in memory and end after `GAME_TIMEOUT_SECONDS` of inactivity, so a restart ends any game in progress. Nothing about a game is stored.

## XP and levels

XP comes only from winning games: `XP_PER_WIN` for beating another member at `rps`, `tictactoe` or `connectfour`, and the smaller `XP_PER_BOT_WIN` for beating the bot at any of them (`blackjack` and `hangman` are always against the bot, so they always pay `XP_PER_BOT_WIN`). Losses, ties and expired games earn nothing, and chatting or voice time earns nothing either. Reaching a new level posts a short announcement (without pinging anyone) in the channel where the game was played.

Level `n` needs `100 + 50 * n` XP to complete, so level 1 is 100 XP and level 10 is 3,250 XP in total. Only the total is stored, so the curve can change without migrating data. Members who leave are hidden from the leaderboard but keep their XP if they return.

## Reminders

Reminders are saved in the database, so they survive restarts. They are posted in the channel where you set them, pinging only you, and fall back to a DM if that channel is gone. A reminder that came due while the bot was offline is delivered late with a note.

## Moderation notes

- Every action checks the role hierarchy: you can't act on yourself, the server owner, or anyone whose top role is equal to or higher than yours or the bot's.
- Kick, ban, timeout and warn DM the member first (best effort, since closed DMs are skipped). Reasons also appear in the server's audit log.
- Warnings are stored in the same SQLite file as settings (`DATABASE_PATH`).
- `unlock` resets the `@everyone` send permission to its default, which removes any explicit allow you had set on that channel.

## Security & Privacy

The bot does not send user data anywhere and has no analytics or telemetry. It reads message content and member info only to run commands. The only data it keeps is per-server settings, warnings (member ID, moderator ID, reason and time) and pending reminders (user ID, channel ID, text and due time) and XP totals (member ID and XP), stored locally in the SQLite file at `DATABASE_PATH`. `/clearwarnings` deletes a member's warnings, a reminder is deleted once it is delivered or cancelled, and `/resetxp` clears a member's XP.

Logs are written only to `logs/bot.log` on the host machine and are cleared on every startup. They record bot lifecycle events, cog loads, errors with tracebacks, and moderation actions (who did what to whom, where, and why).
## License

Released under the [MIT License](LICENSE). You're free to use, modify and distribute Harriet, including commercially, as long as the copyright notice and license text are kept with any copies. It comes with no warranty.
