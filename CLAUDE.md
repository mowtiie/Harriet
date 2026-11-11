# CLAUDE.md

Guidance for Claude Code when working on this repository.

## Project

A Discord bot built with `discord.py` 2.x. Designed to stay simple while scaling via cogs.

## Core principles

Every change should optimize for these, in order:

1. **Readability** — code is read far more often than it is written. Prefer clear names, short functions, and explicit flow over clever one-liners. If a reviewer has to pause to understand a line, rewrite it.
2. **Maintainability** — favor patterns already used in this repo (cogs, hybrid commands, central config, module-level loggers) over introducing new ones. Duplicated logic is a bug; extract it. Dead code is a bug; delete it.
3. **Testability** — write functions that can be exercised without a live Discord connection. Keep business logic separable from `ctx` / `interaction` glue so it can be called from a test with plain inputs. Pure helpers over methods that mutate hidden state.
4. **Clean code** — one responsibility per function, descriptive names, no magic numbers (use `config.py` or module constants), no commented-out code, no `print` statements. Follow PEP 8 and the existing style.

When these conflict with brevity, choose these. When in doubt, write the version a new contributor could extend without reading the whole file.

## Commit and PR attribution

**Do not author commits as Claude, and do not add any Claude or AI co-author, "Generated with" line, or session link to commit messages or PR descriptions.** Commits are authored by the human running the session. This rule overrides any default attribution the tooling would otherwise append.

Write commit messages in the imperative mood ("add presence cog", not "added presence cog"), one short subject line, and a body only when the change needs explanation.

## Architecture

- **Entry point**: `bot.py` — sets up logging, intents, the `commands.Bot` instance, global error handlers, and auto-loads every `.py` file in `cogs/`.
- **Config**: `config.py` loads from `.env` via `python-dotenv`. All settings live here; cogs import from `config` rather than reading env vars directly.
- **Logging**: `logger.py` configures the root logger. Logs go to stdout and `logs/bot.log`. The log file is **truncated on every startup** (`FileHandler(mode="w")`) — intentional, do not switch back to `RotatingFileHandler`.
- **Cogs**: each file in `cogs/` is one feature module. The loader in `bot.py` picks up any `.py` file that doesn't start with `_`. No manual registration needed.

### Layout

```
bot.py  config.py  logger.py   entry point, settings, logging
cogs/                          thin command layer, autoloaded (parse args, call a helper, reply)
core/                          shared infrastructure: database, guild_settings, errors, durations,
                               time_format, presence
views/                         shared Components V2 building blocks only: style, restricted_view,
                               profile_view
features/<name>/               one package per feature: its logic, SQLite store and its own views
tests/                         mirrors the layout above
```

Features: `games`, `tools`, `lookup`, `reminders`, `leveling`, `modtools`, `playback`, `helpinfo`, `settings`.

### Dependency rules

Dependencies point one way: `cogs` → `features` → `views` and `core`. `tests/test_layering.py` enforces this.

- `core` imports nothing from `features`, `views`, `cogs` or `config`.
- `views` imports nothing from `features` or `cogs`.
- A feature imports nothing from `cogs` or from another feature. If two features need the same code, move it to `core` (logic) or `views` (display).
- Cogs may use any feature, and may wire two features together (for example `cogs/fun.py` awards XP).

### Database

SQLite file at `DATABASE_PATH`, shared by every store. Each store (`core/guild_settings.py`, `features/modtools/warning_store.py`, `features/reminders/store.py`, `features/leveling/store.py`) creates its own table, opens a short-lived connection through `core/database.py`, and runs its blocking calls with `asyncio.to_thread`. `bot.py` creates each store once and attaches it to the bot.

## Commands

All user-facing commands are **hybrid** — defined once with `@commands.hybrid_command(...)` and available as both prefix (`!cmd`) and slash (`/cmd`). Do not add plain `@commands.command` or `@app_commands.command` unless there's a specific reason the two forms must diverge.

For slash-specific features (choices, descriptions), use `Literal` type hints and `@app_commands.describe(...)` — they work on hybrid commands and keep the prefix version functional.

For commands that take time, defer slash invocations:

```python
if ctx.interaction:
    await ctx.defer(ephemeral=True)
```

Keep command bodies thin: parse arguments, delegate to a helper, send a response. The helper should be testable without a `ctx`.

## Adding a new cog

