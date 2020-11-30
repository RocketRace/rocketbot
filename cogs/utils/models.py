# -*- coding: utf-8 -*-
'''Avoid import errors'''
from discord.ext import commands
import discord
from typing import *
from datetime import datetime
import aiosqlite
import aiohttp
class Context(commands.Context):
    async def react(self, emoji: discord.PartialEmoji): ...
    async def rocket(self): ...
    async def boom(self, message: str = ..., **kwargs): ...
    async def log(self, **kwargs): ...
    session: aiohttp.ClientSession
    db: aiosqlite.Connection
    def cursor(self) -> aiosqlite.Cursor: ...
    color: discord.Color
class Bot(commands.Bot):
    start_time: datetime
    exit_code: int
    color: discord.Color
    webhook_id: int
    cog_names: List[str]
    log: Optional[Callable]
    log_raw: Optional[Callable]
    db: Optional[aiosqlite.Connection]
    session: aiohttp.ClientSession
    async def connect_sessions(self, *, db: str): ...
    def cursor(self) -> aiosqlite.Connection: ...
    async def on_ready(self): ...
    async def get_context(self, message: discord.Message, *, cls: Type[commands.Context]=...): ...