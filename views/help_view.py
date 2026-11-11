import logging
from collections.abc import Mapping, Sequence

import discord
from discord import ui

from views.help_data import CategoryHelp, CommandHelp
from views.style import ACCENT_COLOR, divider

log = logging.getLogger(__name__)

OVERVIEW_VALUE = "_overview"
VIEW_TIMEOUT_SECONDS = 180
SELECT_DESCRIPTION_LIMIT = 100


def command_label(command: CommandHelp, mentions: Mapping[str, str]) -> str:
    return mentions.get(command.name, f"`/{command.name}`")


def format_usage(command: CommandHelp, prefix: str) -> str:
    signature = f" {command.signature}" if command.signature else ""
    return f"`/{command.name}{signature}` · `{prefix}{command.name}{signature}`"


def format_command_block(
    command: CommandHelp, prefix: str, mentions: Mapping[str, str], heading: str
) -> str:
    lines = [
        f"{heading} {command_label(command, mentions)}",
        command.description,
        f"> **Usage** · {format_usage(command, prefix)}",
    ]
    if command.examples:
        examples = " · ".join(f"`{prefix}{example}`" for example in command.examples)
        lines.append(f"> **Examples** · {examples}")
    return "\n".join(lines)


def format_category_summary(category: CategoryHelp, mentions: Mapping[str, str]) -> str:
    names = " · ".join(command_label(command, mentions) for command in category.commands)
    lines = [f"### {category.icon} {category.name}", category.description, names]
    return "\n".join(line for line in lines if line)


def overview_items(
    categories: Sequence[CategoryHelp], prefix: str, mentions: Mapping[str, str]
) -> list[ui.Item]:
    header = f"# 📖 Help\nRun a command with `{prefix}<command>` or `/<command>`."
    footer = "-# 💡 Pick a category below, or use `/help <command>` for usage and examples."
    return [
        ui.TextDisplay(header),
        divider(),
        *(ui.TextDisplay(format_category_summary(category, mentions)) for category in categories),
        ui.TextDisplay(footer),
    ]


def category_items(
    category: CategoryHelp, prefix: str, mentions: Mapping[str, str]
) -> list[ui.Item]:
    header = f"# {category.icon} {category.name}\n{category.description}".strip()
    return [
        ui.TextDisplay(header),
        divider(),
        *(
            ui.TextDisplay(format_command_block(command, prefix, mentions, "###"))
            for command in category.commands
        ),
    ]


def build_command_view(
    command: CommandHelp, prefix: str, mentions: Mapping[str, str]
) -> ui.LayoutView:
    footer = f"-# {command.category_icon} {command.category_name}"
    view = ui.LayoutView(timeout=None)
    view.add_item(
        ui.Container(
            ui.TextDisplay(format_command_block(command, prefix, mentions, "#")),
            divider(),
            ui.TextDisplay(footer),
            accent_colour=ACCENT_COLOR,
        )
    )
    return view


class HelpView(ui.LayoutView):
    def __init__(
        self,
        categories: Sequence[CategoryHelp],
        *,
        prefix: str,
        mentions: Mapping[str, str],
        author_id: int,
    ) -> None:
        super().__init__(timeout=VIEW_TIMEOUT_SECONDS)
        self.message: discord.Message | None = None
        self._categories = {category.name: category for category in categories}
        self._prefix = prefix
        self._mentions = mentions
        self._author_id = author_id
        self._select = ui.Select(placeholder="Browse a category…")
        self._select.callback = self._on_select
        self._show(None)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id == self._author_id:
            return True
        await interaction.response.send_message(
            "This menu belongs to someone else. Run `/help` to get your own.", ephemeral=True
        )
        return False

    async def on_timeout(self) -> None:
        self._select.disabled = True
        if self.message is None:
            return
        try:
            await self.message.edit(view=self)
        except discord.HTTPException:
            log.warning("Could not disable the expired help menu", exc_info=True)

    async def _on_select(self, interaction: discord.Interaction) -> None:
        self._show(self._categories.get(self._select.values[0]))
        await interaction.response.edit_message(view=self)

    def _show(self, selected: CategoryHelp | None) -> None:
        if selected is None:
            items = overview_items(list(self._categories.values()), self._prefix, self._mentions)
        else:
            items = category_items(selected, self._prefix, self._mentions)
        self._select.options = self._build_options(selected)
        self.clear_items()
        self.add_item(
            ui.Container(
                *items,
                divider(),
                ui.ActionRow(self._select),
                accent_colour=ACCENT_COLOR,
            )
        )

    def _build_options(self, selected: CategoryHelp | None) -> list[discord.SelectOption]:
        overview = discord.SelectOption(
            label="Overview",
            value=OVERVIEW_VALUE,
            description="All categories at a glance",
            emoji="📖",
            default=selected is None,
        )
        categories = [
            discord.SelectOption(
                label=category.name,
                value=category.name,
                description=category.description[:SELECT_DESCRIPTION_LIMIT] or None,
                emoji=category.icon,
                default=category is selected,
            )
            for category in self._categories.values()
        ]
        return [overview, *categories]
