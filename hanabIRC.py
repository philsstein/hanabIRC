
import argparse
import logging
import sys
import os

from ConfigParser import SafeConfigParser
from hanabot import Hanabot

# logger for this module/file
log = logging.getLogger(__name__)

if __name__ == "__main__":
    '''
        main function for hanabot: parse args, create bot state,
        connect to server/channel, run bot.
    '''
    desc = 'hanabot manages games of Hanabi on IRC.'
    argparser = argparse.ArgumentParser(description=desc)
    argparser.add_argument('-s', '--server', type=str, dest='server',
                           help='The IRC server to connect to.')
    argparser.add_argument('-c', '--channel', type=str, dest='channel',
                           help='The IRC #channel to connect to.')
    argparser.add_argument('-l', '--loglevel', type=str, dest='loglevel',
                           default='info', choices=['debug', 'info',
                                                    'warning', 'error',
                                                    'critical'],
                           help='Set the global log level')
    argparser.add_argument('--config', type=str, dest='conffile',
                           help='Configuration file. Command line will '
                                'override values found here.')
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
    hdlr.setFormatter(logging.Formatter('%(asctime)s %(name)-12s '
                                        '%(levelname)-8s %(threadName)s '
                                        '%(message)s', '%m-%d %H:%M:%S'))
    root = logging.getLogger()
    root.handlers = []
    root.addHandler(hdlr)
    root.setLevel(logLevels[args.loglevel])
    #irc = logging.getLogger('irc')
    #irc.setLevel(logging.INFO)
    log.info('set log level to %s (%d)' % (args.loglevel,
                                           logLevels[args.loglevel]))

    # Read in configuration file of it exists or is given.
    conffilename = 'hanabIRC.conf'
    configfiles = [os.path.expanduser('~/.%s' % conffilename),
                   '/etc/%s' % conffilename,
                   conffilename]
    if args.conffile:
        configfiles.insert(0, args.conffile)

    confparse = SafeConfigParser()
    files = confparse.read(configfiles)

    if not confparse.has_section('general'):
        log.critical('No [general] section found in configuration file.')
        sys.exit(1)

    server = confparse.get('general', 'server')
    channel = confparse.get('general', 'channel')

    server = args.server if args.server else server
    channel = args.channel if args.channel else channel

    # GTL - uncomment these once they are supported.
    # port = args.port if args.port else conf.port
    # notify_port = args.notify_port if args.notify_port else conf.notify_port

    # ok - now we can do some actual work.
    bot = Hanabot(server, channel)
    bot.start()
