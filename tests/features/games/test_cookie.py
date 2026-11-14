"""Tests for the cookie mystery: clues, the case generator, the game and its views."""

import random
import unittest
from types import SimpleNamespace
from unittest import mock

from discord import ui

from features.games.cookie_case import (
    FICTIONAL_SUSPECTS,
    MIN_CLUES,
    ROOMS,
    SUSPECT_COUNT,
    Case,
    choose_suspects,
    generate_case,
)
from features.games.cookie_case_view import CookieCaseView
from features.games.cookie_clues import (
    ALL_ASSIGNMENTS,
    ROOM_COUNT,
    FurtherAlong,
    NextTo,
    NotInRoom,
    NotNextTo,
    possible_thieves,
    true_clues,
)
from features.games.cookie_game import STARTING_CLUES, CookieGame
from features.games.cookie_lobby_view import CookieLobbyView
from features.games.cookie_text import (
    COOKIE,
    accusation_text,
    clues_text,
    detectives_text,
    status_text,
    story_text,
    truth_text,
)
from features.games.errors import GameError
from tests.features.games.test_game_views import RecordingHandler, make_interaction, notes_in

ALICE, BOB, CARA, BOT = 1, 2, 4, 3
PLAYERS = {ALICE: "Alice", BOB: "Bob"}
SUSPECTS = ("Alice", "Bob", "Sir Crumbsalot", "Madame Muffin", "Professor Sprinkles")
ROOM_NAMES = tuple(room.name for room in ROOMS)
COMPONENT_LIMIT = 40


def stacked_case() -> Case:
    """Everyone stands in the room matching their number; the cookie is in the Library."""
    clues = tuple(NotInRoom(suspect, 4) for suspect in range(4))
    return Case(SUSPECTS, (0, 1, 2, 3, 4), cookie_room=2, thief=2, clues=clues)


def make_game(players: tuple[int, ...] = (ALICE, BOB)) -> CookieGame:
    return CookieGame(stacked_case(), players)


def make_case_view(handler=None, players=PLAYERS) -> CookieCaseView:
    return CookieCaseView(
        make_game(tuple(players)),
        players,
        bot_id=BOT,
        timeout_seconds=300,
        on_finish=handler,
    )


def selects_in(view: ui.LayoutView) -> list[ui.Select]:
    return [item for item in view.walk_children() if isinstance(item, ui.Select)]


def buttons_in(view: ui.LayoutView) -> list[ui.Button]:
    return [item for item in view.walk_children() if isinstance(item, ui.Button)]


class ClueTests(unittest.TestCase):
    POSITIONS = (0, 1, 3, 2, 4)

    def test_each_kind_of_clue_holds_only_when_it_should(self) -> None:
        self.assertTrue(NotInRoom(0, 1).holds(self.POSITIONS))
        self.assertFalse(NotInRoom(0, 0).holds(self.POSITIONS))
        self.assertTrue(NextTo(0, 1).holds(self.POSITIONS))
        self.assertFalse(NextTo(0, 2).holds(self.POSITIONS))
        self.assertTrue(NotNextTo(0, 2).holds(self.POSITIONS))
        self.assertFalse(NotNextTo(2, 3).holds(self.POSITIONS))
        self.assertTrue(FurtherAlong(4, 0).holds(self.POSITIONS))
        self.assertFalse(FurtherAlong(0, 4).holds(self.POSITIONS))

    def test_clues_read_naturally(self) -> None:
        names = ("Ann", "Ben", "Cy", "Di", "Ed")

        def render(clue) -> str:
            return clue.render(names, ROOM_NAMES)

        self.assertEqual(render(NotInRoom(0, 3)), "**Ann** was not in the **Garden**.")
        self.assertEqual(render(NextTo(0, 1)), "**Ann** was in a room right next to **Ben**'s.")
        self.assertEqual(render(NotNextTo(0, 1)), "**Ann** was not in a room next to **Ben**'s.")
        self.assertEqual(
            render(FurtherAlong(2, 1)), "**Cy** was further along the corridor than **Ben**."
        )

    def test_every_generated_true_clue_is_true(self) -> None:
        for positions in ALL_ASSIGNMENTS[::7]:
            with self.subTest(positions=positions):
                self.assertTrue(all(clue.holds(positions) for clue in true_clues(positions)))

    def test_with_no_clues_anyone_could_be_the_thief(self) -> None:
        self.assertEqual(possible_thieves([], cookie_room=0), set(range(ROOM_COUNT)))

    def test_all_the_true_clues_pin_down_one_thief(self) -> None:
        positions = (3, 0, 4, 1, 2)
        thieves = possible_thieves(true_clues(positions), cookie_room=4)
        self.assertEqual(thieves, {positions.index(4)})


