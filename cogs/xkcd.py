# -*- coding: utf-8 -*-

from discord.ext import commands, tasks
import discord
import aiohttp
from typing import *
import json
import datetime
import asyncio
import random

class Xkcd(commands.Cog):
    '''Commands for interfacing with XKCD.'''

    def __init__(self, bot):
        self.bot = bot
        self.latest_number = 1
        self.update_latest_number.start()

    def cog_unload(self):
        self.update_latest_number.cancel()
    
    @tasks.loop(hours=6)
    async def update_latest_number(self):
        async with self.bot.session.get("https://xkcd.com/info.0.json") as resp:
            data = json.loads(await resp.text())
            self.latest_number = data["num"]

    @commands.group(invoke_without_command=True)
    async def xkcd(self, ctx, *, number: Optional[int]):
        if number is None:
            number = random.randint(1, self.latest_number)
        elif number > self.latest_number:
            return await ctx.boom(f"Number too big. Max: `{self.latest_number}`")
        await self.query_xkcd(ctx, number)
    
    @xkcd.command()
    async def latest(self, ctx):
        await self.query_xkcd(ctx)
    
    async def query_xkcd(self, ctx, number = None):
        '''Queries XKCD and sends an embed with results.'''
        if number is None:
            path = "https://xkcd.com/info.0.json"
        else:
            path = f"https://xkcd.com/{number}/info.0.json"
        
        async with ctx.cs.get(path) as resp:
            if resp.status != 200:
                raise ValueError(number)
            
            data = json.loads(await resp.text())
        
        day, month, year = data["day"], data["month"], data["year"]
        stamp = datetime.datetime(int(year), int(month), int(day))
        
        embed = discord.Embed(
            color = ctx.color,
            title=data["safe_title"],
            timestamp=stamp
        )
        embed.set_image(url=data["img"])
        embed.set_footer(text=data["alt"])

        await ctx.send(embed=embed)

    @xkcd.error
    async def xkcd_error(self, ctx, error):
        if isinstance(error, ValueError):
            await ctx.boom("")
        raise error

def setup(bot):
    bot.add_cog(Xkcd(bot))
