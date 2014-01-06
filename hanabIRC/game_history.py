from GameResponse import GameResponse
import yaml
import time
import os
import logging
import re

log = logging.getLogger(__name__)

class game_history(object):
    hist_file = None
    max_last_games = 512

    @staticmethod
    def add_game(score, players, game_type, channel):
        hist = game_history._get_hist()
        hist['last_games'].append([time.time(), score, players, game_type, channel])
        # trim
        hist['last_games'][:] = hist['last_games'][-game_history.max_last_games:]
        game_history._put_hist(hist)

    @staticmethod
    def last_games(nick, n=10, search_string=None):
        gr = GameResponse()
        hist=game_history._get_hist()
        if not len(hist):
            return GameResponse(retVal=False)
        
        if not search_string:
            gr.private[nick].append('Results of the last %d games:' % n)
        else:
            pattern = re.compile(search_string)
            gr.private[nick].append('Results of the last %d games filtered by '
                                    '%s:' % (n, search_string))

        count = 0
        # extended slice syntax reverses list
        for game in sorted(hist['last_games'][::-1]): 
            time_str = time.strftime("%y-%m-%d %H:%M", time.gmtime(game[0]))
            game_str = 'At %s in %s - score: %d, type: %s, players: %s' % (
                time_str, game[4], int(game[1]), game[3], ', '.join(game[2]))

            if not search_string:
                gr.private[nick].append(game_str)
                count += 1
            else:
                m = pattern.search(game_str)
                if m:
                    gr.private[nick].append(game_str)
                    count += 1

            if count > n-1:
                break

        return gr

    @staticmethod
    def _get_hist():
        if not os.path.exists(game_history.hist_file):
            hist = dict()
            hist['last_games'] = []
        else: 
            with open(game_history.hist_file, 'r') as fd:
                hist = yaml.safe_load(fd)

        return hist

    @staticmethod
    def _put_hist(hist):
        if not os.path.exists(game_history.hist_file):
            d = os.path.dirname(game_history.hist_file)
            if d and not os.path.exists(d):
                try:
                    os.makedirs(d)
                except OSError as e:
                    log.error('Unable to make hist file dir %s: %s' % (d, e))
                    return
        
        # this is remarkably wasteful. rewrites the entire file when 
        # only a single entry may have been added.
        with open(game_history.hist_file, 'w') as fd:
            fd.write(yaml.safe_dump(hist))

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    game_history.hist_file = 'game.hist.test'
    game_history.add_game(12, ['joe', 'henry'], 'standard', '#hanbabIRC')
    game_history.add_game(14, ['joe', 'sandy'], 'standard', '#hanbabIRC2')
    game_history.add_game(24, ['joe', 'sandy'], 'rainbow 5', '#hanbabIRC2')

    print game_history.last_games('nicolas')

    os.unlink(game_history.hist_file)
