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
| `/cookie` | Work out who stole Harriet's cookie from logic clues, with friends or on your own | Anyone |
| `/blackjack` | Blackjack against the bot as the dealer (hit or stand; the dealer stands on 17) | Anyone |
| `/hangman` | Guess a random word one letter at a time before the drawing is finished | Anyone |
| `/guess` | Guess my number from 1 to 100 in 8 tries, with higher or lower hints | Anyone |
| `/minesweeper` | Clear a 5×5 field with 5 hidden mines (the first square is always safe) | Anyone |
| `/rank [member]` | Show a member's level, XP and server rank | Anyone |
| `/leaderboard` | Show the server's XP leaderboard | Anyone |
| `/setxp <member> <amount>`, `/resetxp <member>` | Set or clear a member's XP | Manage Server |

Games are played with buttons (letter menus for `hangman`, a pop-up form for `guess`) and only the players can use them. They live in memory and end after `GAME_TIMEOUT_SECONDS` of inactivity, so a restart ends any game in progress.

**Battleship.** Each side gets a random fleet of three ships (3, 2 and 2 squares) on a 5×5 board, and players take turns firing at squares like `B3`. The message only shows hits (💥), sunk ships (🔥) and misses (🌊). Press **My fleet** to see your own board privately. Against the bot, it fires back right after each of your shots.

**The cookie mystery.** Everyone who presses **Join** becomes a detective and a suspect, and fictional characters fill the remaining seats up to five. Harriet makes up a new case each time: the suspects stood in different rooms along a corridor, and whoever was in the room with the cookie jar is the thief. Clues come out one at a time with **Next clue**, and the case is built so that after the last clue only one suspect fits. Each detective gets one accusation from the menu. A wrong one knocks you out, and the first correct one wins. If everyone is wrong, Harriet wins. The message then shows what really happened. A case goes cold after `COOKIE_CASE_TIMEOUT_SECONDS` of inactivity.

**XP and levels.** XP comes only from winning: `XP_PER_WIN` for beating another member at `rps`, `tictactoe`, `connectfour` or `battleship`, and the smaller `XP_PER_BOT_WIN` for beating the bot at any game. `blackjack`, `hangman`, `guess`, `minesweeper` and `cookie` are always against the bot, so the first detective to solve a cookie case earns `XP_PER_BOT_WIN`. Losses, ties and expired games earn nothing. Reaching a new level posts a short announcement in the channel where the game was played. Level `n` needs `100 + 50 * n` XP to complete, and only the total is stored.

## Fun & Tools

| Command | Description | Permission |
| --- | --- | --- |
| `/8ball <question>` | Ask the magic 8-ball | Anyone |
| `/coinflip` | Flip a coin | Anyone |
| `/roll [dice]` | Roll dice like `d20`, `2d6` or `4d8+3` | Anyone |
| `/choose <a, b, c>` | Pick one option at random | Anyone |
| `/time <when> [timezone]` | Turn a time like `tomorrow 8pm London` into a link everyone sees in their own timezone | Anyone |
| `/remind <duration> <text>` | Get a reminder after `30m`, `2h`, `1d`, `1h30m`, etc. | Anyone |
| `/reminders`, `/unremind <id>` | List or cancel your pending reminders | Anyone |

**Time.** Write the time and then the timezone, all in one go: `/time tomorrow 8pm London`. It understands `8pm`, `20:45`, `noon`, `tomorrow`, weekdays like `friday 18:30`, dates like `2026-12-25 09:00`, and `in 2h30m`. The timezone can be a city (`London`, `New York`), a name (`Europe/London`), an abbreviation (`EST`, `PST`) or an offset (`UTC+2`), and defaults to UTC. Harriet replies with a Discord timestamp that shows in each reader's own timezone, plus codes to copy and paste elsewhere.

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
| `/say [channel] <message>` | Make the bot send a message, here or in another channel | Manage Messages |
| `/slowmode <seconds>` | Set channel slowmode (0 turns it off) | Manage Channels |
| `/lock`, `/unlock` | Stop or allow `@everyone` sending in the channel | Manage Channels |

- Every action checks the role hierarchy: you can't act on yourself, the server owner, or anyone whose top role is equal to or higher than yours or the bot's.
- Kick, ban, timeout and warn DM the member first (best effort, since closed DMs are skipped). Reasons also appear in the server's audit log.
- `/say` posts as the bot, with nothing showing who ran it, but every use is logged in the bot log and the mod-log channel with who said what and where. You can only use it in channels you could post in yourself. Type `\n` for a line break. `@everyone`, `@here` and role pings only work if you have the Mention Everyone permission, and there is a 5-second cooldown. With the prefix, the bot deletes your command message afterwards if it can.
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
| `/status` | Uptime, version, games in progress, errors since start and more | Bot owner |
| `/logs [lines] [all\|errors]` | Show the end of the log (default 25 lines), or only the errors | Bot owner |
| `/backup` | Send you a copy of the database | Bot owner |

The owner commands answer privately. Used with the prefix, `/status`, `/logs` and `/backup` DM you instead, because a reply in the channel would be public.

`/status` shows the commit you're running, and the one you started on if they differ, so you can tell whether a restart or `/reload` is still needed. `/logs` shows long output as a file, and the log is cleared on every start, so `/logs errors` means errors since then. `/backup` takes a consistent snapshot of the SQLite file without touching the original.

`/reload` also loads new cog files, unloads deleted ones, and re-syncs slash commands only when they changed. If an edit has an error, the message says what failed and the previous version keeps running. Changes to `bot.py`, `config.py`, `.env`, intents, the error classes or the database stores still need a real restart. Reloading `music` disconnects it from voice.
