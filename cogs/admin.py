# -*- coding: utf-8 -*-

from bot import Bot, Context
from discord.ext import commands
import discord
import logging
import dbouncer
from datetime import timedelta

class Admin(dbouncer.DefaultBouncer, command_attrs=dict(hidden=True)):
    '''Bot administration commands.'''

    def __init__(self, bot: Bot):
        self.bot = bot
        super().__init__(
            min_guild_age=timedelta(days=1),
            min_members=5
        )

    async def after_leave(self, guild: discord.Guild, *, new: bool):
        await self.bot.log_raw(
            level=logging.WARN,
            message=f"Guild `{guild.name}` (ID: {guild.id}`) left automatically. Guild count: {len(self.bot.guilds)}"
        )

    async def cog_check(self, ctx: Context):
        return await self.bot.is_owner(ctx.author)

    @commands.command()
    async def logout(self, ctx: Context):
        await ctx.session.close()
        await ctx.db.close()
        await ctx.rocket()
        await self.bot.logout()
    
    @commands.command()
    async def load(self, ctx: Context, *cogs):
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

def setup(bot: Bot):
    bot.add_cog(Admin(bot))
