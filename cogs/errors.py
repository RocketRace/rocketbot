# -*- coding: utf-8 -*-

from .utils.models import Bot, Context
from discord.ext import commands
import discord
import logging

class Errors(commands.Cog):
    '''A custom error handler for unhandled exceptions.'''

    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx: Context, error: commands.CommandInvokeError):
        error = getattr(error, "original", error)
        
        ignored = (commands.CommandNotFound, commands.NotOwner, commands.CheckFailure)
        if isinstance(error, ignored):
            return

        await ctx.log(level=logging.ERROR, exc=error)
        await ctx.boom(f"{error.__class__.__name__}: {error}")

def setup(bot: Bot):
    bot.add_cog(Errors(bot))
