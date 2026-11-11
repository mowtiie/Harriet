import discord
from discord import app_commands
from discord.ext import commands

from utilities.profile import avatar_urls, role_fields, server_fields, user_fields
from views.profile_view import build_avatar_view, build_profile_view
from views.style import NO_MENTIONS


class Information(
    commands.Cog, description="Look up details about members, roles and the server."
):
    @commands.hybrid_command(
        name="userinfo",
        description="Show details about a member",
        extras={"examples": ["userinfo", "userinfo @user"]},
    )
    @commands.guild_only()
    @app_commands.describe(member="Member to look up (defaults to you)")
    async def userinfo(
        self, ctx: commands.Context, member: discord.Member | None = None
    ) -> None:
        member = member or ctx.author
        view = build_profile_view(
            member.display_name, str(member), user_fields(member), member.display_avatar.url
        )
        await ctx.send(view=view, allowed_mentions=NO_MENTIONS)

    @commands.hybrid_command(
        name="serverinfo",
        description="Show details about this server",
        extras={"examples": ["serverinfo"]},
    )
    @commands.guild_only()
    async def serverinfo(self, ctx: commands.Context) -> None:
        guild = ctx.guild
        icon_url = guild.icon.url if guild.icon else None
        view = build_profile_view(guild.name, "Server", server_fields(guild), icon_url)
        await ctx.send(view=view, allowed_mentions=NO_MENTIONS)

    @commands.hybrid_command(
        name="avatar",
        description="Show a member's avatar at full size",
        extras={"examples": ["avatar", "avatar @user"]},
    )
    @commands.guild_only()
    @app_commands.describe(member="Member to look up (defaults to you)")
    async def avatar(self, ctx: commands.Context, member: discord.Member | None = None) -> None:
        member = member or ctx.author
        await ctx.send(view=build_avatar_view(member.display_name, avatar_urls(member)))

    @commands.hybrid_command(
        name="roleinfo",
        description="Show details about a role",
        extras={"examples": ["roleinfo @Moderators"]},
    )
    @commands.guild_only()
    @app_commands.describe(role="Role to look up")
    async def roleinfo(self, ctx: commands.Context, role: discord.Role) -> None:
        view = build_profile_view(role.name, "Role", role_fields(role))
        await ctx.send(view=view, allowed_mentions=NO_MENTIONS)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Information())