class SuspectTests(unittest.TestCase):
    def test_the_players_are_suspects_and_the_rest_are_fictional(self) -> None:
        suspects = choose_suspects(["Alice", "Bob"], random.Random(1))
        self.assertEqual(len(suspects), SUSPECT_COUNT)
        self.assertTrue({"Alice", "Bob"} <= set(suspects))
        self.assertEqual(len([name for name in suspects if name in FICTIONAL_SUSPECTS]), 3)

    def test_the_order_is_shuffled(self) -> None:
        orders = {tuple(choose_suspects(["Alice"], random.Random(seed))) for seed in range(20)}
        self.assertGreater(len(orders), 1)

    def test_duplicate_display_names_are_made_unique(self) -> None:
        suspects = choose_suspects(["Alex", "Alex", "Alex"], random.Random(1))
        self.assertEqual(len(set(suspects)), SUSPECT_COUNT)
        self.assertTrue({"Alex", "Alex (2)", "Alex (3)"} <= set(suspects))

    def test_a_player_named_like_a_character_does_not_clash(self) -> None:
        suspects = choose_suspects(["Sir Crumbsalot"], random.Random(1))
        self.assertEqual(len(set(suspects)), SUSPECT_COUNT)

    def test_extra_players_beyond_the_seats_are_ignored(self) -> None:
        names = [f"P{number}" for number in range(8)]
        self.assertEqual(len(choose_suspects(names, random.Random(1))), SUSPECT_COUNT)


class GeneratorTests(unittest.TestCase):
    def cases(self, seeds: int = 200) -> list[Case]:
        cases = []
        for seed in range(seeds):
            rng = random.Random(seed)
            cases.append(generate_case(rng, choose_suspects(["Alice"], rng)))
        return cases

    def test_every_case_has_exactly_one_possible_thief(self) -> None:
        for case in self.cases():
            self.assertEqual(possible_thieves(case.clues, case.cookie_room), {case.thief})

    def test_every_clue_is_true_of_what_really_happened(self) -> None:
        for case in self.cases():
            self.assertTrue(all(clue.holds(case.positions) for clue in case.clues))

    def test_the_thief_is_whoever_stood_in_the_cookie_room(self) -> None:
        for case in self.cases():
            self.assertEqual(case.positions[case.thief], case.cookie_room)
            self.assertEqual(sorted(case.positions), list(range(ROOM_COUNT)))

    def test_there_are_never_too_few_clues_and_no_clue_repeats(self) -> None:
        for case in self.cases():
            self.assertGreaterEqual(len(case.clues), MIN_CLUES)
            self.assertEqual(len(set(case.clues)), len(case.clues))

    def test_cases_are_not_all_the_same(self) -> None:
        thieves = {(case.thief, case.cookie_room) for case in self.cases(50)}
        self.assertGreater(len(thieves), 5)

    def test_the_same_seed_gives_the_same_case(self) -> None:
        def make() -> Case:
            rng = random.Random(42)
            return generate_case(rng, choose_suspects(["Alice"], rng))

        self.assertEqual(make(), make())


