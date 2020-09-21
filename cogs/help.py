# -*- coding: utf-8 -*-

from discord.ext import commands
import discord

class LispHelpCommand(commands.HelpCommand):
    '''This is a help command that uses embeds, adapted from 
    https://gist.github.com/Rapptz/31a346ed1eb545ddeb0d451d81a60b3b.
    '''

    COLOR = discord.Color(0xf0f0f0)

    def get_ending_note(self):
        return f"Use {self.clean_prefix}{self.invoked_with} command {self.clean_suffix} for more help on a command."

    def get_command_signature(self, command):
        return f"{command.qualified_name} {command.signature}"

    async def send_bot_help(self, mapping):
        embed = discord.Embed(color=self.COLOR, title="Command Reference")
        description = self.context.bot.description
        if description:
            embed.description = description
        
        for cog, commands in mapping.items():
            name = "Built-ins" if cog is None else cog.qualified_name
            filtered = await self.filter_commands(commands, sort=True)
            if filtered:
                value = '\u2002'.join(c.name for c in commands)
                if cog and cog.description:
                    value = f"{cog.description}\n{value}"

                embed.add_field(name=name, value=value)

        embed.set_footer(text=self.get_ending_note())
        await self.get_destination().send(embed=embed)

    async def send_cog_help(self, cog):
        embed = discord.Embed(title=f"{cog.qualified_name} Commands", colour=self.COLOUR)
        if cog.description:
            embed.description = cog.description

        filtered = await self.filter_commands(cog.get_commands(), sort=True)
        for command in filtered:
            embed.add_field(name=self.get_command_signature(command), value=command.short_doc or "...", inline=False)

        embed.set_footer(text=self.get_ending_note())
        await self.get_destination().send(embed=embed)
    
    async def send_group_help(self, group):
        embed = discord.Embed(title=group.qualified_name, colour=self.COLOUR)
        if group.help:
            embed.description = group.help

        if isinstance(group, commands.Group):
            filtered = await self.filter_commands(group.commands, sort=True)
            for command in filtered:
                embed.add_field(name=self.get_command_signature(command), value=command.short_doc or "...", inline=False)

        embed.set_footer(text=self.get_ending_note())
        await self.get_destination().send(embed=embed)

    send_command_help = send_group_help

class Help(commands.Cog):
    '''Implementation of custom help commands.'''
    def __init__(self, bot):
        self._original_help_command = bot.help_command
        bot.help_command = LispHelpCommand()
        bot.help_command.cog = self

    def cog_unload(self):
        self.bot.help_command = self._original_help_command

def setup(bot):
    bot.add_cog(Help(bot))
