# -*- coding: utf-8 -*-

from asyncio import subprocess
from typing import Union
from .utils.models import Bot, Context
from discord.ext import commands, menus # type: ignore
import discord
import logging
import asyncio
import dbouncer
import textwrap
import contextlib
import io
from datetime import timedelta

class EasyPaginator(menus.ListPageSource):
    def __init__(self, data):
        super().__init__(data, per_page=1)
    async def format_page(self, menu, page):
        return f"{page}\n`Page {menu.current_page}/{len(self.entries) - 1}`"

class Admin(dbouncer.DefaultBouncer, command_attrs=dict(hidden=True)): # type: ignore
    '''Bot administration commands.'''

    def __init__(self, bot: Bot, **kwargs) -> None:
        self.blocked = set()
        self.bot = bot
        self.last_value = None
        super().__init__(bot, **kwargs)
    
    @commands.Cog.listener()
    async def on_initialized(self):
        async with self.bot.cursor() as cur:
            await cur.execute(
                '''
                SELECT id FROM users WHERE blocked == 1;
                '''
            )
            results = await cur.fetchall()
            self.blocked = set(results)

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
    
    @commands.command()
    async def sql(self, ctx: Context, query: str, *args):
        async with ctx.cursor() as cur:
            await cur.execute(
                query,
                args
            )
            result = await cur.fetchall()
        result = f"Success. Results: ```{result}```"
        await ctx.send(result)
    
    @commands.command(name="eval")
    async def eval_python(self, ctx: Context, *, code: str):
        # no code blocks
        if code.startswith("```") and code.endswith("```"):
            code = "\n".join(code.splitlines()[1:-1])
        if code.startswith("`") and code.endswith("`"):
            code = code[1:-1]
        # technically not always valid but is convenient
        if len(code.splitlines()) == 1:
            if not code.strip().endswith(";"):
                code = "return " + code
        
        code = f"async def wrapper():\n{textwrap.indent(code, prefix='  ')}"

        new_globals = globals().copy()
        new_globals.update({
            "bot":self.bot,
            "ctx":ctx,
            "cog":self.bot.get_cog,
            "_":self.last_value
        })
        # Compiles the coroutine and places it into new_globals
        exec(code, new_globals)
        fn = new_globals["wrapper"]
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            value = await fn()
            self.last_value = value
            printed = stdout.getvalue()
            if printed:
                await ctx.send(f"Stdout:\n```\n{printed}\n```\nResult:\n```py\n{value}\n```")
            else:
                await ctx.send(f"Result:\n```py\n{value}\n```")


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

    @load.command()
    async def git(self, ctx: Context):
        await self.run_shell("git pull", ctx, typing=True)
        for cog in self.bot.cog_names:
            self.bot.reload_extension(cog)
        self.bot.dispatch("initialized")

    async def update_presence(
        self,
        ctx: Context,
        kind: discord.ActivityType,
        msg: str
    ):
        if not msg:
            activity = None
        elif kind == discord.ActivityType.playing:
            activity = discord.Game(name=msg)
        else:
            activity = discord.Activity(type=kind, name=msg)
        await self.bot.change_presence(activity=activity)
        await ctx.rocket()

    @commands.command()
    async def playing(self, ctx: Context, *, msg):
        await self.update_presence(ctx, discord.ActivityType.playing, msg)
    
    @commands.command()
    async def watching(self, ctx: Context, *, msg):
        await self.update_presence(ctx, discord.ActivityType.watching, msg)

    @commands.group(invoke_without_command=True)
    async def listening(self, ctx): pass
    @listening.command(name="to")
    async def listening_to(self, ctx: Context, *, msg):
        await self.update_presence(ctx, discord.ActivityType.listening, msg)

    @commands.group(invoke_without_command=True)
    async def competing(self, ctx): pass
    @competing.command(name="in")
    async def competing_in(self, ctx: Context, *, msg):
        await self.update_presence(ctx, discord.ActivityType.competing, msg)

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

    @commands.command()
    async def block(self, ctx: Context, user: Union[discord.User, int]):
        if isinstance(user, discord.User):
            user = user.id
        async with ctx.cursor() as cur:
            await cur.execute(
                '''
                UPDATE users
                SET blocked = 1
                WHERE id == ?;
                ''',
                (user,)
            )
            await cur.execute(
                '''
                INSERT OR IGNORE INTO users (id, blocked)
                VALUES (?, 1);
                ''',
                (user,)
            )
        await ctx.db.commit()
        await ctx.rocket()

    @commands.command()
    async def unblock(self, ctx: Context, user: Union[discord.User, int]):
        if isinstance(user, discord.User):
            user = user.id
        async with ctx.cursor() as cur:
            await cur.execute(
                '''
                UPDATE users
                SET blocked = 0
                WHERE id == ?;
                ''',
                (user,)
            )
            await cur.execute(
                '''
                INSERT OR IGNORE INTO users (id, blocked)
                VALUES (?, 0);
                ''',
                (user,)
            )
        await ctx.db.commit()
        await ctx.rocket()

def setup(bot: Bot):
    bot.add_cog(Admin(
        bot, 
        min_guild_age=timedelta(days=1),
        min_members=5
    ))
