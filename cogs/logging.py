# -*- coding: utf-8 -*-

from discord.ext import commands
import discord

class Logging(commands.Cog):
    """The description for Logging goes here."""

    def __init__(self, bot):
        self.bot = bot

def setup(bot):
    bot.add_cog(Logging(bot))
