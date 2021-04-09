# -*- coding: utf-8 -*-

from discord.ext import commands, tasks
import discord
import logging
import traceback
from bot import Bot
from typing import List

def provide_context(embed, ctx):
    embed.set_author(
        name=f"{ctx.author.name} {ctx.author.id}",
        icon_url=str(ctx.author.avatar_url)
    )
    embed.timestamp = ctx.message.created_at
    msg = f"Message: {ctx.message.id}\n"
    msg += f"[Jump link]({ctx.message.jump_url})\n"
    if ctx.guild:
        msg += f"Channel: {ctx.channel} {ctx.channel.id}\n"
        msg += f"Guild: {ctx.guild} {ctx.guild.id}"
    else:
        msg += f"(Direct message)"

    embed.add_field(name="Context", value=msg)
    embed.add_field(name="Message contents", value=f"`{ctx.message.content[:1000]}`")

def populate_log(embed: discord.Embed, title = None, message = None, exc: BaseException = None):
    if exc is not None:
        embed.title = "Uncaught Exception"
        value = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
        for i in range(0, len(value), 1024):
            embed.add_field(
                inline=False,
                name=f"{exc.__class__.__name__}: {str(exc)}",
                value=value[i:i+1024]
            )
    else:
        embed.title = title
    embed.description = message

class Logging(commands.Cog):
    '''A custom webhook log.'''

    COLORS = {
        logging.DEBUG: discord.Color(0x7f7f7f),
        logging.INFO: discord.Color(0x69a9bc),
        logging.WARNING: discord.Color(0xe09138),
        logging.ERROR: discord.Color(0xf75d2a),
        logging.CRITICAL: discord.Color(0xc10508),
    }

    def __init__(self, bot: Bot):
        self.bot = bot
        self.bot.log = self.log
        self.bot.log_raw = self.log_raw
        self.buffer: List[discord.Embed] = []
        self.webhook = None
    
    @commands.Cog.listener()
    async def on_initialized(self):
        self.webhook = await self.bot.fetch_webhook(self.bot.webhook_id)
        if not self.flush_loop.is_running():
            self.flush_loop.start()

    def cog_unload(self):
        if self.flush_loop.is_running():
            self.flush_loop.stop()
        self.bot.log = None

    async def append_log(self, embed, level = logging.DEBUG):
        self.buffer.append(embed)
        if len(self.buffer) >= 10 or level >= logging.ERROR:
            await self.flush_buffer()

    async def log(self, ctx, *, level = logging.DEBUG, title = None, message = None, exc = None):
        embed = discord.Embed(
            color=self.COLORS[level],
        )
        provide_context(embed, ctx)
        populate_log(embed, title, message, exc)
        await self.append_log(embed, level)

    async def log_raw(self, *, level = logging.DEBUG, message = None, exc = None):
        embed = discord.Embed(
            color=self.COLORS[level],
        )
        populate_log(embed, message, exc)
        await self.append_log(embed, level)

    @tasks.loop(minutes=1)
    async def flush_loop(self):
        await self.flush_buffer()
    
    async def flush_buffer(self):
        if len(self.buffer) == 0:
            return
        for i in range(0, len(self.buffer), 10):
            embeds = self.buffer[i:i+9]
            await self.webhook.send( # type: ignore
                embeds=embeds, 
                username=f"{self.bot.user.name} logs",
                avatar_url=str(self.bot.user.avatar_url)
            )
        self.buffer.clear()
        
def setup(bot: Bot):
    bot.add_cog(Logging(bot))
