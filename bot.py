#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''A bot for my personal use.'''
from __future__ import annotations

import contextlib
from datetime import datetime

import aiohttp
import aiosqlite
from aiosqlite.core import Connection
import discord
from discord.ext import commands

import config

class Ctx(commands.Context):
    '''A custom command context.'''
    bot: Bot

    async def react(self, emoji):
        '''Adds a reaction to this message.'''
        with contextlib.suppress(discord.HTTPException):
            await self.message.add_reaction(emoji)

    async def rocket(self) -> None:
        '''Reacts with a rocket emoji.'''
        await self.react("\N{ROCKET}")

    async def boom(self, message = None, **kwargs) -> None:
        '''Reacts with a boom emoji, and sends an optional error message.'''
        await self.react("\N{COLLISION SYMBOL}")
        await self.send(message, **kwargs)
    
    async def log(self, **kwargs):
        await self.bot.log(self, **kwargs)

    @property
    def session(self):
        return self.bot.session
    
    @property
    def conn(self):
        return self.bot.db

    def cursor(self):
        return self.bot.cursor()

    @property
    def color(self):
        return self.bot.color

class Bot(commands.Bot):
    '''Custom bot class with convenience methods and attributes.'''
    def __init__(self, prefixes, *, color=discord.Color.default(), db, webhook_id, secret_password, **kwargs):
        self.exit_code = 0
        self.start_time = None
        self.color = color
        self.webhook_id = webhook_id
        self.secret_password = secret_password
        self.cog_names = config.cogs
        self.log = None
        self.log_raw = None
        self.db = None
        self.session = None

        super().__init__(command_prefix=commands.when_mentioned_or(*prefixes), **kwargs)
        for cog in config.cogs:
            try:
                self.load_extension(cog)
            except Exception as exc:
                print(f"Could not load extension {cog} due to {exc.__class__.__name__}: {exc}")

        # Connection acquisition must be asynchronous
        self.loop.create_task(self.connect_sessions(db=db))
    
    async def close(self):
        await self.session.close()
        await self.db.close()

    async def connect_sessions(self, *, db: str):
        self.db = await aiosqlite.connect(db)
        self.session = aiohttp.ClientSession()
        self.dispatch("initialized")
        print("Fully initialized.")

    def cursor(self):
        '''Obtains a cursor once awaited.'''
        return self.db.cursor()

    async def on_ready(self):
        self.start_time = datetime.utcnow()
        print(f"Logged in as {self.user} (ID: {self.user.id})")
        print("Invite:", discord.utils.oauth_url(str(self.user.id)))
    
    # Hook for custom context
    async def get_context(self, message: discord.Message, *, cls=commands.Context):
        return await super().get_context(message, cls=Ctx)

bot = Bot(
    ["rocket ", "Rocket "], # auto-capitalization aware
    color=discord.Color(0xe0e0f0),
    db=config.db,
    webhook_id=config.webhook_id,
    secret_password = config.secret_password,
    allowed_mentions=discord.AllowedMentions(everyone=False),
    intents=discord.Intents(
        guilds=True,
        messages=True,
        reactions=True,
    )
)

bot.run(config.token)
