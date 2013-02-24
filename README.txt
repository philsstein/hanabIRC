
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


TODO:
-----
- add support for telling non command issuer stuff. 
	This could be used to show hands to all players
	after a !play, for example.
- do not print hint to channel if given in a PRIVMSG
- add total time game took at end game?
- keep stats?
- add user-configured color to the bot
- PM user with updated hands when it is their turn
- add !replace command to replace people in-game
- add actual rules text
- make sure when a player leaves, they do not still get PMs.
- When you run out of cards, everyone gets one more turn.

