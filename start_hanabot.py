
import argparse
import logging
import sys
from hanabot import Hanabot

# logger for this module/file
log = logging.getLogger(__name__)

if __name__ == "__main__":
	'''main function for hanabot: parse args, create bot state, connect to server/channel, run bot.'''
	desc = 'hanabot manages games of Hanabi on IRC.'
	argparser = argparse.ArgumentParser(description=desc)
	argparser.add_argument('-s', '--server', type=str, dest='server', required=True, 
						help='The IRC server to connect to.')
	argparser.add_argument('-c', '--channel', type=str, dest='channel', required=True, 
						help='The IRC #channel to connect to.')
	argparser.add_argument('-l', '--loglevel', type=str, dest='loglevel', default='info', 
						choices=['debug', 'info', 'warning', 'error', 'critical'], 
						help='Set the global log level')
	args = argparser.parse_args()

	# adjust logging level
	logLevels = {
		'debug': logging.DEBUG, 
		'info': logging.INFO, 
		'warning': logging.WARNING,
		'error': logging.ERROR, 
		'critical': logging.CRITICAL
	}
	hdlr = logging.StreamHandler()
	hdlr.setFormatter(logging.Formatter('%(asctime)s %(name)-12s %(levelname)-8s %(threadName)s %(message)s', '%m-%d %H:%M:%S'))
	root = logging.getLogger()
	root.handlers = []
	root.addHandler(hdlr)
	root.setLevel(logLevels[args.loglevel])
	#irc = logging.getLogger('irc')
	#irc.setLevel(logging.INFO)
	log.info('set log level to %s (%d)' % (args.loglevel, logLevels[args.loglevel]))

	# ok - now we can do some actual work.	
	bot = Hanabot(args.server, args.channel)	
	bot.start()



