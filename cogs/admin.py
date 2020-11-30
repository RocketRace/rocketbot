# -*- coding: utf-8 -*-

from asyncio import subprocess
from .utils.models import Bot, Context
from discord.ext import commands, menus # type: ignore
import discord
import logging
import asyncio
import dbouncer
from datetime import timedelta

class EasyPaginator(menus.ListPageSource):
    def __init__(self, data):
        super().__init__(data, per_page=1)
    async def format_page(self, menu, page):
        return f"{page}\n`Page {menu.current_page}/{len(self.entries) - 1}`"

class Admin(dbouncer.DefaultBouncer, command_attrs=dict(hidden=True)): # type: ignore
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

    async def run_shell(self, command: str, ctx: Context, *, typing: bool = False) -> menus.MenuPages:
        '''Run a shell command, obtain output and display it as a menu.'''
        if typing: # Using a with block is a bit difficult here
            await ctx.trigger_typing()
        proc = await asyncio.create_subprocess_shell(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE
        )
        result = await proc.communicate()
        stdout, stderr = (stream.decode() if stream else "" for stream in result)
        merged = stdout + "\n" + stderr
        msgs = [
            f"Return code: {proc.returncode}\n```{merged[i:i+1900]}```"
            for i in range(0, len(merged), 1900)
        ]
        menu = menus.MenuPages(source=EasyPaginator(msgs), delete_message_after=True)
        await menu.start(ctx)
        return menu

    async def cog_check(self, ctx: Context):
        return await self.bot.is_owner(ctx.author)

    @commands.command()
    async def sh(self, ctx: Context, *, cmd: str):
        await self.run_shell(cmd, ctx, typing=True)

    @commands.command(aliases=["yeet"])
    async def logout(self, ctx: Context):
        await ctx.session.close()
        await ctx.db.close()
        await ctx.rocket()
        await self.bot.logout()
    
    @commands.group(invoke_without_command=True)
    async def load(self, ctx: Context, *cogs):
        if len(cogs) == 0:
            for cog in self.bot.cog_names:
                self.bot.reload_extension(cog)
        else:
            for cog in cogs:
                self.bot.reload_extension("cogs." + cog)
        self.bot.dispatch("initialized")
        await ctx.rocket()

    @load.command(name="all")
    async def _all(self, ctx: Context):
        await self.run_shell("git pull", ctx, typing=True)
        for cog in self.bot.cog_names:
            self.bot.reload_extension(cog)
        await ctx.rocket()

    @commands.command()
    async def playing(self, ctx: Context, *, message):
        activity = discord.Game(message) if message else None
        await self.bot.change_presence(activity=activity)
        await ctx.rocket()

    @commands.command()
    @commands.guild_only()
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
        await ctx.me.edit(nick=new) # type: ignore
        await ctx.rocket()

def setup(bot: Bot):
    bot.add_cog(Admin(
        bot, 
        min_guild_age=timedelta(days=1),
        min_members=5
    ))
