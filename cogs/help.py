# -*- coding: utf-8 -*-

from discord.ext import commands
import discord
import asyncio
from typing import *
from .utils.models import Bot, Context

class RocketHelpCommand(commands.MinimalHelpCommand):
    '''A help command with a silly gimmick.'''
    context: Context
    def __init__(self, color: discord.Color, *args, **kwargs):
        self.color = color
        super().__init__(*args, **kwargs)

    async def send_pages(self) -> None:
        '''Stupid gag'''
        ctx = self.context
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

class Help(commands.Cog):
    '''The help command'''
    def __init__(self, bot: Bot):
        self.bot = bot
        self._original_help_command = bot.help_command
        bot.help_command = RocketHelpCommand(bot.color)
        bot.help_command.cog = self

    def cog_unload(self):
        self.bot.help_command = self._original_help_command

def setup(bot: Bot):
    bot.add_cog(Help(bot))
