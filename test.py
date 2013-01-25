from hanabi import Game
from text_markup import xterm_markup

def printLines(lines):
	for l in lines:
		print l

g = Game('foobar', xterm_markup())
printLines(g.add_player('Olive'))
printLines(g.show_game_state())
printLines(g.add_player('Maisie'))
printLines(g.add_player('Jasper'))
printLines(g.add_player('George'))
printLines(g.add_player('Frank'))
printLines(g.add_player('One Too Many'))
printLines(g.show_game_state())
printLines(g.remove_player('Olive'))
printLines(g.show_game_state())


