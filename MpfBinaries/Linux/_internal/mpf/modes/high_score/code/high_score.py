"""Contains the High Score mode code."""
import asyncio
from random import choice

from mpf.core.async_mode import AsyncMode
from mpf.core.player import Player


class HighScore(AsyncMode):

    """High score mode.

    Mode which runs during the game ending process to check for high scores and lets the players enter their names or
    initials.
    """

    __slots__ = ["data_manager", "high_scores", "high_score_config", "pending_award", "vars"]

    def __init__(self, *args, **kwargs):
        """Initialize high score mode."""
        self.data_manager = None
        self.high_scores = None
        self.high_score_config = None
        self.pending_award = None
        self.vars = None
        super().__init__(*args, **kwargs)

    def mode_init(self):
        """Initialize high score mode."""
        self.data_manager = self.machine.create_data_manager('high_scores')
        self.high_scores = self.data_manager.get_data()

        self.high_score_config = self.machine.config_validator.validate_config(
            config_spec='high_score',
            source=self.config.get('high_score', {}),
            section_name='high_score')

        # if data is invalid. do not use it
        if self.high_scores and not self._validate_data(self.high_scores):
            self.log.warning("High score data failed validation. Resetting to defaults.")
            self.high_scores = None

        # Load defaults if no high_scores are stored
        if not self.high_scores:
            self._load_defaults()

        self._create_machine_vars()
        self.pending_award = None

        for event in self.high_score_config['reset_high_scores_events']:
            # important: this may not be a mode handler as it should be always active
            self.machine.events.add_handler(event, self._reset)

    def _load_defaults(self):
        """Load default high scores."""
        self.high_scores = {k: [[next(iter(a.keys())), next(iter(a.values()))] for a in v] for (k, v) in
                            self.config['high_score']['defaults'].items()}

    def _load_vars(self):
        """Load var values from the config file."""
        self.vars = {k: [[next(iter(a.keys())), next(iter(a.values()))] for a in v] for (k, v) in
                     self.config['high_score']['vars'].items()}

    def _reset(self, **kwargs):
        """Reset high scores."""
        del kwargs
        self._load_defaults()
        self._create_machine_vars()
        self._write_scores_to_disk()

    def _validate_data(self, data):
        try:
            for category in data:
                if category not in self.high_score_config['categories']:
                    self.log.warning("Found invalid category in high scores.")
                    return False

                for entry in data[category]:
                    if not isinstance(entry, list) or (len(entry) != 2 and len(entry) != 3):
                        self.log.warning("Found invalid high score entry.")
                        return False

                    if not isinstance(entry[0], str) or not isinstance(entry[1], (int, float)):
                        self.log.warning("Found invalid data type in high score entry.")
                        return False
                if len(data[category]) != len(self.config['high_score']['defaults'][category]):
                    self.log.warning("High Score Category %s contains %s entries while defaults contain %s",
                                     category, len(data[category]),
                                     len(self.config['high_score']['defaults'][category]))
                    return False

        except TypeError:
            return False

        return True

    def _create_machine_vars(self):
        """Create all machine vars in the machine on start.

        This is used in attract mode.
        """
        for category, entries in self.high_score_config['categories'].items():
            try:
                for position, (label, (name, value, *hs_vars)) in (
                        enumerate(zip(entries,
                                      self.high_scores[category]))):

                    self.machine.variables.set_machine_var(
                        name=category + str(position + 1) + '_label',
                        value=label)

                    '''machine_var: (high_score_category)(position)_label

                    desc: The "label" of the high score for that specific
                    score category and position. For example,
                    ``score1_label`` holds the label for the #1 position
                    of the "score" player variable (which might be "GRAND
                    CHAMPION").

                    '''

                    self.machine.variables.set_machine_var(
                        name=category + str(position + 1) + '_name',
                        value=name)

                    '''machine_var: (high_score_category)(position)_name

                    desc: Holds the player's name (or initials) for the
                    high score for that category and position.

                    '''

                    self.machine.variables.set_machine_var(
                        name=category + str(position + 1) + '_value',
                        value=value)

                    '''machine_var: (high_score_category)(position)_value

                    desc: Holds the numeric value for the high score
                    for that category and position.

                    '''

                    if len(hs_vars) > 0:
                        for k, v in hs_vars[0].items():
                            self.machine.variables.set_machine_var(
                                name=category + str(position + 1) + '_' + str(k),
                                value=v)

                    '''machine_var: (high_score_category)(position)_(variable)

                    desc: Holds the player or machine variable(s) for the high
                    score for that category and position.

                    '''

            except KeyError:
                self.high_scores[category] = list()

    # pylint: disable-msg=too-many-nested-blocks
    async def _run(self) -> None:
        """Run high score mode."""
        if not self.machine.game or not self.machine.game.player_list:
            self.warning_log("High Score started but there was no game. Will not start.")
            return

        new_high_score_list = {}

        # iterate highscore categories
        for category_name, award_names in self.high_score_config['categories'].items():
            new_list = list()

            # add the existing high scores to the list

            # make sure we have this category in the existing high scores
            if category_name in self.high_scores:
                for category_high_scores in self.high_scores[category_name]:
                    new_list.append(category_high_scores)

            # add the players scores from this game to the list
            for player in self.machine.game.player_list:
                # if the player var is 0, don't add it. This prevents
                # values of 0 being added to blank high score lists
                if player[category_name]:
                    new_list.append([player, player[category_name]])

            # sort if from highest to lowest
            new_list.sort(key=lambda x: x[1], reverse=category_name not in self.high_score_config['reverse_sort'])

            # scan through and see if any of our players are in this list
            i = 0
            while i < len(award_names) and i < len(new_list):
                entry = new_list[i]
                if isinstance(entry[0], Player):
                    player, value = entry
                    # ask player for initials if we do not know them
                    if not player.initials:
                        try:
                            player.initials = await self._ask_player_for_initials(player, award_names[i],
                                                                                  value, category_name)
                        except asyncio.TimeoutError:
                            del new_list[i]
                            # no entry when the player missed the timeout
                            continue
                    # get vars from config
                    self._load_vars()
                    if category_name in self.vars:
                        var_dict = self._assign_vars(category_name, player)
                        # add high score with variables
                        new_list[i] = [player.initials, value, var_dict]
                    else:
                        # add high score without variables
                        new_list[i] = [player.initials, value]
                    # show award slide
                    player_num = player.number
                    await self._show_award_slide(player_num, player.initials, category_name, award_names[i], value)

                # next entry
                i += 1

            # save the new list for this category and trim it so that it's the length specified in the config
            new_high_score_list[category_name] = new_list[:len(award_names)]

        self.high_scores = new_high_score_list
        self._write_scores_to_disk()
        self._create_machine_vars()

    def _assign_vars(self, category_name, player):
        """Define all vars that are for the given category, and assign their values."""
        # create dictionary of the variable name and its value, then load it for the category
        player_num_index = player.number - 1
        var_dict = dict()
        j = 0
        while j < len(self.vars[category_name]) and bool(self.vars[category_name]):
            if 'player' in self.vars[category_name][j][0]:
                var_dict[self.vars[category_name][j][0] + '_' + self.vars[category_name][j][1]] \
                    = self.machine.game.player_list[player_num_index][self.vars[category_name][j][1]]
            else:
                var_dict[self.vars[category_name][j][0] + '_' + self.vars[category_name][j][1]] \
                    = self.machine.variables.get_machine_var(self.vars[category_name][j][1])
            j += 1
        # return the dictionary of items for this specific player and category entry
        return var_dict

    # pylint: disable-msg=too-many-arguments
    async def _ask_player_for_initials(self, player: Player, award_label: str, value: int, category_name: str) -> str:
        """Show text widget to ask player for initials."""
        self.info_log("New high score. Player: %s, award_label: %s"
                      ", Value: %s", player, award_label, value)

        self.machine.events.post('high_score_enter_initials',
                                 award=award_label,
                                 player_num=player.number,
                                 value=value)

        event_result = await asyncio.wait_for(
            self.machine.events.wait_for_event("text_input_high_score_complete"),
            timeout=self.high_score_config['enter_initials_timeout']
        )   # type: dict

        input_initials = event_result["text"] if "text" in event_result else ''

        # If no initials were input, some can be randomly chosen from the 'filler_initials' config section
        if not input_initials and self.high_score_config["filler_initials"]:
            # High scores are stored as an array of [name, score]
            existing_initials = [n[0] for n in self.high_scores[category_name]]
            unused_initials = [i for i in self.high_score_config["filler_initials"] if i not in existing_initials]
            # If there aren't enough to choose something unique, just pick any from the fillers
            if not unused_initials:
                unused_initials = self.high_score_config["filler_initials"]
            input_initials = choice(unused_initials)
        return input_initials

    # pylint: disable-msg=too-many-arguments
    async def _show_award_slide(self, player_num, player_name: str, category_name: str, award: str, value: int) -> None:
        if not self.high_score_config['award_slide_display_time']:
            return

        self.machine.events.post(
            'high_score_award_display',
            player_name=player_name,
            award=award,
            value=value)
        self.machine.events.post(
            '{}_award_display'.format(award),
            player_name=player_name,
            award=award,
            value=value)
        self.machine.events.post(
            '{}_award_display'.format(category_name),
            player_num=player_num,
            player_name=player_name,
            category_name=category_name,
            award=award,
            value=value)
        await asyncio.sleep(self.high_score_config['award_slide_display_time'] / 1000)

    def _write_scores_to_disk(self) -> None:
        self.data_manager.save_all(data=self.high_scores)
