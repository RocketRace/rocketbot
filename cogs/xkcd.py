# -*- coding: utf-8 -*-
from __future__ import annotations

import contextlib
import datetime
import json
import random
from typing import TYPE_CHECKING, Dict, Optional

import discord
from discord.ext import menus  # type: ignore
from discord.ext import commands, tasks

if TYPE_CHECKING:
    from bot import Bot, Ctx
else:
    Ctx = commands.Context

class XkcdMenu(menus.Menu):
    '''A menu that fetches its page source from XKCD.'''
    def __init__(self, number: int, **kwargs):
        self.current = number
        super().__init__(delete_message_after=True, **kwargs)

    async def send_initial_message(self, ctx: Ctx, channel: discord.TextChannel):
        embed = await self.ctx.cog.query_xkcd(self.current)
        return await channel.send(embed=embed)

    async def show_page(self, page_number: int):
        self.current = page_number
        embed = await self.ctx.cog.query_xkcd(page_number)
        await self.message.edit(embed=embed)
    
    async def show_checked_page(self, page_number: int):
        if 1 <= page_number <= self.ctx.cog.latest_number:
            await self.show_page(page_number)

    @menus.button("\N{BLACK LEFT-POINTING DOUBLE TRIANGLE WITH VERTICAL BAR}\ufe0f")
    async def first_comic(self, payload):
        if self.current != 1:
            await self.show_page(1)

    @menus.button("\N{BLACK LEFT-POINTING TRIANGLE}\ufe0f")
    async def previous_comic(self, payload):
        await self.show_checked_page(self.current - 1)

    @menus.button("\N{TWISTED RIGHTWARDS ARROWS}") # Discord rejects a variation selector here!
    async def random_comic(self, payload):
        await self.show_page(random.randint(1, self.ctx.cog.latest_number))

    @menus.button("\N{BLACK RIGHT-POINTING TRIANGLE}\ufe0f")
    async def next_comic(self, payload):
        await self.show_checked_page(self.current + 1)

    @menus.button("\N{BLACK RIGHT-POINTING DOUBLE TRIANGLE WITH VERTICAL BAR}\ufe0f")
    async def latest_comic(self, payload):
        if self.current != self.ctx.cog.latest_number:
            await self.show_checked_page(self.ctx.cog.latest_number)
    
    @menus.button("\N{BLACK SQUARE FOR STOP}\ufe0f")
    async def stop_menu(self, payload):
        self.stop()

