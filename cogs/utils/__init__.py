# -*- coding: utf-8 -*-
'''
Utility functions for the benefit of the bot.

Worth using elsewhere, too
'''

from datetime import timedelta

def humanize_duration(td: timedelta, millis: bool = False) -> str:
    '''Returns a human-friendly string representing a duration'''
    out = ""
    total = td.total_seconds()
    days, total = divmod(total, 24 * 60 * 60)
    if days != 0:
        out += f"{int(days)} days, "
    hours, total = divmod(total, 60 * 60)
    if hours != 0:
        out += f"{int(hours)} hours, "
    minutes, total = divmod(total, 60)
    if minutes != 0:
        out += f"{int(minutes)} mins, "
    seconds, rest = divmod(total, 1)
    if seconds != 0:
        out += f"{int(seconds)} secs, "
    if millis and rest * 1000 != 0:
        out +=  f"{int(rest * 1000)} ms, "
    return out[:-2]