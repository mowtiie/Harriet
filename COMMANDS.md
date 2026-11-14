# Commands

Every command works as a slash command (`/play`) and as a prefix command (`do play`, using `COMMAND_PREFIX`). Run `/help` in Discord to browse them, or `/help <command>` for usage and examples.

## General

| Command | Description | Permission |
| --- | --- | --- |
| `/help [command]` | Browse commands by category, or get usage and examples for one | Anyone |
| `/info` | About the bot and how to use it | Anyone |
| `/ping` | Latency check | Anyone |
| `/hello` | Greeting | Anyone |
| `/invite` | Get the bot's invite link | Bot owner |

## Games

| Command | Description | Permission |
| --- | --- | --- |
| `/rps [member]` | Rock paper scissors against the bot, or a member (picks stay hidden until both choose) | Anyone |
| `/tictactoe [member]` | Tic-tac-toe against the bot, or a member | Anyone |
| `/connectfour [member]` | Connect four against the bot, or a member | Anyone |
| `/battleship [member]` | Battleship on a 5×5 board against the bot, or a member | Anyone |
| `/blackjack` | Blackjack against the bot as the dealer (hit or stand; the dealer stands on 17) | Anyone |
| `/hangman` | Guess a random word one letter at a time before the drawing is finished | Anyone |
| `/guess` | Guess my number from 1 to 100 in 8 tries, with higher or lower hints | Anyone |
| `/minesweeper` | Clear a 5×5 field with 5 hidden mines (the first square is always safe) | Anyone |
| `/rank [member]` | Show a member's level, XP and server rank | Anyone |
| `/leaderboard` | Show the server's XP leaderboard | Anyone |
| `/setxp <member> <amount>`, `/resetxp <member>` | Set or clear a member's XP | Manage Server |

Games are played with buttons (letter menus for `hangman`, a pop-up form for `guess`) and only the players can use them. They live in memory and end after `GAME_TIMEOUT_SECONDS` of inactivity, so a restart ends any game in progress.

**Battleship.** Each side gets a random fleet of three ships (3, 2 and 2 squares) on a 5×5 board, and players take turns firing at squares like `B3`. The message only shows hits (💥), sunk ships (🔥) and misses (🌊). Press **My fleet** to see your own board privately. Against the bot, it fires back right after each of your shots.

**XP and levels.** XP comes only from winning: `XP_PER_WIN` for beating another member at `rps`, `tictactoe`, `connectfour` or `battleship`, and the smaller `XP_PER_BOT_WIN` for beating the bot at any game. `blackjack`, `hangman`, `guess` and `minesweeper` are always against the bot. Losses, ties and expired games earn nothing. Reaching a new level posts a short announcement in the channel where the game was played. Level `n` needs `100 + 50 * n` XP to complete, and only the total is stored.

## Fun & Tools

| Command | Description | Permission |
| --- | --- | --- |
| `/8ball <question>` | Ask the magic 8-ball | Anyone |
| `/coinflip` | Flip a coin | Anyone |
| `/roll [dice]` | Roll dice like `d20`, `2d6` or `4d8+3` | Anyone |
| `/choose <a, b, c>` | Pick one option at random | Anyone |
| `/remind <duration> <text>` | Get a reminder after `30m`, `2h`, `1d`, `1h30m`, etc. | Anyone |
| `/reminders`, `/unremind <id>` | List or cancel your pending reminders | Anyone |

Reminders are saved in the database, so they survive restarts. They are posted in the channel where you set them, pinging only you, and fall back to a DM if that channel is gone. A reminder that came due while the bot was offline is delivered late with a note.

## Music

| Command | Description | Permission |
| --- | --- | --- |
| `/play <query>` | Play a link, search YouTube, or play a file from `MUSIC_DIR` | Anyone in voice |
| `/skip`, `/pause`, `/resume`, `/stop`, `/leave` | Control playback (`stop` also clears the queue) | Anyone in the bot's voice channel |
| `/join`, `/queue`, `/nowplaying` | Join your channel, show the queue, show the current track | Anyone |

## Moderation

| Command | Description | Permission |
| --- | --- | --- |
| `/kick <member> [reason]` | Kick a member | Kick Members |
| `/ban <user> [reason]`, `/unban <user> [reason]` | Ban or unban a user | Ban Members |
| `/timeout <member> <duration> [reason]` | Time a member out (`30m`, `2h`, `3d`, `1h30m`, up to 28 days) | Moderate Members |
| `/untimeout <member> [reason]` | End a timeout early | Moderate Members |
| `/warn <member> <reason>` | Warn a member and record it | Moderate Members |
| `/warnings <member>`, `/clearwarnings <member>` | Show or remove a member's warnings | Moderate Members |
| `/clear [n]` | Delete the last n messages (1 to `MAX_CLEAR_AMOUNT`, default 5) | Manage Messages |
| `/slowmode <seconds>` | Set channel slowmode (0 turns it off) | Manage Channels |
| `/lock`, `/unlock` | Stop or allow `@everyone` sending in the channel | Manage Channels |

- Every action checks the role hierarchy: you can't act on yourself, the server owner, or anyone whose top role is equal to or higher than yours or the bot's.
- Kick, ban, timeout and warn DM the member first (best effort, since closed DMs are skipped). Reasons also appear in the server's audit log.
- `unlock` resets the `@everyone` send permission to its default, which removes any explicit allow you had set on that channel.

## Info & Settings

| Command | Description | Permission |
| --- | --- | --- |
| `/userinfo [member]`, `/avatar [member]` | Member details, or their avatar at full size | Anyone |
| `/serverinfo`, `/roleinfo <role>` | Details about the server or a role | Anyone |
| `/settings` | Show this server's settings | Anyone |
| `/setvolume <0-100>` | Set the music volume for this server | Manage Server |
| `/setmodlog [channel]` | Set the channel moderation actions are logged to (empty turns it off) | Manage Server |
| `/setpresence` | Change the bot's presence | Bot owner |
| `/reload [cog]` | Reload one cog, or all of them, without restarting the bot | Bot owner |

`/reload` also loads new cog files, unloads deleted ones, and re-syncs slash commands only when they changed. If an edit has an error, the message says what failed and the previous version keeps running. Changes to `bot.py`, `config.py`, `.env`, intents, the error classes or the database stores still need a real restart. Reloading `music` disconnects it from voice.
