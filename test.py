from hanabi import Game, Player, Card
from text_markup import xterm_markup

def display(lists):
    for lines in [('Public:', lists[0]), ('Private:', lists[1])]:
        print lines[0]
        if not len(lines[1]):
            print '\t ---'
        else:
            for l in lines[1]:
                print '\t', l

g = Game('foobar', xterm_markup())
display(g.add_player('Olive'))
display(g.get_status('Olive', show_all=True))
display(g.add_player('Maisie'))
display(g.add_player('Jasper'))
display(g.add_player('George'))
display(g.add_player('Frank'))
display(g.add_player('One Too Many'))
display(g.show_game_state())
display(g.remove_player('George'))
display(g.show_game_state())
display(g.start_game())
display(g.remove_player('Maisie'))

# cheat and force Olive to have red: 12345 and Jasper tohave yellow 12345
g.players['Olive'].hand = [Card(xterm_markup.RED, i+1, g.markup) for i in range(5)]
g.players['Jasper'].hand = [Card(xterm_markup.YELLOW, i+1, g.markup) for i in range(5)]
g.players['Frank'].hand = [Card(xterm_markup.GREEN, i+1, g.markup) for i in range(5)]

# force turn order
g.turn_order = ['Olive', 'Jasper', 'Frank']
display(g.get_status('Olive', show_all=True))
display(g.play_card('Olive', 1))
display(g.play_card('Jasper', 3))
display(g.play_card('Frank', 3))
display(g.play_card('Olive', 1))
display(g.play_card('Jasper', 1))
display(g.play_card('Frank', 3))
display(g.play_card('Olive', 1))
display(g.show_game_state())
