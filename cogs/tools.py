# -*- coding: utf-8 -*-

from __future__ import annotations

import re
import string
import unicodedata
from typing import TYPE_CHECKING

import discord
from discord.ext import commands

if TYPE_CHECKING:
    from bot import Bot, Ctx
else:
    Ctx = commands.Context

class Tools(commands.Cog):
    """Convenience commands designed to be unobtrusive"""

    def __init__(self, bot: Bot):
        self.bot = bot
        self.keycaps: dict[str, str] = {}
        self.define_keycaps()

    def define_keycaps(self):
        '''Adds some shorthands for keycaps'''
        # Numbers
        for i in range(10):
            self.keycaps[str(i)] = f"{i}\uFE0F\u20E3" # vs-16, enclosing keycap
        self.keycaps["10"] = "\U0001F51F" # keycap 10

        # Letters
        for c in string.ascii_lowercase:
            self.keycaps[c] = chr(ord(c) - ord('a') + ord("\U0001F1E6")) # regional indicator A

    @commands.command(name="poll:")
    async def poll(self, ctx: Ctx, *, msg: str):
        '''Parses a poll request from a message and adds the parsed reactions.
        
        An example command could be something like:
        ```
        poll: Should I go outside
        
        :sunflower: Yes
        :computer: No
        
        I'll definitely go but I just want to feel validated / superior :slight_smile:
        ```

        The bot will then parse out the :sunflower: and :computer: emoji from the message,
        and add those as reactions. 
        
        This is *not* an overengineered poll command with embeds and timeouts and whatever.
        It just adds reactions. (Okay, it's a little overengineered.)
        '''
        # This determines if a line starts with emoji.
        #
        # Custom emoji are easy to parse out.
        # 
        # Instead of using a stupid and unmaintainable unicode emoji regex, 
        # this uses heuristics and Discord 400s to parse built-in emoji.
        custom_emoji_regex = re.compile(r"<a?:[a-zA-Z0-9_]{2,32}:[0-9]{18,22}>")
        definitely_not_emoji_regex = re.compile(r"[\x21-\x3B\x3D\x3F-\x7E]")
        lines = [line.split(None, 1)[0] for line in msg.splitlines() if line and not line.isspace()]
        for maybe_emoji in lines:
            # numbers and letters are cool
            try:
                shorthand = maybe_emoji.removesuffix(":").strip().lower()
                await ctx.message.add_reaction(self.keycaps[shorthand])
            except KeyError as e:
                pass
            # An incomplete match is enough to rule this out
            if definitely_not_emoji_regex.match(maybe_emoji) is not None:
                continue
            # This is definitely a custom emoji
            if custom_emoji_regex.match(maybe_emoji) is not None:
                try:
                    await ctx.message.add_reaction(maybe_emoji)
                except discord.Forbidden:
                    return await ctx.send(f"I can't react with {maybe_emoji}")
                except discord.HTTPException as exc:
                    if exc.status == 400:
                        return await ctx.boom(f"I have no access to {maybe_emoji}")
            # This *could* be a unicode emoji, but we'll have to check to be sure
            else:
                try:
                    await ctx.message.add_reaction(maybe_emoji)
                except discord.Forbidden:
                    return await ctx.send(f"I can't react with {maybe_emoji}")
                # Not valid
                except discord.HTTPException:
                    pass
    
    @commands.command(aliases=["charinfo", "char"])
    async def chars(self, ctx: Ctx, *, string: str):
        '''Return character info for a string'''
        out = []
        width = 4
        for c in string:
            num = f"{ord(c):x}"
            if len(num) <= 2:
                escape = f"\\x{num:0>2}"
            elif len(num) <= 4:
                escape = f"\\u{num:0>4}"
                width = max(width, 6)
            else:
                escape = f"\\U{num:0>8}"
                width = max(width, 10)
            name = unicodedata.name(c, "<name missing>")
            out.append(f"`{escape: <{width}}`: `{c}` `{name.upper()}`")
        
        result = "\n".join(out)
        if len(result) > 2000:
            return await ctx.boom("Result too long")
        await ctx.send(result)

def setup(bot: Bot):
    bot.add_cog(Tools(bot))
