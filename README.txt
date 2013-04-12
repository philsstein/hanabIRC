
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

* 2013-02-13 - Initial creation. (See git logs for history.)
* 2013-02-13 - Interface updates after user feedback.
* 2013-02-14 
	- Added mutli-channel support. Hanbot can now run in multiple channels, keeping track of multiple games.
	- Enforce one person per game
	- Use NOTICE instead of prvimsg to display text inline to user/channel.
* 2013-02-14 - Version 0.1.4 - added support for rainbow cards. When starting a game, add "rainbow" to start command to use them: "!start rainbow".
* 2013-02-24 - Version 0.1.5 - added support for hanabot talking to all players during move. Current player notified when it is his/her turn. Fixed bug that caused Hanabot to ignore privmsgs. Everyone now gets notified of all player's hands at the start of a turn.
* 2013-03-10 - Version 0.1.6 - everyone now gets one more turn when the deck empties before the game ends.
* 2013-03-11 - Version 0.1.7 - notify channel works. If "notify_channel" given in the configuration file, that channel will get a notification when a new game begins (regardless of which channel it starts in.) 
* 2013-04-12 - Version 0.1.8 - sort discard pile, notes, and storms. 
* 2013-04-12 - Version 0.1.9 - Dicard pile display is more compact. Can add 5 or 10 rainbow cards (instead of just 5). Post-game action bug squashed. Do not prefix # to channel in !new if it is already there.


TODO:
-----
- do not print hint to channel if given in a PRIVMSG
- add total time game took at end game?
- keep stats?
- add user-configured color to the bot
- add !replace command to replace people in-game
- add actual rules text
- make sure when a player leaves, they do not still get PMs.
