from GameResponse import GameResponse
import yaml
import time
import os

class game_history(object):
    hist_file = None
    max_last_games = 512

    @staticmethod
    def add_game(score, players, channel):
        hist = game_history._get_hist()
        hist['last_games'].append([time.time(), score, players, channel])
        # trim
        hist['last_games'][:] = hist['last_games'][-game_history.max_last_games:]
        game_history._put_hist(hist)

    @staticmethod
    def last_games(n=10):
        gr = GameResponse()
        hist=game_history._get_hist()
        if not len(hist):
            return GameResponse(retVal=False)

        gr.public.append('Results of the last %d games:' % n)
        for game in sorted(hist['last_games'][-n:]):
            print 'game:', game
            gr.public.append('In %s - score: %d, players: %s' % (
                game[3], int(game[1]), ', '.join(game[2])))

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
            try:
                os.makedirs(os.path.dirname(game_history.hist_file))
            except OSError as e:
                log.warn('Unable to create history file. Most likely permission '
                         'denied.')
                return

        with open(game_history.hist_file, 'w') as fd:
            fd.write(yaml.safe_dump(hist))

if __name__ == "__main__":
    game_history.hist_file = 'game.hist.test'
    game_history.add_game(12, ['joe', 'henry'], '#hanbabIRC')
    game_history.add_game(14, ['joe', 'sandy'], '#hanbabIRC2')
    game_history.add_game(24, ['joe', 'sandy'], '#hanbabIRC2')

    print game_history.last_games()
