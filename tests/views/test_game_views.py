"""Tests for the interactive game views using fake interactions."""

import unittest
from types import SimpleNamespace
from unittest import mock

from games.rps import Move, RpsGame
from games.tictactoe import TicTacToeGame
from views.rps_view import RpsView, describe_result
from views.tictactoe_view import TicTacToeView, status_text

ALICE, BOB, BOT, STRANGER = 1, 2, 3, 4
NAMES = {ALICE: "Alice", BOB: "Bob", BOT: "Harriet"}


def make_interaction(user_id: int) -> mock.Mock:
    interaction = mock.Mock()
    interaction.user = SimpleNamespace(id=user_id)
    interaction.response.send_message = mock.AsyncMock()
    interaction.response.edit_message = mock.AsyncMock()
    return interaction


class FixedRng:
    def __init__(self, move: Move) -> None:
        self._move = move

    def choice(self, _options: list[Move]) -> Move:
        return self._move


def make_rps_view(opponent_id: int, vs_bot: bool, bot_move: Move = Move.SCISSORS) -> RpsView:
    return RpsView(
        RpsGame(ALICE, opponent_id),
        NAMES,
        human_ids=(ALICE,) if vs_bot else (ALICE, opponent_id),
        bot_id=opponent_id if vs_bot else None,
        rng=FixedRng(bot_move),
        timeout_seconds=60,
    )


class RpsViewAgainstBotTests(unittest.IsolatedAsyncioTestCase):
    async def test_one_pick_finishes_the_game(self) -> None:
        view = make_rps_view(BOT, vs_bot=True, bot_move=Move.SCISSORS)
        interaction = make_interaction(ALICE)
        await view._on_pick(Move.ROCK, interaction)
        interaction.response.edit_message.assert_awaited_once()
        self.assertEqual(view._game.winner_id, ALICE)
        self.assertTrue(view.is_finished())

    async def test_result_text_names_both_picks_and_the_winner(self) -> None:
        game = RpsGame(ALICE, BOT)
        game.pick(ALICE, Move.ROCK)
        game.pick(BOT, Move.PAPER)
        self.assertEqual(
            describe_result(game, NAMES).splitlines(),
            ["**Alice** picked Rock", "**Harriet** picked Paper", "**Harriet** wins."],
        )


class RecordingHandler:
    def __init__(self, note: str | None = "+50 XP") -> None:
        self.winners: list[int | None] = []
        self._note = note

    async def __call__(self, winner_id: int | None) -> str | None:
        self.winners.append(winner_id)
        return self._note


def notes_in(view: object) -> list[str]:
    return [item.content for item in view.walk_children() if hasattr(item, "content")]


class WinHandlerTests(unittest.IsolatedAsyncioTestCase):
    async def test_rps_reports_the_winner_and_shows_the_note(self) -> None:
        handler = RecordingHandler()
        view = make_rps_view(BOT, vs_bot=True, bot_move=Move.SCISSORS)
        view._on_finish = handler
        await view._on_pick(Move.ROCK, make_interaction(ALICE))
        self.assertEqual(handler.winners, [ALICE])
        self.assertIn("-# +50 XP", notes_in(view))

    async def test_rps_reports_the_bot_as_winner_too(self) -> None:
        handler = RecordingHandler(note=None)
        view = make_rps_view(BOT, vs_bot=True, bot_move=Move.PAPER)
        view._on_finish = handler
        await view._on_pick(Move.ROCK, make_interaction(ALICE))
        self.assertEqual(handler.winners, [BOT])
        self.assertFalse([text for text in notes_in(view) if text.startswith("-#")])

    async def test_rps_tie_reports_no_winner(self) -> None:
        handler = RecordingHandler(note=None)
        view = make_rps_view(BOT, vs_bot=True, bot_move=Move.ROCK)
        view._on_finish = handler
        await view._on_pick(Move.ROCK, make_interaction(ALICE))
        self.assertEqual(handler.winners, [None])

    async def test_unfinished_rps_does_not_report(self) -> None:
        handler = RecordingHandler()
        view = make_rps_view(BOB, vs_bot=False)
        view._on_finish = handler
        await view._on_pick(Move.ROCK, make_interaction(ALICE))
        self.assertEqual(handler.winners, [])

    async def test_tictactoe_reports_only_when_the_game_ends(self) -> None:
        handler = RecordingHandler()
        view = TicTacToeView(TicTacToeGame(ALICE, BOB), NAMES, 60, handler)
        for user, square in ((ALICE, 0), (BOB, 3), (ALICE, 1), (BOB, 4)):
            await view._on_press(square, make_interaction(user))
        self.assertEqual(handler.winners, [])
        await view._on_press(2, make_interaction(ALICE))
        self.assertEqual(handler.winners, [ALICE])
        self.assertIn("-# +50 XP", notes_in(view))

    async def test_a_game_without_a_handler_still_works(self) -> None:
        view = make_rps_view(BOT, vs_bot=True)
        await view._on_pick(Move.ROCK, make_interaction(ALICE))
        self.assertTrue(view.is_finished())


