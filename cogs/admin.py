# -*- coding: utf-8 -*-

from discord.ext import commands
import discord
import logging

class Admin(commands.Cog, command_attrs=dict(hidden=True)):
    '''Bot administration commands.'''

    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        return await self.bot.is_owner(ctx.author)

    @commands.command()
    async def logout(self, ctx):
        await ctx.session.close()
        await ctx.db.close()
        await ctx.rocket()
        await self.bot.logout()
    
    @commands.command()
    async def load(self, ctx, *cogs):
        if len(cogs) == 0:
            for cog in self.bot.cog_names:
                self.bot.reload_extension(cog)
        else:
            for cog in cogs:
                self.bot.reload_extension("cogs." + cog)
        await ctx.rocket()

    @commands.command()
    async def playing(self, ctx, *, message):
        await commands.Bot.change_presence(activity=discord.Game(message) or None)

    @commands.command()
    async def log(self, ctx):
        for i in range(10):
            await ctx.log()
        await ctx.rocket()

def setup(bot):
    bot.add_cog(Admin(bot))
