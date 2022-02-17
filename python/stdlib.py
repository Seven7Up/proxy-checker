#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import argparse
import signal
from sys import exit

from colorama import Back, Fore
from colorama import init as colorama_init


class CapitalisedHelpFormatter(argparse.HelpFormatter):
    def add_usage(self, usage, actions, groups, prefix=False):
        if not prefix:
            prefix = "Usage: "
        return super(CapitalisedHelpFormatter, self).add_usage(usage, actions, groups, prefix)


class LocalParser(argparse.ArgumentParser):
    def __init__(self, formatter_class=CapitalisedHelpFormatter, *args, **kwargs):
        super().__init__(formatter_class=formatter_class, *args, **kwargs)

    def error(self, message):
        print("Error: %s" % message)
        self.print_help()
        exit(1)


def getindex(tocheck_01, value, tocheck_02=False):
    if type(tocheck_01[0]) == tuple:
        for i, (k, v) in enumerate(tocheck_01):
            if v == value:
                return (i, k, v)
        return 1
    elif tocheck_02:
        for i, (k, v) in enumerate(zip(tocheck_01, tocheck_02)):
            if v == value:
                return (i, k, v)
        return 1
    else:
        raise Exception("Error in getindex() args!")


class levels:
    NOSET = 0
    CRITICAL = 1
    WARNING = 2
    # 3 is not set
    INFO = 4
    DEBUG = 5


class msgtype_prefixes:
    # msg_type = [color, prefix, indent]
    info = [Fore.BLUE, "*", 4]
    success = [Fore.GREEN, "+", 4]
    error = [Fore.RED, "-", 4]
    warn = [Fore.YELLOW, "!", 4]
    critical = [Back.RED, "CRITICAL", 11]
    debug = [Fore.MAGENTA, "DEBUG", 8]


class Logger(object):
    def __init__(self, name=False, level=levels.INFO):
        colorama_init()
        self.name = name
        self.level = level

    def setlevel(self, level):
        if level in list(levels.__dict__.values()):
            self.level = level
            return 0
        else:
            self.error(
                "Level Error: You've set a wrong Level value(%s)!" % level)
            return 1

    def getlevel(self, string=False):
        if string:
            index = getindex(list(levels.__dict__.items()), self.level)
            if index == 1:
                self.critical(
                    "Error in Logger object: Cannot get %s index!?!" % self.level)
                exit(1)

            level_name = index[1]
            return level_name
        else:
            return self.level

    def log(self, string, msgtype, file=False):
        if not file:
            from sys import stdout
            file = stdout

        msg = ""
        if msgtype in dir(msgtype_prefixes):
            color, prefix, indent = getattr(msgtype_prefixes, msgtype)
            msg += "[%s%s%s] " % (color, prefix,
                                  # I'll search to find an advanced way to check this, but now I'll leave like that for the next time
                                  Fore.RESET if msgtype != "critical" else Back.RESET)
        else:
            msg += "[?] "
            indent = 4

        if self.name:
            msg = "%s: %s" % (self.name, msg)

        msg += string
        msg = ("\n" + (" " * indent)).join(msg.splitlines())
        print(msg, file=file)

    def info(self, string):
        if self.level < levels.INFO:
            return 1
        self.log(string, "info")
        return 0

    def success(self, string):
        if self.level < levels.INFO:
            return 1
        self.log(string, "success")
        return 0

    def error(self, string):
        if self.level < levels.INFO:
            return 1
        self.log(string, "error")
        return 0

    def warn(self, string):
        if self.level < levels.WARNING:
            return 1
        self.log(string, "warn")
        return 0

    def critical(self, string):
        if self.level < levels.CRITICAL:
            return 1
        self.log(string, "critical")
        return 0

    def debug(self, string):
        if self.level < levels.DEBUG:
            return 1
        self.log(string, "debug")
        return 0


def init_killer():
    def hdl(*args):
        exit(0)

    signal.signal(signal.SIGINT, hdl)
    signal.signal(signal.SIGQUIT, hdl)
