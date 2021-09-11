# -*- coding: utf-8 -*-

from __future__ import annotations

import re
from typing import TYPE_CHECKING

import discord
from discord.ext import commands

discord.Message

if TYPE_CHECKING:
    from bot import Bot, Ctx
else:
    Ctx = commands.Context

class Tools(commands.Cog):
    """Convenience commands designed to be unobtrusive"""

    def __init__(self, bot: Bot):
        self.bot = bot

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
        It just adds reactions.
        '''
        # This determines if a line starts with emoji.
        #
        # Custom emoji are easy to parse out.
        # 
        # Instead of using a stupid and unmaintainable unicode emoji regex, 
        # this uses heuristics and Discord 400s to parse built-in emoji.
        custom_emoji_regex = re.compile(r"<a?:[a-zA-Z0-9_]{2,32}:[0-9]{18,22}>")
        definitely_not_emoji_regex = re.compile(r"[\x21-\x3B\x3D\x3F-\x7E]")
        lines = [line.split(None, 1)[0] for line in msg.splitlines() if " " in line]
        for maybe_emoji in lines:
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

def setup(bot: Bot):
    bot.add_cog(Tools(bot))