class CookieGameTests(unittest.TestCase):
    def test_the_case_opens_with_a_couple_of_clues(self) -> None:
        game = make_game()
        self.assertEqual(len(game.visible_clues), STARTING_CLUES)
        self.assertTrue(game.has_hidden_clues)

    def test_clues_come_out_one_at_a_time_until_none_are_left(self) -> None:
        game = make_game()
        total = len(game.case.clues)
        for expected in range(STARTING_CLUES + 1, total + 1):
            game.reveal_next_clue()
            self.assertEqual(len(game.visible_clues), expected)
        self.assertFalse(game.has_hidden_clues)
        with self.assertRaises(GameError):
            game.reveal_next_clue()

    def test_naming_the_thief_solves_the_case(self) -> None:
        game = make_game()
        accusation = game.accuse(ALICE, 2)
        self.assertTrue(accusation.correct)
        self.assertEqual(game.solver_id, ALICE)
        self.assertTrue(game.is_solved)
        self.assertTrue(game.is_over)

    def test_a_wrong_accusation_knocks_the_detective_out_but_not_the_case(self) -> None:
        game = make_game()
        self.assertFalse(game.accuse(ALICE, 0).correct)
        self.assertEqual(game.eliminated, {ALICE})
        self.assertFalse(game.is_over)
        self.assertTrue(game.accuse(BOB, 2).correct)
        self.assertEqual(game.solver_id, BOB)

    def test_a_detective_only_gets_one_accusation(self) -> None:
        game = make_game()
        game.accuse(ALICE, 0)
        with self.assertRaises(GameError):
            game.accuse(ALICE, 2)
        self.assertFalse(game.is_solved)

    def test_everyone_guessing_wrong_closes_the_case_as_failed(self) -> None:
        game = make_game()
        game.accuse(ALICE, 0)
        self.assertFalse(game.is_failed)
        game.accuse(BOB, 1)
        self.assertTrue(game.is_failed)
        self.assertTrue(game.is_over)
        self.assertIsNone(game.solver_id)

    def test_a_stranger_cannot_accuse(self) -> None:
        with self.assertRaises(GameError):
            make_game().accuse(99, 2)

    def test_nothing_changes_once_the_case_is_closed(self) -> None:
        game = make_game()
        game.accuse(ALICE, 2)
        with self.assertRaises(GameError):
            game.accuse(BOB, 2)
        with self.assertRaises(GameError):
            game.reveal_next_clue()

    def test_a_solo_detective_has_a_single_try(self) -> None:
        game = make_game((ALICE,))
        game.accuse(ALICE, 0)
        self.assertTrue(game.is_failed)


class TextTests(unittest.TestCase):
    def test_the_story_names_the_cookie_room_corridor_and_suspects(self) -> None:
        text = story_text(stacked_case())
        self.assertIn("**Library**", text)
        self.assertIn("🍳 Kitchen → 🥫 Pantry → 📚 Library → 🌳 Garden → 🕸️ Attic", text)
        self.assertIn("Sir Crumbsalot", text)

    def test_the_clue_list_counts_what_has_been_revealed(self) -> None:
        game = make_game()
        lines = clues_text(game).splitlines()
        self.assertEqual(lines[0], "**Clues** (2 of 4)")
        self.assertEqual(len(lines), 1 + STARTING_CLUES)
        self.assertTrue(lines[1].startswith("1. "))

    def test_eliminated_detectives_are_struck_through(self) -> None:
        game = make_game()
        self.assertEqual(detectives_text(game, PLAYERS), "-# Detectives: Alice, Bob")
        game.accuse(BOB, 0)
        self.assertEqual(detectives_text(game, PLAYERS), "-# Detectives: Alice, ~~Bob~~")

    def test_accusations_are_described_either_way(self) -> None:
        game = make_game()
        wrong = game.accuse(ALICE, 0)
        self.assertIn("is out", accusation_text(wrong, game, PLAYERS))
        right = game.accuse(BOB, 2)
        self.assertIn("got the thief", accusation_text(right, game, PLAYERS))

    def test_status_covers_every_stage(self) -> None:
        game = make_game()
        self.assertIn("accuse", status_text(game, PLAYERS, False))
        self.assertEqual(status_text(game, PLAYERS, True), "The case went cold.")
        game.accuse(ALICE, 2)
        self.assertIn("**Alice** cracked the case", status_text(game, PLAYERS, False))
        failed = make_game()
        failed.accuse(ALICE, 0)
        failed.accuse(BOB, 0)
        self.assertIn("got away", status_text(failed, PLAYERS, False))

    def test_the_truth_lists_every_room_and_marks_only_the_cookie_room(self) -> None:
        lines = truth_text(stacked_case()).splitlines()
        self.assertEqual(len(lines), 1 + ROOM_COUNT)
        marked = [line for line in lines if COOKIE in line]
        self.assertEqual(marked, ["📚 Library: **Sir Crumbsalot** 🍪"])