class RpsViewAgainstMemberTests(unittest.IsolatedAsyncioTestCase):
    async def test_first_pick_is_private_and_second_reveals_the_result(self) -> None:
        view = make_rps_view(BOB, vs_bot=False)
        first, second = make_interaction(ALICE), make_interaction(BOB)

        await view._on_pick(Move.ROCK, first)
        first.response.send_message.assert_awaited_once()
        self.assertTrue(first.response.send_message.await_args.kwargs["ephemeral"])
        first.response.edit_message.assert_not_awaited()
        self.assertFalse(view._game.is_finished)

        await view._on_pick(Move.PAPER, second)
        second.response.edit_message.assert_awaited_once()
        self.assertEqual(view._game.winner_id, BOB)

    async def test_picking_twice_is_refused_privately(self) -> None:
        view = make_rps_view(BOB, vs_bot=False)
        await view._on_pick(Move.ROCK, make_interaction(ALICE))
        again = make_interaction(ALICE)
        await view._on_pick(Move.PAPER, again)
        self.assertIn("already", again.response.send_message.await_args.args[0])
        self.assertEqual(view._game.move_of(ALICE), Move.ROCK)

    async def test_only_the_players_may_press(self) -> None:
        view = make_rps_view(BOB, vs_bot=False)
        self.assertTrue(await view.interaction_check(make_interaction(BOB)))
        outsider = make_interaction(STRANGER)
        self.assertFalse(await view.interaction_check(outsider))
        outsider.response.send_message.assert_awaited_once()


class TicTacToeViewTests(unittest.IsolatedAsyncioTestCase):
    def make_view(self) -> TicTacToeView:
        return TicTacToeView(TicTacToeGame(ALICE, BOB), NAMES, timeout_seconds=60)

    async def test_move_updates_the_board_and_message(self) -> None:
        view = self.make_view()
        interaction = make_interaction(ALICE)
        await view._on_press(4, interaction)
        self.assertEqual(view._game.board[4], "X")
        interaction.response.edit_message.assert_awaited_once()

    async def test_out_of_turn_press_is_refused_privately(self) -> None:
        view = self.make_view()
        interaction = make_interaction(BOB)
        await view._on_press(0, interaction)
        self.assertEqual(view._game.board[0], "")
        self.assertTrue(interaction.response.send_message.await_args.kwargs["ephemeral"])

    async def test_game_stops_when_someone_wins(self) -> None:
        view = self.make_view()
        for user, square in ((ALICE, 0), (BOB, 3), (ALICE, 1), (BOB, 4), (ALICE, 2)):
            await view._on_press(square, make_interaction(user))
        self.assertEqual(view._game.winner_id, ALICE)
        self.assertTrue(view.is_finished())

    async def test_timeout_locks_the_board_and_edits_the_message(self) -> None:
        view = self.make_view()
        view.message = mock.Mock(edit=mock.AsyncMock())
        await view.on_timeout()
        view.message.edit.assert_awaited_once()
        buttons = [item for item in view.walk_children() if hasattr(item, "disabled")]
        self.assertTrue(buttons)
        self.assertTrue(all(button.disabled for button in buttons))


class StatusTextTests(unittest.TestCase):
    def test_turn_win_draw_and_timeout(self) -> None:
        game = TicTacToeGame(ALICE, BOB)
        self.assertEqual(status_text(game, NAMES, False), "**Alice**'s turn (X).")
        self.assertIn("didn't move in time", status_text(game, NAMES, True))

        won = TicTacToeGame(ALICE, BOB)
        for user, square in ((ALICE, 0), (BOB, 3), (ALICE, 1), (BOB, 4), (ALICE, 2)):
            won.play(user, square)
        self.assertEqual(status_text(won, NAMES, False), "**Alice** wins.")

        drawn = TicTacToeGame(ALICE, BOB)
        for number, square in enumerate((0, 1, 2, 4, 3, 5, 7, 6, 8)):
            drawn.play(ALICE if number % 2 == 0 else BOB, square)
        self.assertEqual(status_text(drawn, NAMES, False), "It's a draw.")


if __name__ == "__main__":
    unittest.main()
