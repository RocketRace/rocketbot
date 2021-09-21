# -*- coding: utf-8 -*-

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from discord.ext import commands

if TYPE_CHECKING:
    from bot import Bot, Ctx
else:
    Ctx = commands.Context

class Errors(commands.Cog):
    '''A custom error handler for unhandled exceptions.'''

    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx: Ctx, error: commands.CommandInvokeError):
        error = getattr(error, "original", error)
        
        ignored = (commands.CommandNotFound, commands.NotOwner, commands.CheckFailure)
        if isinstance(error, ignored):
            return
        
        elif isinstance(error, commands.MissingRequiredArgument):
            return await ctx.boom("Missing required arguments...")

        await ctx.log(level=logging.ERROR, exc=error)
        await ctx.boom(f"{error.__class__.__name__}: {error}")

def setup(bot: Bot):
    bot.add_cog(Errors(bot))