class CookieCaseViewTests(unittest.IsolatedAsyncioTestCase):
    async def test_next_clue_reveals_one_and_disables_when_none_are_left(self) -> None:
        view = make_case_view()
        interaction = make_interaction(ALICE)
        await view._on_next_clue(interaction)
        self.assertEqual(len(view._game.visible_clues), STARTING_CLUES + 1)
        interaction.response.edit_message.assert_awaited_once()
        await view._on_next_clue(make_interaction(BOB))
        self.assertTrue(next(b for b in buttons_in(view) if b.label == "Next clue").disabled)

    async def test_asking_for_a_clue_that_does_not_exist_is_refused_privately(self) -> None:
        view = make_case_view()
        for _ in range(len(view._game.case.clues) - STARTING_CLUES):
            await view._on_next_clue(make_interaction(ALICE))
        late = make_interaction(ALICE)
        await view._on_next_clue(late)
        self.assertTrue(late.response.send_message.await_args.kwargs["ephemeral"])

    async def test_a_wrong_accusation_keeps_the_case_open_for_the_others(self) -> None:
        handler = RecordingHandler()
        view = make_case_view(handler)
        interaction = make_interaction(ALICE)
        await view._accuse(0, interaction)
        interaction.response.edit_message.assert_awaited_once()
        self.assertEqual(handler.winners, [])
        self.assertFalse(view.is_finished())
        self.assertEqual(len(selects_in(view)), 1)

    async def test_the_second_accusation_by_one_detective_is_refused(self) -> None:
        view = make_case_view()
        await view._accuse(0, make_interaction(ALICE))
        again = make_interaction(ALICE)
        await view._accuse(2, again)
        self.assertIn("already", again.response.send_message.await_args.args[0])

    async def test_solving_reports_the_solver_and_shows_the_truth(self) -> None:
        handler = RecordingHandler()
        view = make_case_view(handler)
        await view._accuse(2, make_interaction(BOB))
        self.assertEqual(handler.winners, [BOB])
        self.assertTrue(view.is_finished())
        self.assertIn("-# +50 XP", notes_in(view))
        self.assertTrue(any("What really happened" in text for text in notes_in(view)))
        self.assertEqual(selects_in(view), [])
        self.assertEqual(buttons_in(view), [])

    async def test_everyone_failing_reports_the_bot_as_the_winner(self) -> None:
        handler = RecordingHandler(note=None)
        view = make_case_view(handler)
        await view._accuse(0, make_interaction(ALICE))
        await view._accuse(1, make_interaction(BOB))
        self.assertEqual(handler.winners, [BOT])

    async def test_the_accusation_menu_lists_every_suspect(self) -> None:
        select = selects_in(make_case_view())[0]
        self.assertEqual([option.label for option in select.options], list(SUSPECTS))
        self.assertEqual([option.value for option in select.options], ["0", "1", "2", "3", "4"])

    async def test_only_the_detectives_may_use_it(self) -> None:
        view = make_case_view()
        self.assertTrue(await view.interaction_check(make_interaction(ALICE)))
        self.assertTrue(await view.interaction_check(make_interaction(BOB)))
        self.assertFalse(await view.interaction_check(make_interaction(99)))

    async def test_a_cold_case_shows_the_truth(self) -> None:
        view = make_case_view()
        view.message = mock.Mock(edit=mock.AsyncMock())
        await view.on_timeout()
        view.message.edit.assert_awaited_once()
        self.assertTrue(any("What really happened" in text for text in notes_in(view)))
        self.assertEqual(selects_in(view), [])

    def test_the_layout_fits_discords_component_limit(self) -> None:
        view = make_case_view()
        while view._game.has_hidden_clues:
            view._game.reveal_next_clue()
        view._render()
        self.assertLessEqual(len(list(view.walk_children())), COMPONENT_LIMIT)


