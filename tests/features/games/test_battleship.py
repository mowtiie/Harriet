"""Tests for battleship rules, the bot player and the view."""

import random
import unittest
from unittest import mock

from discord import ui

from features.games.battleship import (
    FLEET_SIZES,
    SIZE,
    SQUARES,
    BattleshipGame,
    Board,
    new_battleship_game,
    orthogonal_neighbors,
    place_fleet,
    square_name,
)
from features.games.battleship_bot import pick_target
from features.games.battleship_view import (
    HIT,
    MISS,
    SHIP,
    SUNK,
    BattleshipView,
    describe_shot,
    own_fleet_text,
    status_text,
)
from features.games.errors import GameError
from tests.features.games.test_game_views import RecordingHandler, make_interaction, notes_in

ALICE, BOB, BOT = 1, 2, 3
NAMES = {ALICE: "Alice", BOB: "Bob", BOT: "Harriet"}
COMPONENT_LIMIT = 40

# Bob's ships: a 3-square ship on A1-C1, and two 2-square ships.
BOB_FLEET = [frozenset({0, 1, 2}), frozenset({10, 15}), frozenset({22, 23})]
# Alice's ships sit on the other side of the board.
ALICE_FLEET = [frozenset({4, 9, 14}), frozenset({20, 21}), frozenset({12, 17})]


def new_game() -> BattleshipGame:
    return BattleshipGame(ALICE, BOB, ALICE_FLEET, BOB_FLEET)


def sink_bobs_fleet(game: BattleshipGame) -> None:
    """Alice fires at every one of Bob's ship squares, while Bob wastes shots on water."""
    bobs_squares = sorted(square for ship in BOB_FLEET for square in ship)
    wasted = iter([5, 6, 7, 8, 11, 13, 16])
    for number, square in enumerate(bobs_squares):
        game.play(ALICE, square)
        if number < len(bobs_squares) - 1:
            game.play(BOB, next(wasted))


def make_view(game: BattleshipGame | None = None, bot_id: int | None = None, handler=None):
    game = game or new_game()
    return BattleshipView(game, NAMES, 60, handler, bot_id=bot_id, rng=random.Random(0))


def buttons_in(view: BattleshipView) -> list[ui.Button]:
    return [item for item in view.walk_children() if isinstance(item, ui.Button)]


class NamingTests(unittest.TestCase):
    def test_squares_are_named_column_letter_then_row_number(self) -> None:
        self.assertEqual(square_name(0), "A1")
        self.assertEqual(square_name(SIZE - 1), "E1")
        self.assertEqual(square_name(SQUARES - 1), "E5")
        self.assertEqual(square_name(7), "C2")

    def test_orthogonal_neighbours_stay_on_the_board(self) -> None:
        self.assertEqual(sorted(orthogonal_neighbors(0)), [1, 5])
        self.assertEqual(sorted(orthogonal_neighbors(12)), [7, 11, 13, 17])
        self.assertEqual(sorted(orthogonal_neighbors(4)), [3, 9])


