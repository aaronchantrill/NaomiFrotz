# -*- coding: utf-8 -*-
import logging
import os.path
from . import textPlayer as tp
from naomi import plugin


class FrotzPlugin(plugin.SpeechHandlerPlugin):
    def get_phrases(self):
        return [
            self.gettext("LET'S PLAY A GAME"),
            self.gettext("ZORK")
        ]

    def intents(self):
        GameKeywords = []
        if os.path.isfile(os.path.join(os.path.dirname(os.path.realpath(__file__)),"games","zork1.z5")):
            GameKeywords.extend(["ZORK", "ZORK ONE"])
        if os.path.isfile(os.path.join(os.path.dirname(os.path.realpath(__file__)),"games","AMFV.z5")):
            GameKeywords.extend(["A MIND FOREVER VOYAGING", "MIND"])
        if os.path.isfile(os.path.join(os.path.dirname(os.path.realpath(__file__)),"games","hhgg.z5")):
            GameKeywords.extend(["THE HITCHHIKERS GUIDE TO THE GALAXY", "HITCHHIKERS"])
        return {
            'FrotzIntent': {
                'locale': {
                    'en-US': {
                        'keywords': {
                            'GameKeyword': GameKeywords
                        },
                        'templates': [
                            'LET US PLAY A GAME',
                            'LET US PLAY {GameKeyword}',
                            'PLAY {GameKeyword}'
                        ]
                    }
                },
                'action': self.handle
            }
        }

    def handle(self, intent, mic, *args):
        _ = self.gettext
        text = intent['input']
        self._mic = mic
        self._logger = logging.getLogger(__name__)
        # pdb.set_trace()
        self.game_file = "zork1.z5"
        self.game_name = "zork one"
        if("MIND" in text):
            self.game_file = "AMFV.z5"
            self.game_name = "a mind forever voyaging"
        if("HITCHHIKERS" in text):
            self.game_file = "hhgg.z3"
            self.game_name = "the hitchhiker's guide to the galaxy"
        self.game = self.game_file[:self.game_file.find('.')]
        self.savefile = os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            "games",
            self.game+".sav"
        )
        self._mic.say(self.gettext("beginning "+self.game_name))
        # open zork1.corpus in the current directory and create
        # a phrase list from it
        corpus = os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            "games",
            self.game+".corpus"
        )
        phrases = [_('QUIT')]
        with open(corpus, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                phrases.append(line)

        self._logger.debug('Starting frotz mode...')
        with self._mic.special_mode(self.game, phrases):
            self._logger.debug('Frotz mode started.')
            t = tp.textPlayer(self.game_file)
            response = t.run()
            if(os.path.isfile(self.savefile)):
                t.restore(self.savefile)
                response = t.execute_command('l')
            current_location = response.location
            self._mic.say(response.location)
            if(response.description):
                self._mic.say(response.description)

            mode_not_stopped = True
            while mode_not_stopped:
                texts = self._mic.active_listen()

                text = ''
                if texts:
                    text = ', '.join(texts).upper()

                if not text:
                    # mic.say(_('Pardon?'))
                    continue

                # Here I have the chance to catch
                # some commonly misheard phrases
                if("GO SELF" in text):
                    self._logger.debug('GO SELF corrected to GO SOUTH')
                    text = "GO SOUTH"
                if("WHERE ROBE" in text):
                    self._logger.debug('WHERE ROBE corrected to WEAR ROBE')
                    text = "WEAR ROBE"

                if("QUIT" in text):
                    mode_not_stopped = False
                else:
                    response = t.execute_command(text)
                    say_location = False
                    # Don't state the location at the beginning of each
                    # response
                    # For the most part, only state the location when
                    # the location changes or if I ask for "look" or
                    # "where am i"
                    if(current_location != response.location):
                        current_location = response.location
                        say_location = True
                    if(text == ['LOOK'] or text == ['WHERE AM I']):
                        say_location = True
                    if(not response.description):
                        say_location = True
                    if(say_location):
                        self._mic.say(response.location)
                    if(response.description):
                        self._mic.say(response.description)

        self._mic.say(self.gettext('Saving game'))
        t.save(self.savefile)
        t.quit()
        self._mic.say(self.gettext('Ending game'))
        self._logger.debug("Frotz mode stopped.")

    def is_valid(self, text):
        """
        Returns True if the input should activate this plugin.

        Arguments:
        text -- user-input, typically transcribed speech
        """
        return any(p.lower() in text.lower() for p in self.get_phrases())