def make_user(user_id: int, name: str) -> SimpleNamespace:
    return SimpleNamespace(id=user_id, display_name=name)


def make_lobby_interaction(user_id: int, name: str) -> mock.Mock:
    interaction = make_interaction(user_id)
    interaction.user = make_user(user_id, name)
    interaction.message = mock.Mock()
    return interaction


class CookieLobbyViewTests(unittest.IsolatedAsyncioTestCase):
    def make_lobby(self, start_case=None) -> CookieLobbyView:
        return CookieLobbyView(ALICE, "Alice", start_case or mock.Mock(), timeout_seconds=60)

    async def test_players_can_join_once(self) -> None:
        lobby = self.make_lobby()
        await lobby._on_join(make_lobby_interaction(BOB, "Bob"))
        self.assertEqual(lobby._players, {ALICE: "Alice", BOB: "Bob"})
        again = make_lobby_interaction(BOB, "Bob")
        await lobby._on_join(again)
        self.assertIn("already", again.response.send_message.await_args.args[0])
        self.assertEqual(len(lobby._players), 2)

    async def test_the_lobby_fills_up(self) -> None:
        lobby = self.make_lobby()
        for number in range(SUSPECT_COUNT - 1):
            await lobby._on_join(make_lobby_interaction(100 + number, f"P{number}"))
        full = make_lobby_interaction(CARA, "Cara")
        await lobby._on_join(full)
        self.assertEqual(len(lobby._players), SUSPECT_COUNT)
        self.assertIn("full", full.response.send_message.await_args.args[0])

    async def test_only_the_host_can_start_the_case(self) -> None:
        start_case = mock.Mock()
        lobby = self.make_lobby(start_case)
        await lobby._on_join(make_lobby_interaction(BOB, "Bob"))
        refused = make_lobby_interaction(BOB, "Bob")
        await lobby._on_start(refused)
        start_case.assert_not_called()
        self.assertIn("Alice", refused.response.send_message.await_args.args[0])

    async def test_starting_swaps_the_lobby_for_the_case(self) -> None:
        case_view = make_case_view()
        start_case = mock.Mock(return_value=case_view)
        lobby = self.make_lobby(start_case)
        await lobby._on_join(make_lobby_interaction(BOB, "Bob"))
        interaction = make_lobby_interaction(ALICE, "Alice")
        await lobby._on_start(interaction)
        start_case.assert_called_once_with({ALICE: "Alice", BOB: "Bob"})
        interaction.response.edit_message.assert_awaited_once_with(view=case_view)
        self.assertIs(case_view.message, interaction.message)
        self.assertTrue(lobby.is_finished())

    async def test_an_unstarted_lobby_closes_itself(self) -> None:
        lobby = self.make_lobby()
        lobby.message = mock.Mock(edit=mock.AsyncMock())
        await lobby.on_timeout()
        lobby.message.edit.assert_awaited_once()
        self.assertEqual(buttons_in(lobby), [])

    async def test_anyone_can_press_join_without_being_a_detective_yet(self) -> None:
        lobby = self.make_lobby()
        self.assertTrue(await lobby.interaction_check(make_lobby_interaction(99, "Stranger")))


if __name__ == "__main__":
    unittest.main()
