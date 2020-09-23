# -*- coding: utf-8 -*-

from discord.ext import commands
import discord
import logging

class Errors(commands.Cog):
    '''A custom error handler for unhandled exceptions.'''

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        error = getattr(error, "original", error)
        await ctx.log(level=logging.ERROR, exc=error)
        
        ignored = (commands.CommandNotFound, commands.NotOwner)
        if isinstance(error, ignored):
            return

        embed = discord.Embed(
            title=error.__class__.__name__,
            description=str(error),
            color=ctx.color,
        )
        await ctx.boom(embed=embed)

def setup(bot):
    bot.add_cog(Errors(bot))
