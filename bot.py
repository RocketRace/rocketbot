#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''A bot for my personal use.'''
from discord.ext import commands
import discord
import aiohttp
import config

class Context(commands.Context):
    '''A custom command context.'''
    async def react(self, emoji):
        '''Adds a reaction to this message.'''
        try:
            await self.message.add_reaction(emoji)
        except discord.HTTPException:
            # This just means that users get no feedback
            pass

    async def rocket(self):
        '''Reacts with a rocket emoji.'''
        await self.react("\N{ROCKET}")

    async def boom(self, message = None):
        '''Reacts with a boom emoji, and sends an optional error message.'''
        await self.react("\N{COLLISION SYMBOL}")
        if message is not None:
            await self.send(message)
    
    async def error(self, original):
        await self.rocket(boom=True)

    @property
    def cs(self):
        return self.bot.session
    
    @property
    def color(self):
        return self.bot.color

class Bot(commands.Bot):
    '''Custom bot class with convenience methods and attributes.'''
    def __init__(self, prefix, **kwargs):
        self.session = aiohttp.ClientSession()
        self.color = kwargs.get("color") or discord.Color.default()
        super().__init__(command_prefix=commands.when_mentioned_or(prefix), **kwargs)
        for cog in config.cogs:
            try:
                self.load_extension(cog)
            except Exception as exc:
                print(f"Could not load extension {cog} due to {exc.__class__.__name__}: {exc}")

    async def on_ready(self):
        print(f"Logged in as {self.user} (ID: {self.user.id})")
        print("Invite:", discord.utils.oauth_url(self.user.id))
    
    async def get_context(self, message, *, cls=Context):
        return await super().get_context(message, cls=cls)

bot = Bot("rocket ", color=discord.Color(0xe0e0f0))

bot.run(config.token)
