# -*- coding: utf-8 -*-

from discord import activity
from .utils.models import Bot, Context
from discord.ext import commands
import discord
import logging
import dbouncer
from datetime import timedelta

class Admin(dbouncer.DefaultBouncer, command_attrs=dict(hidden=True)):
    '''Bot administration commands.'''

    async def after_leave(self, guild: discord.Guild, *, new: bool):
        await self.bot.log_raw(
            level=logging.DEBUG,
            message=f"Guild `{guild.name}` (ID: {guild.id}`) left automatically. Guild count: {len(self.bot.guilds)}"
        )
    
    async def on_guild_limit_reached(self, guild: discord.Guild):
        await self.bot.log_raw(
            level=logging.WARN,
            message=f"Guild `{guild.name}` (ID: {guild.id}`) left automatically. Guild count: {len(self.bot.guilds)}!"
        )

    async def cog_check(self, ctx: Context):
        return await self.bot.is_owner(ctx.author)

    @commands.command(aliases=["yeet"])
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
    async def playing(self, ctx: Context, *, message):
        activity = discord.Game(message) if message else None
        await self.bot.change_presence(activity=activity)
        await ctx.rocket()

    @commands.command()
    @commands.bot_has_permissions(change_nickname=True)
    async def nick(self, ctx: Context):
        nick = ctx.author.display_name
        long = "\u0363\u0367\u036d\u0366\u036b\u0363\u036d\u0364\u0369"
        short = "\u0363\u0367\u036d\u0366"
        if len(nick) > len(long):
            overlay = long
        elif len(short) <= len(nick) < len(long):
            overlay = short
        else:
            return await ctx.boom("Nick too short")
        new = "".join([*map("".join, zip(nick, overlay))]) + nick[len(overlay):]
        await ctx.me.edit(nick=new)
        await ctx.rocket()

def setup(bot: Bot):
    bot.add_cog(Admin(
        bot, 
        min_guild_age=timedelta(days=1),
        min_members=5
    ))