class Xkcd(commands.Cog):
    '''Commands for interfacing with XKCD'''

    def __init__(self, bot: Bot):
        self.bot = bot
        self.latest_number = 1
        self.cached_users: Dict[int, bool] = {}
    
    @commands.Cog.listener()
    async def on_initialized(self): # Called once bot.session and bot.db are ready
        async with self.bot.cursor() as cur:
            await cur.execute(
                '''
                SELECT last_xkcd FROM stats;
                '''
            )
            # hohoho pistol operator goes boom
            self.latest_number ,= await cur.fetchone()
        if not self.update_xkcd.is_running():
            self.update_xkcd.start()

    def cog_unload(self):
        if self.update_xkcd.is_running():
            self.update_xkcd.stop()

    @tasks.loop(minutes=15)
    async def update_xkcd(self):
        '''Checks for a new XKCD and sends update DMs to all opted in'''
        async with self.bot.cursor() as cur:
            await cur.executemany(
                '''
                    INSERT OR IGNORE INTO users (id, xkcd_remind)
                    VALUES (?, ?);
                    ''',
                self.cached_users.items()
            )
            async with self.bot.session.get("https://xkcd.com/info.0.json") as resp:
                data = json.loads(await resp.text())
            if data["num"] > self.latest_number:
                await self.send_notifications(data["num"])
                self.latest_number = data["num"]
                await cur.execute(
                    '''
                    UPDATE stats SET last_xkcd = ?;
                    ''',
                    (data["num"],)
                )

    async def send_notifications(self, latest_number):
        '''Sends notifications to all who have been opted in'''
        async with self.bot.cursor() as cur:
            await cur.execute(
                '''
                SELECT id FROM users WHERE xkcd_remind = 1;
                '''
            )
            rows = await cur.fetchall()
        for (id,) in rows:
            with contextlib.suppress(discord.Forbidden):
                for num in range(self.latest_number + 1, latest_number + 1):
                    embed = await self.query_xkcd(num)
                    # Raw methods are used here due to a lack of member cache
                    # If `members` intent is enabled, `m = get_member(ID)` and `m.send(...)` may be used
                    channel = await self.bot.http.start_private_message(id) # type: ignore
                    chan_id = channel["id"]
                    await self.bot.http.send_message( # type: ignore
                        chan_id,
                        "\n".join([
                            f"XKCD #`{num}`",
                            "*You're being reminded because you opted in using `rocket opt in`.*",
                            "*To opt out from reminders, use `rocket opt out`.*"
                        ]),
                        embed=embed.to_dict()
                    )

    @commands.group(invoke_without_command=True)
    async def xkcd(self, ctx: Ctx, *, number: Optional[int]):
        '''Browse XKCD comics.
        
        Provide `number` to view a specific comic, or omit it to view a random one.
        '''
        if number is None:
            number = random.randint(1, self.latest_number)
        elif number > self.latest_number:
            return await ctx.boom(
                f"Number too big (`{number}`). Max: `{self.latest_number}` (run `rocket latest` to view the latest comic)"
            )
        await XkcdMenu(number=number).start(ctx)

    @xkcd.command()
    async def latest(self, ctx: Ctx):
        '''Returns the latest comic.'''
        await XkcdMenu(number=self.latest_number).start(ctx)

    async def query_xkcd(self, number = None) -> discord.Embed:
        '''Queries XKCD and returns an embed with the content.'''
        if number is None:
            path = "https://xkcd.com/info.0.json"
        else:
            path = f"https://xkcd.com/{number}/info.0.json"
        
        async with self.bot.session.get(path) as resp:
            if resp.status != 200:
                raise ValueError(number)
            
            data = json.loads(await resp.text())
        
        day, month, year = data["day"], data["month"], data["year"]
        stamp = datetime.datetime(int(year), int(month), int(day))
        
        embed = discord.Embed(
            color = self.bot.color,
            title=data["safe_title"],
            timestamp=stamp,
            url=f"https://xkcd.com/{number}",
        )
        embed.set_image(url=data["img"])
        embed.set_footer(text=data["alt"])
        return embed

    @commands.group(invoke_without_command=True)
    async def opt(self, ctx: Ctx):
        '''Opt in or out from XKCD reminders.'''
        if self.cached_users.get(ctx.author.id) is not None:
            result = self.cached_users[ctx.author.id]
        else:
            async with ctx.cursor() as cur:
                await cur.execute(
                    '''
                    SELECT xkcd_remind FROM users WHERE id = ?;
                    ''',
                    (ctx.author.id, )
                )
                fetch = await cur.fetchone()
                result = False if fetch is None else fetch[0]
        self.cached_users[ctx.author.id] = result
        if result:
            await ctx.send("You are currently opted in to XKCD reminders.")
        else:
            await ctx.send("You are currently opted out from XKCD reminders.")


    @opt.command(name="in")
    async def optin(self, ctx: Ctx):
        '''Opt in.'''
        self.cached_users[ctx.author.id] = True
        await ctx.send("You were opted in to XKCD reminders.")

    @opt.command(name="out")
    async def optout(self, ctx: Ctx):
        '''Opt out.'''
        self.cached_users[ctx.author.id] = False
        await ctx.send("You were opted out from XKCD reminders.")

def setup(bot: Bot):
    bot.add_cog(Xkcd(bot))
