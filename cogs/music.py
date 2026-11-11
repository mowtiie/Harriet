import logging
from functools import partial

import discord
from discord import app_commands
from discord.ext import commands

import config
from core.guild_settings import VOLUME_KEY
from features.playback.checks import in_voice_channel, with_active_player
from features.playback.errors import QueueFullError, ResolveError
from features.playback.music_view import build_added_view, build_now_playing_view, build_queue_view
from features.playback.player import GuildPlayer, is_ffmpeg_available
from features.playback.queue import MusicQueue
from features.playback.resolver import matching_local_names, resolve_track

log = logging.getLogger(__name__)

AUTOCOMPLETE_LIMIT = 25
FFMPEG_MISSING_MESSAGE = "FFmpeg is not installed on the host, so I can't play audio."
NOTHING_PLAYING_MESSAGE = "Nothing is playing."


class Music(commands.Cog, description="Play music in voice channels."):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self._players: dict[int, GuildPlayer] = {}
        if not is_ffmpeg_available():
            log.warning("FFmpeg was not found on PATH; music commands will not work")

    async def cog_unload(self) -> None:
        for player in list(self._players.values()):
            await player.disconnect()

    @commands.Cog.listener()
    async def on_voice_state_update(
        self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState
    ) -> None:
        player = self._players.get(member.guild.id)
        if player is None:
            return
        if member.id == self.bot.user.id and after.channel is None:
            self._players.pop(member.guild.id, None)
        elif all(m.bot for m in player.voice_client.channel.members):
            await player.disconnect()

    @commands.hybrid_command(
        name="join", description="Join your voice channel", extras={"examples": ["join"]}
    )
    @commands.guild_only()
    @in_voice_channel()
    async def join(self, ctx: commands.Context) -> None:
        player = await self._get_or_create_player(ctx)
        await ctx.send(f"Joined {player.voice_client.channel.mention}.")

    @commands.hybrid_command(
        name="play",
        description="Play a link, search YouTube, or play a file from the music folder",
        extras={"examples": ["play lofi hip hop", "play https://youtu.be/dQw4w9WgXcQ", "play song.mp3"]},
    )
    @commands.guild_only()
    @in_voice_channel()
    @app_commands.describe(query="A link, a search, or a file name from the music folder")
    async def play(self, ctx: commands.Context, *, query: str) -> None:
        if not is_ffmpeg_available():
            await ctx.send(FFMPEG_MISSING_MESSAGE, ephemeral=True)
            return
        if ctx.interaction:
            await ctx.defer()

        try:
            track = await resolve_track(query, config.MUSIC_DIR, ctx.author.display_name)
            player = await self._get_or_create_player(ctx)
            starts_now = not player.is_active
            position = player.queue.add(track)
        except (ResolveError, QueueFullError) as error:
            await ctx.send(str(error), ephemeral=True)
            return

        view = build_now_playing_view(track) if starts_now else build_added_view(track, position)
        await ctx.send(view=view)
        await player.start_if_idle()

    @play.autocomplete("query")
    async def autocomplete_query(
        self, interaction: discord.Interaction, current: str
    ) -> list[app_commands.Choice[str]]:
        names = matching_local_names(config.MUSIC_DIR, current, AUTOCOMPLETE_LIMIT)
        return [app_commands.Choice(name=name, value=name) for name in names]

    @commands.hybrid_command(
        name="skip", description="Skip the current track", extras={"examples": ["skip"]}
    )
    @commands.guild_only()
    @with_active_player()
    async def skip(self, ctx: commands.Context) -> None:
        player = self._players.get(ctx.guild.id)
        if player is None or not player.is_active:
            await ctx.send(NOTHING_PLAYING_MESSAGE, ephemeral=True)
            return
        title = player.queue.current.title
        player.skip()
        await ctx.send(f"Skipped **{title}**.")

    @commands.hybrid_command(
        name="pause", description="Pause playback", extras={"examples": ["pause"]}
    )
    @commands.guild_only()
    @with_active_player()
    async def pause(self, ctx: commands.Context) -> None:
        player = self._players.get(ctx.guild.id)
        if player is None or not player.voice_client.is_playing():
            await ctx.send(NOTHING_PLAYING_MESSAGE, ephemeral=True)
            return
        player.pause()
        await ctx.send("Paused.")

    @commands.hybrid_command(
        name="resume", description="Resume playback", extras={"examples": ["resume"]}
    )
    @commands.guild_only()
    @with_active_player()
    async def resume(self, ctx: commands.Context) -> None:
        player = self._players.get(ctx.guild.id)
        if player is None or not player.voice_client.is_paused():
            await ctx.send("Nothing is paused.", ephemeral=True)
            return
        player.resume()
        await ctx.send("Resumed.")

    @commands.hybrid_command(
        name="stop", description="Stop playback and clear the queue", extras={"examples": ["stop"]}
    )
    @commands.guild_only()
    @with_active_player()
    async def stop(self, ctx: commands.Context) -> None:
        player = self._players.get(ctx.guild.id)
        if player is not None:
            player.stop()
        await ctx.send("Stopped and cleared the queue.")

    @commands.hybrid_command(
        name="leave", description="Leave the voice channel", extras={"examples": ["leave"]}
    )
    @commands.guild_only()
    @with_active_player()
    async def leave(self, ctx: commands.Context) -> None:
        player = self._players.get(ctx.guild.id)
        if player is not None:
            await player.disconnect()
        await ctx.send("Left the voice channel.")

    @commands.hybrid_command(
        name="queue", description="Show the current queue", extras={"examples": ["queue"]}
    )
    @commands.guild_only()
    async def queue(self, ctx: commands.Context) -> None:
        player = self._players.get(ctx.guild.id)
        if player is None:
            await ctx.send(NOTHING_PLAYING_MESSAGE, ephemeral=True)
            return
        await ctx.send(view=build_queue_view(player.queue.current, player.queue.upcoming))

    @commands.hybrid_command(
        name="nowplaying",
        description="Show the track that is playing",
        extras={"examples": ["nowplaying"]},
    )
    @commands.guild_only()
    async def nowplaying(self, ctx: commands.Context) -> None:
        player = self._players.get(ctx.guild.id)
        if player is None or player.queue.current is None:
            await ctx.send(NOTHING_PLAYING_MESSAGE, ephemeral=True)
            return
        await ctx.send(view=build_now_playing_view(player.queue.current))

    async def _get_or_create_player(self, ctx: commands.Context) -> GuildPlayer:
        player = self._players.get(ctx.guild.id)
        if player is not None:
            return player
        voice_client = ctx.guild.voice_client or await ctx.author.voice.channel.connect()
        player = GuildPlayer(
            voice_client,
            MusicQueue(config.MAX_QUEUE_SIZE),
            partial(
                self.bot.guild_settings.get_int, ctx.guild.id, VOLUME_KEY, config.DEFAULT_VOLUME
            ),
            config.MUSIC_IDLE_TIMEOUT_SECONDS,
        )
        self._players[ctx.guild.id] = player
        return player


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Music(bot))
