"""Test the bonus mode."""
from mpf.tests.MpfTestCase import MpfTestCase, MagicMock, test_config_directory


class TestBonusMode(MpfTestCase):

    def get_config_file(self):
        return 'config.yaml'

    def get_machine_path(self):
        return 'tests/machine_files/bonus/'

    def _start_game(self):
        self.machine.playfield.add_ball = MagicMock()
        self.machine.ball_controller.num_balls_known = 3
        self.hit_and_release_switch("s_start")
        self.advance_time_and_run()
        self.assertIsNotNone(self.machine.game)

    def _stop_game(self):
        # stop game
        self.assertIsNotNone(self.machine.game)
        self.machine.game.end_game()
        self.advance_time_and_run()
        self.assertIsNone(self.machine.game)

    def test_slam_tilt_in_service(self):
        """Test that bonus does not crash on slam tilt during service mode."""
        self._start_game()
        # todo add handler to game_ending to delay it a bit

        self.advance_time_and_run(5)
        # enter menu
        self.machine.switch_controller.process_switch("s_service_enter", state=1, logical=True)
        self.machine.switch_controller.process_switch("s_slam_tilt", state=1, logical=True)
        self.advance_time_and_run()

    def testBonus(self):
        self.mock_event("bonus_entry")
        # start game
        self._start_game()

        self.post_event("start_mode1")
        self.advance_time_and_run()
        self.assertTrue(self.machine.mode_controller.is_active('mode1'))

        # player gets some score
        self.post_event("hit_target")

        # score 3 ramp shots
        self.post_event("score_ramps")
        self.post_event("score_ramps")
        self.post_event("score_ramps")

        # score 2 modes
        self.post_event("score_modes")
        self.post_event("score_modes")

        # increase multiplier to 5 (by hitting it 4 times)
        self.post_event("add_multiplier")
        self.post_event("add_multiplier")
        self.post_event("add_multiplier")
        self.post_event("add_multiplier")
        self.advance_time_and_run()

        # drain a ball
        self.machine.game.balls_in_play = 0
        self.advance_time_and_run(1)

        # check that bonus mode is loaded
        self.assertModeRunning('bonus')
        self.advance_time_and_run(1)
        self.assertEqual("bonus_ramps", self._last_event_kwargs["bonus_entry"]["entry"])
        self.assertEqual(3000, self._last_event_kwargs["bonus_entry"]["score"])
        self.assertEqual(3, self._last_event_kwargs["bonus_entry"]["hits"])
        self.advance_time_and_run(2)
        self.assertEqual("bonus_modes", self._last_event_kwargs["bonus_entry"]["entry"])
        self.assertEqual(10000, self._last_event_kwargs["bonus_entry"]["score"])
        self.assertEqual(2, self._last_event_kwargs["bonus_entry"]["hits"])
        self.advance_time_and_run(2)
        self.assertEqual("bonus_undefined_var", self._last_event_kwargs["bonus_entry"]["entry"])
        self.assertEqual(0, self._last_event_kwargs["bonus_entry"]["score"])
        self.assertEqual(0, self._last_event_kwargs["bonus_entry"]["hits"])
        self.advance_time_and_run(2)
        self.assertEqual("bonus_static", self._last_event_kwargs["bonus_entry"]["entry"])
        self.assertEqual(2000, self._last_event_kwargs["bonus_entry"]["score"])
        self.assertEqual(1, self._last_event_kwargs["bonus_entry"]["hits"])
        self.advance_time_and_run(2)
        self.assertEqual("subtotal", self._last_event_kwargs["bonus_entry"]["entry"])
        self.assertEqual(15000, self._last_event_kwargs["bonus_entry"]["score"])
        self.advance_time_and_run(2)
        self.assertEqual("multiplier", self._last_event_kwargs["bonus_entry"]["entry"])
        self.assertEqual(5, self._last_event_kwargs["bonus_entry"]["score"])
        self.advance_time_and_run(2)
        self.assertEqual("total", self._last_event_kwargs["bonus_entry"]["entry"])
        self.assertEqual(75000, self._last_event_kwargs["bonus_entry"]["score"])
        self.assertEqual(76337, self.machine.game.player.score)

        # check resets
        self.assertEqual(0, self.machine.game.player.ramps)
        self.assertEqual(2, self.machine.game.player.modes)
        self.assertEqual(5, self.machine.game.player.bonus_multiplier)

        self.advance_time_and_run(10)
        self.mock_event("bonus_entry")

        # drain a ball
        self.machine.game.balls_in_play = 0
        self.advance_time_and_run(1)
        self.assertModeRunning('bonus')
        self.advance_time_and_run(2)

        self.assertEqual("bonus_ramps", self._last_event_kwargs["bonus_entry"]["entry"])
        self.assertEqual(0, self._last_event_kwargs["bonus_entry"]["score"])
        self.assertEqual(0, self._last_event_kwargs["bonus_entry"]["hits"])
        self.advance_time_and_run(2)
        self.assertEqual("bonus_modes", self._last_event_kwargs["bonus_entry"]["entry"])
        self.assertEqual(10000, self._last_event_kwargs["bonus_entry"]["score"])
        self.assertEqual(2, self._last_event_kwargs["bonus_entry"]["hits"])
        self.advance_time_and_run(2)
        self.assertEqual("bonus_undefined_var", self._last_event_kwargs["bonus_entry"]["entry"])
        self.assertEqual(0, self._last_event_kwargs["bonus_entry"]["score"])
        self.assertEqual(0, self._last_event_kwargs["bonus_entry"]["hits"])
        self.advance_time_and_run(2)
        self.assertEqual("bonus_static", self._last_event_kwargs["bonus_entry"]["entry"])
        self.assertEqual(2000, self._last_event_kwargs["bonus_entry"]["score"])
        self.assertEqual(1, self._last_event_kwargs["bonus_entry"]["hits"])
        self.advance_time_and_run(2)
        self.assertEqual("subtotal", self._last_event_kwargs["bonus_entry"]["entry"])
        self.assertEqual(12000, self._last_event_kwargs["bonus_entry"]["score"])
        self.advance_time_and_run(2)
        self.assertEqual("multiplier", self._last_event_kwargs["bonus_entry"]["entry"])
        self.assertEqual(5, self._last_event_kwargs["bonus_entry"]["score"])
        self.advance_time_and_run(2)
        self.assertEqual("total", self._last_event_kwargs["bonus_entry"]["entry"])
        self.assertEqual(60000, self._last_event_kwargs["bonus_entry"]["score"])
        self.assertEqual(136337, self.machine.game.player.score)

        # multiplier should stay the same
        self.assertEqual(0, self.machine.game.player.ramps)
        self.assertEqual(2, self.machine.game.player.modes)
        self.assertEqual(5, self.machine.game.player.bonus_multiplier)

        # drain a ball
        self.machine.game.balls_in_play = 0
        self.advance_time_and_run(30)

        # make some changes for the next test
        self.machine.game.player.ramps = 1
        self.machine.game.player.bonus_multiplier = 2

        # test the hurry up
        self.mock_event("bonus_entry")
        self.mock_event("bonus_start")

        # drain a ball
        self.machine.game.balls_in_play = 0
        self.advance_time_and_run(1)
        self.assertEventCalled('bonus_start')
        self.assertEventNotCalled('bonus_entry')

        self.advance_time_and_run(2)
        self.assertEqual("bonus_ramps", self._last_event_kwargs["bonus_entry"]["entry"])

        self.post_event('flipper_cancel', .1)
        self.assertEqual("bonus_modes", self._last_event_kwargs["bonus_entry"]["entry"])

        self.advance_time_and_run(.5)
        self.assertEqual("bonus_undefined_var", self._last_event_kwargs["bonus_entry"]["entry"])
        self.advance_time_and_run(.5)
        self.assertEqual("bonus_static", self._last_event_kwargs["bonus_entry"]["entry"])
        self.advance_time_and_run(.5)
        self.assertEqual("subtotal", self._last_event_kwargs["bonus_entry"]["entry"])

        self.advance_time_and_run(.5)
        self.assertEqual("multiplier", self._last_event_kwargs["bonus_entry"]["entry"])

        self.advance_time_and_run(.5)
        self.assertEqual("total", self._last_event_kwargs["bonus_entry"]["entry"])

        # test multiplier screens are skipped if multiplier is 1
        self.advance_time_and_run(30)
        self.machine.game.player.bonus_multiplier = 1
        self.machine.game.player.ramps = 1

        # test the hurry up
        self.mock_event("bonus_start")
        self.mock_event("bonus_entry")

        # drain a ball
        self.machine.game.balls_in_play = 0
        self.advance_time_and_run(3)

        self.assertEqual("bonus_ramps", self._last_event_kwargs["bonus_entry"]["entry"])
        self.assertEqual(1000, self._last_event_kwargs["bonus_entry"]["score"])
        self.assertEqual(1, self._last_event_kwargs["bonus_entry"]["hits"])
        self.advance_time_and_run(2)
        self.assertEqual("bonus_modes", self._last_event_kwargs["bonus_entry"]["entry"])
        self.assertEqual(10000, self._last_event_kwargs["bonus_entry"]["score"])
        self.assertEqual(2, self._last_event_kwargs["bonus_entry"]["hits"])
        self.advance_time_and_run(2)
        self.assertEqual("bonus_undefined_var", self._last_event_kwargs["bonus_entry"]["entry"])
        self.assertEqual(0, self._last_event_kwargs["bonus_entry"]["score"])
        self.assertEqual(0, self._last_event_kwargs["bonus_entry"]["hits"])
        self.advance_time_and_run(2)
        self.assertEqual("bonus_static", self._last_event_kwargs["bonus_entry"]["entry"])
        self.assertEqual(2000, self._last_event_kwargs["bonus_entry"]["score"])
        self.assertEqual(1, self._last_event_kwargs["bonus_entry"]["hits"])
        self.advance_time_and_run(2)
        self.assertEqual("total", self._last_event_kwargs["bonus_entry"]["entry"])
        self.assertEqual(13000, self._last_event_kwargs["bonus_entry"]["score"])
        self.assertEqual(175337, self.machine.game.player.score)


    @test_config_directory("tests/machine_files/bonus_no_keep_multiplier/")
    def testBonusNoKeepMultiplier(self):
        self.mock_event("bonus_entry")
        # start game
        self._start_game()

        self.post_event("start_mode1")
        self.advance_time_and_run()
        self.assertTrue(self.machine.mode_controller.is_active('mode1'))

        # player gets some score
        self.post_event("hit_target")

        # score 3 ramp shots
        self.post_event("score_ramps")
        self.post_event("score_ramps")
        self.post_event("score_ramps")

        # score 2 modes
        self.post_event("score_modes")
        self.post_event("score_modes")

        # increase multiplier to 5 (by hitting it 4 times)
        self.post_event("add_multiplier")
        self.post_event("add_multiplier")
        self.post_event("add_multiplier")
        self.post_event("add_multiplier")
        self.advance_time_and_run()

        # drain a ball
        self.machine.game.balls_in_play = 0
        self.advance_time_and_run(1)

        # check that bonus mode is loaded
        self.assertModeRunning('bonus')
        self.advance_time_and_run(2)

        self.assertEqual("bonus_ramps", self._last_event_kwargs["bonus_entry"]["entry"])
        self.assertEqual(3000, self._last_event_kwargs["bonus_entry"]["score"])
        self.assertEqual(3, self._last_event_kwargs["bonus_entry"]["hits"])
        self.advance_time_and_run(2)
        self.assertEqual("bonus_modes", self._last_event_kwargs["bonus_entry"]["entry"])
        self.assertEqual(10000, self._last_event_kwargs["bonus_entry"]["score"])
        self.assertEqual(2, self._last_event_kwargs["bonus_entry"]["hits"])
        self.advance_time_and_run(2)
        self.assertEqual("subtotal", self._last_event_kwargs["bonus_entry"]["entry"])
        self.assertEqual(13000, self._last_event_kwargs["bonus_entry"]["score"])
        self.advance_time_and_run(2)
        self.assertEqual("multiplier", self._last_event_kwargs["bonus_entry"]["entry"])
        self.assertEqual(5, self._last_event_kwargs["bonus_entry"]["score"])
        self.advance_time_and_run(2)
        self.assertEqual("total", self._last_event_kwargs["bonus_entry"]["entry"])
        self.assertEqual(65000, self._last_event_kwargs["bonus_entry"]["score"])
        self.assertEqual(66337, self.machine.game.player.score)

        # check resets
        self.assertEqual(0, self.machine.game.player.ramps)
        self.assertEqual(2, self.machine.game.player.modes)
        self.assertEqual(5, self.machine.game.player.bonus_multiplier)

        self.mock_event("bonus_entry")
        self.advance_time_and_run(20)

        # drain a ball
        self.machine.game.balls_in_play = 0
        self.advance_time_and_run(2)
        self.assertEqual("bonus_modes", self._last_event_kwargs["bonus_entry"]["entry"])
        self.assertEqual(10000, self._last_event_kwargs["bonus_entry"]["score"])
        self.assertEqual(2, self._last_event_kwargs["bonus_entry"]["hits"])
        self.advance_time_and_run(2)
        self.assertEqual("total", self._last_event_kwargs["bonus_entry"]["entry"])
        self.assertEqual(10000, self._last_event_kwargs["bonus_entry"]["score"])
        self.assertEqual(76337, self.machine.game.player.score)


    def testBonusTilted(self):
        self.mock_event("bonus_ramps")
        self.mock_event("bonus_modes")
        self.mock_event("bonus_subtotal")
        self.mock_event("bonus_multiplier")
        self.mock_event("bonus_total")
        # start game
        self._start_game()

        self.post_event("start_mode1")
        self.advance_time_and_run()

        # player gets some score
        self.post_event("hit_target")

        # score 3 ramp shots
        self.post_event("score_ramps")
        self.post_event("score_ramps")
        self.post_event("score_ramps")

        # score 2 modes
        self.post_event("score_modes")
        self.post_event("score_modes")

        # increase multiplier to 5 (by hitting it 4 times)
        self.post_event("add_multiplier")
        self.post_event("add_multiplier")
        self.post_event("add_multiplier")
        self.post_event("add_multiplier")
        self.advance_time_and_run()

        # tilt the game
        self.machine.game.tilted = True

        # drain a ball
        self.machine.game.balls_in_play = 0
        self.advance_time_and_run(30)
        self.assertEqual(1337, self.machine.game.player.score)

        # check resets
        self.assertEqual(0, self.machine.game.player.ramps)
        self.assertEqual(2, self.machine.game.player.modes)
        self.assertEqual(5, self.machine.game.player.bonus_multiplier)

    @test_config_directory("tests/machine_files/bonus_additional_events/")
    def testBonusStopEvent(self):
        self.mock_event("bonus_ramps")
        self.mock_event("bonus_modes")
        self.mock_event("bonus_subtotal")
        self.mock_event("bonus_multiplier")
        self.mock_event("bonus_total")
        # start game
        self._start_game()

        self.post_event("start_mode1")
        self.advance_time_and_run()

        # player gets some score
        self.post_event("hit_target")

        # score 3 ramp shots
        self.post_event("score_ramps")
        self.post_event("score_ramps")
        self.post_event("score_ramps")

        # score 2 modes
        self.post_event("score_modes")
        self.post_event("score_modes")

        # increase multiplier to 5 (by hitting it 4 times)
        self.post_event("add_multiplier")
        self.post_event("add_multiplier")
        self.post_event("add_multiplier")
        self.post_event("add_multiplier")
        self.advance_time_and_run()

        # drain a ball
        self.machine.game.balls_in_play = 0
        self.advance_time_and_run(30)
        self.assertEqual(66337, self.machine.game.player.score)
        self.assertModeRunning("bonus")
        self.post_event("stop_bonus")
        self.advance_time_and_run(.1)
        self.assertModeNotRunning("bonus")

        # check resets
        self.assertEqual(0, self.machine.game.player.ramps)
        self.assertEqual(2, self.machine.game.player.modes)
        self.assertEqual(5, self.machine.game.player.bonus_multiplier)

    @test_config_directory("tests/machine_files/bonus_dynamic_keep_multiplier/")
    def testBonusDynamicKeepMultiplier(self):
        # start game
        self._start_game()

        self.post_event("start_mode1")
        self.advance_time_and_run()
        self.assertTrue(self.machine.mode_controller.is_active('mode1'))

        # increase multiplier to 5 (by hitting it 4 times)
        self.post_event("add_multiplier")
        self.post_event("add_multiplier")
        self.post_event("add_multiplier")
        self.post_event("add_multiplier")
        self.advance_time_and_run()

        # drain a ball
        self.machine.game.balls_in_play = 0
        self.advance_time_and_run(1)

        # check that bonus mode is loaded
        self.assertModeRunning('bonus')
        self.advance_time_and_run(29)

        # check resets
        self.assertEqual(5, self.machine.game.player.bonus_multiplier)

        # drain a ball
        self.machine.game.balls_in_play = 0
        self.advance_time_and_run(1)

        # check that bonus mode is loaded
        self.assertModeRunning('bonus')
        self.advance_time_and_run(29)

        # add multipliers
        self.post_event("add_multiplier")
        self.post_event("add_multiplier")
        self.post_event("add_multiplier")
        self.post_event("add_multiplier")
        self.advance_time_and_run()

        # check resets
        self.assertEqual(1, self.machine.game.player.bonus_multiplier)

