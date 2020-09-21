# -*- coding: utf-8 -*-

from discord.ext import commands
import discord

class Admin(commands.Cog, command_attrs=dict(hidden=True)):
    '''Bot administration commands.'''

    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        return await self.bot.is_owner(ctx.author)

    @commands.command()
    async def logout(self, ctx):
        await ctx.cs.close()
        await ctx.rocket()
        await self.bot.logout()
    
    @commands.command()
    async def load(self, ctx, *cogs):
        for cog in cogs:
            self.bot.load_extension("cogs." + cog)
        await ctx.rocket()

    @commands.command()
    async def playing(self, ctx, *, message):
        await commands.Bot.change_presence(activity=discord.Game(message) or None)

def setup(bot):
    bot.add_cog(Admin(bot))