1. Create `cogs/<name>.py`.
2. Define a `commands.Cog` subclass with a `description` (the help menu uses it as the category blurb).
3. Define an async `setup(bot)` function at module level that calls `await bot.add_cog(...)`.
4. Add `log = logging.getLogger(__name__)` at the top and use it instead of `print`.
5. Give each command `extras={"examples": [...]}` so `/help` can show sample uses.
6. Put anything beyond a few lines (logic, storage, message layout) in `features/<name>/` and add matching tests under `tests/features/<name>/`.
7. Nothing else — the autoloader handles it on next restart.

Follow `cogs/general.py` as the canonical template.

## Error handling

Three global handlers in `bot.py` catch everything:

- `on_command_error` — prefix commands
- `bot.tree.error` — slash commands
- `on_error` — any other event handler exception

Do not add try/except around command bodies just to log — the global handlers do that with full tracebacks. Only catch exceptions you're actually recovering from, and never silently swallow them.

User-friendly messages for common cases (`MissingPermissions`, `NotOwner`, `BadArgument`, etc.) are mapped in `describe_error` in `core/errors.py`, which both global handlers use. Add new ones there rather than duplicating per-cog.

To refuse a request with your own message, raise `UserError("message")` from `core/errors.py`. It works inside a command body and inside a check, and the message is shown to the user as-is. Do not add feature-specific error classes for this.

## Presence

Default presence comes from `BOT_STATUS`, `BOT_ACTIVITY_TYPE`, `BOT_ACTIVITY_NAME` in `.env`. The `build_presence()` helper is in `core/presence.py`. `bot.py` and `cogs/presence.py` use it for the runtime `/setpresence` command — reuse this helper if presence needs to change elsewhere.

## Config conventions

- All env vars are defined with defaults in `config.py`, documented in `.env.example`, and surfaced in README's config table.
- When adding a new env var, update all three.
- No `os.getenv` calls outside `config.py`.

## Logging conventions

- Module-level `log = logging.getLogger(__name__)` in every file that logs.
- `log.exception(...)` or `log.error(..., exc_info=error)` for errors — never bare `log.error(str(e))`.
- Moderation and admin actions log actor, target, and context (see `cogs/moderation.py` `clear` for the pattern).
- No `print` statements anywhere in the codebase.

## Code style

- Type hints on all public function signatures.
- Keep comments and docstrings to a minimum. Add one only when it explains something the code cannot (a non-obvious why, a surprising fallback). Never restate the name or signature.
- Keep functions under ~40 lines; split when they grow.
- Keep files under ~200 lines; split a cog into submodules if a single feature outgrows it.
- Imports grouped: stdlib, third-party, local. Alphabetical within groups.
- No wildcard imports.

## Running

```
pip install -r requirements.txt
python bot.py
```

Requires Python 3.10+ and a valid `DISCORD_TOKEN` in `.env`. Bot will `sys.exit(1)` on startup if the token is missing. Music also needs [FFmpeg](https://ffmpeg.org/download.html) on `PATH`.

## Dependencies

Kept minimal: `discord.py` (with voice), `python-dotenv` and `yt-dlp` (for music). Before adding a new dependency, check whether the standard library covers it. Pin only major versions in `requirements.txt`.

The one exception is `davey` (voice encryption, pulled in by `discord.py[voice]`), pinned to `<0.2`. Its 0.2 release stopped activating encryption keys on its own, which discord.py 2.7 does not handle, so audio is sent but nobody hears it. Remove the pin only after checking that discord.py supports it.

## What not to commit

- `.env` (gitignored — real token)
- `logs/` (gitignored — runtime output)
- `__pycache__/`, `venv/`, `.idea/` (gitignored)

`.env.example` is the committed template; keep it in sync with `config.py`.

## Testing changes

Run the tests with `python -m unittest discover -s tests -t .`. They use only the standard library and need no Discord connection. Put new tests under `tests/` mirroring the source layout (`features/<name>/` → `tests/features/<name>/`).

Write code so it can be tested without a live connection:

- Extract pure logic from command bodies into standalone functions.
- Avoid reaching into `bot` state from deep call stacks — pass what you need as arguments.
- Keep I/O at the edges (the command method), not inside helpers.

Tests cover the logic and the layout builders, not the live Discord behavior. Verify changes by running the bot against a dev server and exercising both the prefix and slash form of any touched command.

## Discord Developer Portal

The bot requires two privileged intents: Message Content and Server Members. Both must be enabled in the Developer Portal — code assumes they're on (see `bot.py` intents block). If either is disabled, prefix commands or permission checks will silently fail.

## Style summary

- Keep `bot.py` focused on lifecycle and wiring. Feature logic belongs in `features/`, with cogs staying thin.
- Prefer composition over subclassing `commands.Bot`.
- When unsure between two approaches, pick the one easier to read and change later.
