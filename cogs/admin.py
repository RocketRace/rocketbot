# -*- coding: utf-8 -*-

from __future__ import annotations

import asyncio
import contextlib
import datetime
import io
import logging
import textwrap
from urllib import parse
from asyncio import subprocess
from datetime import timedelta
from typing import TYPE_CHECKING, Any, TypeVar, Union

import dbouncer
import discord
from discord.ext import menus  # type: ignore
from discord.ext import commands

if TYPE_CHECKING:
    from bot import Bot, Ctx
else:
    Ctx = commands.Context

_T = TypeVar("_T")
Sdict = dict[str, _T]

class EasyPaginator(menus.ListPageSource):
    def __init__(self, data):
        super().__init__(data, per_page=1)
    async def format_page(self, menu, page):
        return f"{page}\n`Page {menu.current_page + 1}/{len(self.entries)}`"

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

    async def run_shell(self, command: str, ctx: Ctx, *, typing: bool = False) -> menus.MenuPages:
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

    async def cog_check(self, ctx: Ctx):
        return await self.bot.is_owner(ctx.author)

    @commands.command()
    async def sh(self, ctx: Ctx, *, cmd: str):
        await self.run_shell(cmd, ctx, typing=True)
    
    @commands.command()
    async def sql(self, ctx: Ctx, query: str, *args):
        async with ctx.cursor() as cur:
            await cur.execute(
                query,
                args
            )
            result = [list(row) for row in await cur.fetchall()]
        lines = "\n".join(" | ".join(str(column) for column in row) for row in result)
        result = f"Success. Results: ```{lines}```"
        await ctx.send(result)
    
    @commands.command(name="eval")
    async def eval_python(self, ctx: Ctx, *, code: str):
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
    async def logout(self, ctx: Ctx):
        await ctx.rocket()
        await self.bot.close()
    
    @commands.group(invoke_without_command=True)
    async def load(self, ctx: Ctx, *cogs):
        if len(cogs) == 0:
            for cog in self.bot.cog_names:
                self.bot.reload_extension(cog)
        else:
            for cog in cogs:
                self.bot.reload_extension("cogs." + cog)
        self.bot.dispatch("initialized")
        await ctx.rocket()

    @load.command()
    async def git(self, ctx: Ctx):
        await self.run_shell("git pull", ctx, typing=True)
        for cog in self.bot.cog_names:
            self.bot.reload_extension(cog)
        self.bot.dispatch("initialized")

    async def update_presence(
        self,
        ctx: Ctx,
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
    async def playing(self, ctx: Ctx, *, msg):
        await self.update_presence(ctx, discord.ActivityType.playing, msg)
    
    @commands.command()
    async def watching(self, ctx: Ctx, *, msg):
        await self.update_presence(ctx, discord.ActivityType.watching, msg)

    @commands.group(invoke_without_command=True)
    async def listening(self, ctx): pass
    @listening.command(name="to")
    async def listening_to(self, ctx: Ctx, *, msg):
        await self.update_presence(ctx, discord.ActivityType.listening, msg)

    @commands.group(invoke_without_command=True)
    async def competing(self, ctx): pass
    @competing.command(name="in")
    async def competing_in(self, ctx: Ctx, *, msg):
        await self.update_presence(ctx, discord.ActivityType.competing, msg)

    @commands.command()
    @commands.guild_only()
    @commands.bot_has_permissions(change_nickname=True)
    async def nick(self, ctx: Ctx):
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
    async def block(self, ctx: Ctx, user: Union[discord.User, int]):
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
        await ctx.rocket()

    @commands.command()
    async def unblock(self, ctx: Ctx, user: Union[discord.User, int]):
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
        await ctx.rocket()

    @commands.command()
    async def yum(self, ctx: Ctx, tomorrow: bool = False):
        async with self.bot.session.get("https://kitchen.kanttiinit.fi/areas?idsOnly=1") as resp:
            areas = await resp.json()
        restaurant_ids = [str(id) for area in areas if area["id"] == 1 for id in area["restaurants"]]
        id_str = ",".join(restaurant_ids)
        async with self.bot.session.get(f"https://kitchen.kanttiinit.fi/restaurants?ids={id_str}&priceCategories=student,studentPremium") as resp:
            restaurants: list[Sdict[Any]] = await resp.json()
        day = datetime.date.today()
        if tomorrow:
            day = day + datetime.timedelta(days=1)
        async with self.bot.session.get(f"https://kitchen.kanttiinit.fi/menus?restaurants={id_str}&days={day}") as resp:
            menus: Sdict[Sdict[list[Sdict[Any]]]] = await resp.json()
        panel = discord.Embed(
            color=self.bot.color,
            title="Open restaurants",
            url=f"https://kanttiinit.fi/?day={day}"
        )
        for id in restaurant_ids:
            restaurant = [r for r in restaurants if r["id"] == int(id)][0]

            name = restaurant["name"]
            address = restaurant["address"]
            url = restaurant["url"]
            hours = restaurant["openingHours"][day.weekday()]
            price_category = restaurant["priceCategory"]
            if price_category == "student":
                price = "Student prices"
            else:
                price = "Student discounts"
            
            if hours is None:
                continue
            
            lines = [
                f"[{address}](https://maps.google.com?q={parse.quote(address)})",
                f"Open {hours} [(Link)]({url})"
            ]
            try:
                menu: list[Sdict] = menus[id][str(day)]
                if not menu:
                    continue
                lines.append("```")
                for meal in menu:
                    title = meal["title"]
                    properties = " ".join(meal["properties"])
                    if properties:
                        lines.append(f"{title} -- {properties}")
                    else:
                        lines.append(title)
                lines.append("```")

            except KeyError:
                continue
            
            panel.add_field(
                name=f"{name} -- [{price}]",
                value="\n".join(lines),
                inline=False
            )
        await ctx.send(embed=panel)

def setup(bot: Bot):
    bot.add_cog(Admin(
        bot, 
        min_guild_age=timedelta(days=1),
        min_members=5
    ))
