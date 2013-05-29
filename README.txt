
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

You may want to save the log file and run it in the background:

> hanabIRC 2>&1 > hanabIRC.log & 

History
=======

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
- remove rainbow after added and game ends.
