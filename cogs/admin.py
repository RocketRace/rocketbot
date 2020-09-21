# -*- coding: utf-8 -*-

from discord.ext import commands
import discord

class Admin(commands.Cog):
    '''Bot administration commands.'''

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.is_owner()
    async def logout(self, ctx):
        await ctx.cs.close()
        await ctx.rocket()
        await self.bot.logout()
    
    @commands.command()
    @commands.is_owner()
    async def load(self, ctx, cog):
        self.bot.load_extension("cogs." + cog)
        await ctx.rocket()

def setup(bot):
    bot.add_cog(Admin(bot))
