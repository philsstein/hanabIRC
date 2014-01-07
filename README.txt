========
HanabIRC
========

An IRC bot that organizes and plays the card game Hanabi.

Installing and running the hanabot:
-----------------------------------
To run the game on your own channel do the following:

Download and install hanabIRC and dependencies:

> sudo pip install hanabIRC

Generate a default configuration file:

> sudo hanabIRC --makeconf > /etc/hanabIRC.conf

Edit the default configuration:

> vi /etc/hanabIRC.conf

Run the bot:

> hanabIRC

You may want to run the bot in screen or tmux.

> tmux 
> hanabIRC 2>&1 | tee hanabot.log
> ^B-d  # to unattach from tmux.

History
=======
* 2014-01-07 - Version 1.1.03 - bugfix for new !last syntax.
* 2014-01-06 - Version 1.1.02 - added optional 3rd arg to !last, a pattern. If given only display game strings that contain that pattern.
* 2013-11-29 - Version 1.1.0001 - Stop abuse of !last by Chank.
* 2013-11-04 - Version 1.1.0 - Bold the Table line in addition to underline to make it stand out.
* 2013-10-31 - Version 1.0.99 - Revert auto-join, was causing odd effects. Use light cyan for blue color. 
* 2013-10-30 - Version 1.0.98 - Use mIRC black color for all color backgrounds. Easier for non-black-background clients.
* 2013-10-29 - Version 1.0.97 - Fixed, hopefully, the notice about no hints remaining. 
* 2013-10-29 - Version 1.0.96 - Do not add obviously unplayed games to game history log.
* 2013-10-29 - Version 1.0.95 - Devoice on game end. Devoice on !leave always.
* 2013-10-29 - Version 1.0.94 - !Join will start a new game if there is not one in the channel already. voice/devoice fixes.
							     Disable !die command.
* 2013-10-29 - Version 1.0.93 - Remove !die command. Voice players in game. Add note when thre are no hints remaining.
* 2013-10-01 - Version 1.0.91 - Fix another speling error.
* 2013-09-17 - Version 1.0.9 - Fix speling error.
* 2013-09-09 - Version 1.0.8 - Do not show whose turn it is if not in game. 
* 2013-09-09 - Version 1.0.7 - Do not allow someone to both watch and play the game!
* 2013-09-07 - Version 1.0.6 - Reformat date in !last listing
                             - Added !watch command so people can observer the game (see the hands as they change)
                                use !leave to leave the game as an observer.
* 2013-09-06 - Version 1.0.5 - added rate limiting to bot output. should ease the bot-kicked-from-flooding problem.
                             - added timestamps to game history listing
* 2013-08-03 - Version 1.0.4 - Added support for showing all hints given by doing "!hints all". 
* 2013-08-02 - Version 1.0.3 - End game with zero points when all storms flipped.
* 2013-07-25 - Version 1.0.2 - Show game type in !last output. 
* 2013-07-21 - Version 1.0.1 - Show !last only to nick that requested it in order to not ping people in channel. 
* 2013-07-21 - Version 1.0.0 - Same as 0.2.5
* 2013-07-21 - Version 0.2.50 - !last n command added: show results for the last N games. History is persistant across restarts. 
* 2013-07-18 - Version 0.2.40 - Can have multiple home channels now.
* 2013-07-17 - Version 0.2.35 - Make repeat_backs == False the default.
* 2013-07-13 - Version 0.2.34 - Tweak to !hints to fix oddness when used before game starts.
* 2013-07-13 - Version 0.2.33 - New command !hints shows all hints given to the user during current game.
* 2013-07-12 - Version 0.2.32 - Handle card back wrap around correctly in A-Z case.
* 2013-07-12 - Version 0.2.31 - added game options. one option so far: repeat_backs. If False use A-Z for card backs, else A-E
* 2013-07-07 - Version 0.2.3 - Fix empty command ("!") error. 
* 2013-06-21 - Version 0.2.2 - Fix underline control code - 0x1f instead of 0x15. Also use lighter blue and green to make a little more visible.
* 2013-06-20 - Version 0.2.1 - Underline "Table" line to make it stand out a bit more.
* 2013-05-31 - Version 0.2.0 - Fix misspeling.
* 2013-05-28 - Version 0.1.25 - Do not show turn or hands privately on last turn. 
* 2013-05-28 - Version 0.1.24 - Show turns remaining on table once deck is empty.
* 2013-05-28 - Version 0.1.23 - Make rainbow card display consistant: "RNBW".
* 2013-05-27 - Version 0.1.22 - Only people in the game can !stop it. 
* 2013-05-27 - Version 0.1.21 - More rainbow updates. Delete a game at !stop.
* 2013-05-27 - Version 0.1.20 - Rainbow updates. Display chan name in !games. Correctly delete a game when it's over. 
* 2013-05-27 - Version 0.1.19 - Bug fix for rainbow game.
* 2013-05-24 - Version 0.1.18 - Fix partial colors given as clues handling. Order hands alphabetically. 
* 2013-05-24 - Version 0.1.17 - Allow "invalid" hints to be given and count them as a real hint.
* 2013-05-22 - Version 0.1.16 - Fix (again) fencepost error of last turns at game end. Count hint as a turn in last turns.
* 2013-05-15 - Version 0.1.15 - Show hands of all players at end of game.
* 2013-05-14 - Version 0.1.14 - Fix fencepost error when computing end of game due to end of deck.
* 2013-05-07 - Version 0.1.13 - Use /msg for table display soas to not disturb people in the channel, but not playing. Sort table and discard piles in the same way.
* 2013-04-18 - Version 0.1.12 - Bug fix. 
* 2013-04-17 - Version 0.1.11 - Bug fix in !game and !games command.
* 2013-04-17 - Version 0.1.10 - Display table in same compact form as the discard pile. New command !stop immediately stops and scores the game. Only players can !stop a game. 
* 2013-04-12 - Version 0.1.9 - Dicard pile display is more compact. Can add 5 or 10 rainbow cards (instead of just 5). Post-game action bug squashed. Do not prefix # to channel in !new if it is already there.
* 2013-04-12 - Version 0.1.8 - sort discard pile, notes, and storms. 
* 2013-03-11 - Version 0.1.7 - notify channel works. If "notify_channel" given in the configuration file, that channel will get a notification when a new game begins (regardless of which channel it starts in.) 
* 2013-03-10 - Version 0.1.6 - everyone now gets one more turn when the deck empties before the game ends.
* 2013-02-24 - Version 0.1.5 - added support for hanabot talking to all players during move. Current player notified when it is his/her turn. Fixed bug that caused Hanabot to ignore privmsgs. Everyone now gets notified of all player's hands at the start of a turn.
* 2013-02-14 - Version 0.1.4 - added support for rainbow cards. When starting a game, add "rainbow" to start command to use them: "!start rainbow".
* 2013-02-14 
	- Added mutli-channel support. Hanbot can now run in multiple channels, keeping track of multiple games.
	- Enforce one person per game
	- Use NOTICE instead of prvimsg to display text inline to user/channel.
* 2013-02-13 - Interface updates after user feedback.
* 2013-02-13 - Initial creation. (See git logs for history.)

TODO:
-----
- do not print hint to channel if given in a PRIVMSG
- add total time game took at end game?
- keep stats?
- add user-configured color to the bot
- add !replace command to replace people in-game
- add actual rules text
- make sure when a player leaves, they do not still get PMs.
- remove redundant need to specify player name in !hint command in two player games.
