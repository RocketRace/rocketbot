# -*- coding: utf-8 -*-
from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

import discord
from discord.ext import commands

if TYPE_CHECKING:
    from bot import Bot, Ctx


class RocketHelpCommand(commands.MinimalHelpCommand):
    '''A help command with a silly gimmick.'''
    ctx: Ctx
    def __init__(self, color: discord.Color, *args, **kwargs):
        self.color = color
        self.dm_flag = False
        super().__init__(*args, **kwargs)

    async def send_bot_help(self, *args):
        self.dm_flag = True
        await super().send_bot_help(*args)
        self.dm_flag = False

    async def send_pages(self) -> None:
        '''Stupid gag'''
        ctx = self.ctx
        # Triggers when someone runs the plain help command in a guild
        # Otherwise, just sends normal help
        if self.dm_flag and ctx.guild is not None:
            try:
                await ctx.author.send("help")
            except discord.HTTPException:
                message = await ctx.boom("I can't send help to you. Are you blocking DMs, or — me?")
            else:
                await ctx.rocket()
                message = await ctx.send("Help has been sent to your DMs!")
                await asyncio.sleep(1)
                await ctx.author.trigger_typing()
                await asyncio.sleep(3)
                await ctx.author.send("no seriously")
                await asyncio.sleep(1)
                await ctx.author.trigger_typing()
                await asyncio.sleep(2)
                await ctx.author.send("help me please")
                if len(self.paginator.pages) == 1:
                    # Ideally this is always the case
                    await message.edit(content=self.paginator.pages[0])
                else:
                    await message.delete()
                    destination = self.get_destination()
                    for page in self.paginator.pages:
                        await destination.send(page)
        else: #awww
            for page in self.paginator.pages:
                await self.get_destination().send(page)

class Meta(commands.Cog):
    '''The meta commands'''
    def __init__(self, bot: Bot):
        self.bot = bot
        self._original_help_command = bot.help_command
        bot.help_command = RocketHelpCommand(bot.color)
        bot.help_command.cog = self

    def cog_unload(self):
        self.bot.help_command = self._original_help_command
    
    @commands.command()
    async def hello(self, ctx: Ctx):
        msg = "\n".join([
            "Hi! I'm the robotic sibling of RocketRace#0798.",
            "I'm on GitHub: <https://github.com/RocketRace/rocketbot>",
        ])
        await ctx.send(msg)

def setup(bot: Bot):
    bot.add_cog(Meta(bot))