class FleetPlacementTests(unittest.TestCase):
    def test_random_fleets_are_valid_for_many_seeds(self) -> None:
        for seed in range(300):
            fleet = place_fleet(random.Random(seed))
            with self.subTest(seed=seed):
                self.assertEqual(sorted(len(ship) for ship in fleet), sorted(FLEET_SIZES))
                squares = [square for ship in fleet for square in ship]
                self.assertEqual(len(squares), len(set(squares)))
                self.assertTrue(all(0 <= square < SQUARES for square in squares))
                for ship in fleet:
                    rows = {square // SIZE for square in ship}
                    columns = {square % SIZE for square in ship}
                    self.assertTrue(len(rows) == 1 or len(columns) == 1)

    def test_ships_are_straight_and_unbroken(self) -> None:
        for seed in range(100):
            for ship in place_fleet(random.Random(seed)):
                ordered = sorted(ship)
                gaps = {b - a for a, b in zip(ordered, ordered[1:])}
                self.assertIn(gaps, ({1}, {SIZE}))


class BoardTests(unittest.TestCase):
    def test_a_miss_and_a_hit(self) -> None:
        board = Board(BOB_FLEET)
        self.assertFalse(board.fire(24).hit)
        result = board.fire(0)
        self.assertTrue(result.hit)
        self.assertIsNone(result.sunk_size)
        self.assertEqual(board.hit_squares, {0})
        self.assertEqual(board.live_hits, {0})

    def test_the_last_hit_on_a_ship_sinks_it_and_reports_its_size(self) -> None:
        board = Board(BOB_FLEET)
        board.fire(22)
        self.assertEqual(board.fire(23).sunk_size, 2)
        self.assertEqual(board.sunk_squares, {22, 23})
        self.assertEqual(board.live_hits, frozenset())
        self.assertEqual(board.ships_afloat, 2)

    def test_the_same_square_cannot_be_shot_twice(self) -> None:
        board = Board(BOB_FLEET)
        board.fire(0)
        with self.assertRaises(GameError) as caught:
            board.fire(0)
        self.assertIn("A1", str(caught.exception))
        self.assertEqual(len(board.shots), 1)

    def test_the_board_falls_when_every_ship_is_sunk(self) -> None:
        board = Board(BOB_FLEET)
        for square in (0, 1, 2, 10, 15, 22):
            board.fire(square)
        self.assertFalse(board.is_defeated)
        board.fire(23)
        self.assertTrue(board.is_defeated)


class BattleshipGameTests(unittest.TestCase):
    def test_first_player_fires_first_at_the_other_board(self) -> None:
        game = new_game()
        self.assertEqual(game.current_player_id, ALICE)
        game.play(ALICE, 0)
        self.assertEqual(game.board_of(BOB).shots, {0})
        self.assertEqual(game.board_of(ALICE).shots, frozenset())

    def test_turns_alternate_even_after_a_hit(self) -> None:
        game = new_game()
        self.assertTrue(game.play(ALICE, 0).hit)
        self.assertEqual(game.current_player_id, BOB)
        game.play(BOB, 24)
        self.assertEqual(game.current_player_id, ALICE)

    def test_wrong_player_cannot_fire(self) -> None:
        game = new_game()
        with self.assertRaises(GameError):
            game.play(BOB, 0)
        with self.assertRaises(GameError):
            game.play(99, 0)
        self.assertEqual(game.history, [])

    def test_a_repeat_shot_is_refused_and_keeps_the_turn(self) -> None:
        game = new_game()
        game.play(ALICE, 24)
        game.play(BOB, 24)
        with self.assertRaises(GameError):
            game.play(ALICE, 24)
        self.assertEqual(game.current_player_id, ALICE)

    def test_history_records_every_shot_in_order(self) -> None:
        game = new_game()
        game.play(ALICE, 0)
        game.play(BOB, 24)
        self.assertEqual([(s.player_id, s.index) for s in game.history], [(ALICE, 0), (BOB, 24)])

    def test_sinking_every_ship_wins_and_ends_the_game(self) -> None:
        game = new_game()
        sink_bobs_fleet(game)
        self.assertTrue(game.is_over)
        self.assertEqual(game.winner_id, ALICE)
        with self.assertRaises(GameError):
            game.play(BOB, 5)

    def test_no_winner_while_ships_remain(self) -> None:
        game = new_game()
        game.play(ALICE, 0)
        self.assertIsNone(game.winner_id)
        self.assertFalse(game.is_over)

    def test_new_games_get_independent_random_fleets(self) -> None:
        game = new_battleship_game(ALICE, BOB, random.Random(5))
        self.assertEqual(len(game.board_of(ALICE).ship_squares), sum(FLEET_SIZES))
        self.assertEqual(len(game.board_of(BOB).ship_squares), sum(FLEET_SIZES))


class BotTests(unittest.TestCase):
    def test_follows_up_next_to_a_damaged_ship(self) -> None:
        board = Board(BOB_FLEET)
        board.fire(0)
        for seed in range(30):
            self.assertIn(pick_target(board, random.Random(seed)), (1, 5))

    def test_goes_back_to_searching_once_a_ship_is_sunk(self) -> None:
        board = Board(BOB_FLEET)
        board.fire(22)
        board.fire(23)
        self.assertEqual(board.live_hits, frozenset())
        for seed in range(30):
            target = pick_target(board, random.Random(seed))
            self.assertNotIn(target, board.shots)
            self.assertEqual(sum(divmod(target, SIZE)) % 2, 0)

    def test_searches_on_a_checkerboard_when_nothing_is_hit(self) -> None:
        board = Board(BOB_FLEET)
        for seed in range(30):
            target = pick_target(board, random.Random(seed))
            self.assertEqual(sum(divmod(target, SIZE)) % 2, 0)

    def test_never_fires_at_a_square_twice_and_always_finishes_the_game(self) -> None:
        for seed in range(100):
            board = Board(place_fleet(random.Random(seed)))
            rng = random.Random(seed)
            fired = 0
            while not board.is_defeated:
                board.fire(pick_target(board, rng))
                fired += 1
                self.assertLessEqual(fired, SQUARES)

    def test_needs_clearly_fewer_shots_than_firing_at_random(self) -> None:
        def random_target(board: Board, rng: random.Random) -> int:
            return rng.choice([index for index in range(SQUARES) if index not in board.shots])

        def average_shots(strategy) -> float:
            total = 0
            for seed in range(200):
                board = Board(place_fleet(random.Random(seed)))
                rng = random.Random(seed + 1000)
                while not board.is_defeated:
                    board.fire(strategy(board, rng))
                total += len(board.shots)
            return total / 200

        self.assertLess(average_shots(pick_target), average_shots(random_target) - 3)


class DisplayTests(unittest.TestCase):
    def test_shot_descriptions(self) -> None:
        game = new_game()
        game.play(ALICE, 24)
        game.play(BOB, 4)
        game.play(ALICE, 22)
        game.play(BOB, 9)
        game.play(ALICE, 23)
        lines = [describe_shot(shot, NAMES) for shot in game.history]
        self.assertEqual(lines[0], "**Alice** fired at `E5`: miss.")
        self.assertEqual(lines[1], "**Bob** fired at `E1`: hit!")
        self.assertEqual(lines[4], "**Alice** fired at `D5`: hit and sunk a 2-square ship!")

    def test_status_covers_turn_win_and_timeout(self) -> None:
        game = new_game()
        self.assertEqual(
            status_text(game, NAMES, False), "**Alice**'s turn. Fire at **Bob**'s waters."
        )
        self.assertIn("didn't fire in time", status_text(game, NAMES, True))
        sink_bobs_fleet(game)
        self.assertEqual(
            status_text(game, NAMES, False), "**Alice** sank the whole fleet and wins."
        )

    def test_own_fleet_shows_ships_hits_and_incoming_misses(self) -> None:
        game = new_game()
        game.play(ALICE, 24)
        game.play(BOB, 4)
        game.play(ALICE, 0)
        game.play(BOB, 0)
        text = own_fleet_text(game.board_of(ALICE))
        self.assertEqual(text.count(HIT), 1)
        self.assertEqual(text.count(MISS), 1)
        self.assertEqual(text.count(SHIP), 6)
        self.assertIn("ship(s) afloat", text)


class BattleshipViewTests(unittest.IsolatedAsyncioTestCase):
    async def test_a_shot_updates_the_game_and_the_message(self) -> None:
        view = make_view()
        interaction = make_interaction(ALICE)
        await view._on_press(0, interaction)
        interaction.response.edit_message.assert_awaited_once()
        self.assertEqual(view._game.board_of(BOB).shots, {0})
        self.assertEqual(view._game.current_player_id, BOB)

    async def test_an_out_of_turn_press_is_refused_privately(self) -> None:
        view = make_view()
        interaction = make_interaction(BOB)
        await view._on_press(0, interaction)
        self.assertEqual(view._game.history, [])
        self.assertTrue(interaction.response.send_message.await_args.kwargs["ephemeral"])

    async def test_the_grid_shows_the_waters_the_current_player_is_firing_at(self) -> None:
        view = make_view()
        await view._on_press(0, make_interaction(ALICE))
        await view._on_press(4, make_interaction(BOB))
        grid = [button for button in buttons_in(view) if button.label != "My fleet"]
        self.assertEqual(len(grid), SQUARES)
        self.assertEqual(str(grid[0].emoji), HIT)
        self.assertIsNone(grid[0].label)
        self.assertEqual(grid[1].label, "B1")

    async def test_unshot_squares_never_reveal_where_ships_are(self) -> None:
        view = make_view()
        grid = [button for button in buttons_in(view) if button.label != "My fleet"]
        self.assertTrue(all(button.emoji is None for button in grid))
        self.assertEqual([button.label for button in grid[:5]], ["A1", "B1", "C1", "D1", "E1"])

    async def test_sunk_ships_look_different_from_single_hits(self) -> None:
        view = make_view()
        for user, square in ((ALICE, 22), (BOB, 5), (ALICE, 23), (BOB, 6)):
            await view._on_press(square, make_interaction(user))
        grid = [button for button in buttons_in(view) if button.label != "My fleet"]
        self.assertEqual(str(grid[22].emoji), SUNK)
        self.assertEqual(str(grid[23].emoji), SUNK)

    async def test_my_fleet_is_private_and_shows_only_your_own_ships(self) -> None:
        view = make_view()
        interaction = make_interaction(ALICE)
        await view._on_fleet(interaction)
        kwargs = interaction.response.send_message.await_args.kwargs
        text = interaction.response.send_message.await_args.args[0]
        self.assertTrue(kwargs["ephemeral"])
        self.assertEqual(text.count(SHIP), sum(FLEET_SIZES))
        first_row = text.splitlines()[2]
        self.assertEqual(first_row.count(SHIP), 1)

    async def test_winning_reports_the_winner_and_shows_the_note(self) -> None:
        handler = RecordingHandler()
        view = make_view(handler=handler)
        bobs_squares = sorted(square for ship in BOB_FLEET for square in ship)
        wasted = iter([5, 6, 7, 8, 11, 13, 16])
        for number, square in enumerate(bobs_squares):
            await view._on_press(square, make_interaction(ALICE))
            if number < len(bobs_squares) - 1:
                await view._on_press(next(wasted), make_interaction(BOB))
        self.assertEqual(handler.winners, [ALICE])
        self.assertTrue(view.is_finished())
        self.assertIn("-# +50 XP", notes_in(view))
        self.assertFalse([b for b in buttons_in(view) if b.label == "My fleet"])

    async def test_a_game_in_progress_reports_nothing(self) -> None:
        handler = RecordingHandler()
        view = make_view(handler=handler)
        await view._on_press(0, make_interaction(ALICE))
        self.assertEqual(handler.winners, [])

    async def test_against_the_bot_it_fires_back_straight_away(self) -> None:
        game = BattleshipGame(ALICE, BOT, ALICE_FLEET, BOB_FLEET)
        view = make_view(game, bot_id=BOT)
        await view._on_press(24, make_interaction(ALICE))
        self.assertEqual(len(game.board_of(ALICE).shots), 1)
        self.assertEqual(game.current_player_id, ALICE)

    async def test_the_bot_is_not_a_restricted_player(self) -> None:
        view = make_view(BattleshipGame(ALICE, BOT, ALICE_FLEET, BOB_FLEET), bot_id=BOT)
        self.assertTrue(await view.interaction_check(make_interaction(ALICE)))
        self.assertFalse(await view.interaction_check(make_interaction(BOT)))

    async def test_only_the_two_players_may_press(self) -> None:
        view = make_view()
        self.assertTrue(await view.interaction_check(make_interaction(ALICE)))
        self.assertTrue(await view.interaction_check(make_interaction(BOB)))
        self.assertFalse(await view.interaction_check(make_interaction(99)))

    async def test_a_whole_game_against_the_bot_can_be_played_to_the_end(self) -> None:
        handler = RecordingHandler(note=None)
        game = new_battleship_game(ALICE, BOT, random.Random(3))
        view = make_view(game, bot_id=BOT, handler=handler)
        for square in range(SQUARES):
            if view.is_finished():
                break
            if square not in game.board_of(BOT).shots:
                await view._on_press(square, make_interaction(ALICE))
        self.assertTrue(game.is_over)
        self.assertEqual(handler.winners, [game.winner_id])

    async def test_timeout_locks_every_square(self) -> None:
        view = make_view()
        view.message = mock.Mock(edit=mock.AsyncMock())
        await view.on_timeout()
        view.message.edit.assert_awaited_once()
        self.assertTrue(all(button.disabled for button in buttons_in(view)))

    def test_the_layout_fits_discords_component_limit(self) -> None:
        self.assertLessEqual(len(list(make_view().walk_children())), COMPONENT_LIMIT)


if __name__ == "__main__":
    unittest.main()
