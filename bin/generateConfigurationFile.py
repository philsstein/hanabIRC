#!/usr/bin/env python

from ConfigParser import SafeConfigParser
import sys
import argparse

if __name__ == "__main__":
    desc = 'Generate a default HanabIRC configuration file to the console'
    argparser = argparse.ArgumentParser(description=desc)
    argparser.add_argument('-o', '--outfile', dest='outfile',
                           help='The name of the file to write the '
                                'configuration to. If not given, write '
                                'to stdout.')
    args = argparser.parse_args()

    section = 'general'
    parser = SafeConfigParser()
    parser.add_section(section)
    parser.set(section, 'server', 'irc.freenode.net')
    parser.set(section, 'channels', 'hanabIRC,playhanabi')
    parser.set(section, 'port', '6667')
    parser.set(section, 'nick', 'hanabot')
    parser.set(section, 'nick_pass', 'PASSWORD')
    parser.set(section, 'topic', 'Welcome to Hanabi on IRC')

    if args.outfile:
        with open(args.outfile, 'wb') as fd:
            parser.write(fd)
    else:
        parser.write(sys.stdout)
