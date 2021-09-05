# -*- coding: utf-8 -*-

from __future__ import annotations

import asyncio
import contextlib
import json
import random as r
from datetime import datetime
from random import randint
from typing import TYPE_CHECKING, Dict, Optional

import discord
from discord.ext import commands

from . import utils

if TYPE_CHECKING:
    from bot import Bot, Ctx
else:
    Ctx = commands.Context

class Shell(commands.Cog):
    '''Assorted shell commands'''

    def __init__(self, bot: Bot):
        self.bot = bot
        with open("data/icons.json") as fp:
            self.distros: Dict[str, str] = json.load(fp)
        self.distro_names = [*self.distros.keys()]
        self.lower_distros = {d.lower(): d for d in self.distro_names}
        self.instruction_sets = (
            "6502","6809","680x0","8080","8051",
            "x86","x86_64","Alpha","ARC","ARM",
            "Thumb","Arm64","AVR","AVR32","Blackfin",
            "Crusoe","Elbrus","DLX","eSi-RISC",
            "Itanium","M32R","Micro32","MIPS","MMIX",
            "NS320xx","OpenRISC","PA-RISC","PDP-8",
            "PDP-11","POWER","RISC-V","RX","S+core",
            "SPARC","SuperH","System/360","Transputer",
            "VAX","Z80","SUBLEQ","Minsky Machine Notation",
            "Ideal Turing Machine","BitBitJump"
        )
        self.package_managers = (
            "dpkg","flatpak","guix","brew","ipkg",
            "netpkg","opkg","pacman","pisi","pkgsrc",
            "yum","dnf","up2date","zypper","urpmi",
            "apt-rpm","slackpkg","slapt-get","apt-get",
            "snap","swaret","fink","port","pkg","nuget"
            "wpkg",
        )
        self.shhh = (
            "sh","bash","ksh","zsh","csh","tcsh","ch",
            "eshell","fish","pwsh","rc","sash","scsh",
        )
        self.des = (
            "Luna","Fluent","Aqua",
            "KDE","GNOME","Xfce","LXDE","CDE","EDE","GEM","IRIX",
            "Ambient","Budgie","Deepin DE","Elokab",
            "Enlightenment","Étoilé","GNUstep","Innova","Liri",
            "Lumina","LXDE","LXQt","MATE","MaXX","Maynard","Mezzo",
            "Moksha","Pantheon","Project Looking Glass","Razor-qt",
            "ROX","Sugar","theShell","Trinity","Unity",
            "vera","Weston","Zorin","Audio-only (no DE)"
        )
        self.wms = (
            "2bwm","9wm","aewm","awesome","Berry","Blackbox","bspwm",
            "Compiz","cwm","dwm","Enlightenment","evilwm","EXWM","Fluxbox",
            "FLWM","FVWM","i3","IceWM","Ion","JWM","KWin (KDE)","Matchbox",
            "Metacity","Mutter","mwm","Openbox","PekWM","PlayWM","Ratpoison",
            "Sawfish","sithWM","spectrwm","steamcompmgr","StumpWM","twm",
            "WMFS","Window Maker","Wingo","wmii","Xfwm","xmonad","uwm",
            "Quartz Compositor","No WM Necessary"
        )

    @commands.command()
    async def neofetch(self, ctx: Ctx, *, distro: Optional[str] = None):
        '''Shows the user's system information.'''
        if isinstance(ctx.channel, discord.TextChannel):
            title = f"{ctx.author.display_name} @ {ctx.channel.name}"
        else:
            title = f"{ctx.author.display_name} @ Direct Message"
        if distro is None:
            distro_name = r.choice(self.distro_names)
        elif distro not in self.lower_distros:
            return await ctx.boom(
                f"Distro `{distro}` not found."
            )
        else:
            distro_name = self.lower_distros[distro]
        pacmans = set(r.choices(self.package_managers, k=r.randint(1, 3)))
        if ctx.guild:
            host = "Host: " + ctx.guild.name
        else:
            host = "Host: Direct Message"
        fields = [
            title,
            len(title) * "-",
            f"OS: {distro_name} v{r.randint(0,4)}.{r.randint(0,16)}.{r.randint(0,256)} {r.choice(self.instruction_sets)}",
            host,
            f"Kernel: {r.randint(0,32)}.{r.randint(0,8)}.{r.randint(0,3)}",
            "Uptime: " + utils.humanize_duration(datetime.utcnow() - self.bot.start_time),
            f"Packages: {r.randint(0, 1024)} ({', '.join(pacmans)})",
            f"Shell: {r.choice(self.shhh)} {r.randint(0,8)}.{r.randint(0,4)}.{r.randint(0,24)}",
            f"Resolution: {2**randint(0,12) * 3**randint(0,2)}x{2**randint(0,10) * 3**randint(0,3)}",
            "DE: " + r.choice(self.des),
            "WM: " + r.choice(self.wms),
            "Terminal: Discord"
        ]
        # This uses an embed because it allows the code blocks to be scaled better, and provides a better 
        # color contrast inside the codeblocks. Unfortunately, it makes the mobile experience marginally
        # worse.
        embed = discord.Embed(color=ctx.color, description= "\n".join([
            "```",
            self.distros[distro_name].replace("`", "\u200b`"),
            "```",
            "```diff",
            *fields,
            "```",
        ]))
        await ctx.send(embed=embed)

    @commands.command()
    async def sudo(self, ctx: Ctx, *, command):
        '''Execute a command with super user privileges'''
        if ctx.author.id in ():
            return await ctx.boom(f"{ctx.author} is not in the sudoers file. This incident has been reported.")
        n = 0
        messages = [await ctx.send("Password: \N{CLOSED LOCK WITH KEY}")]
        while True:
            try:
                message = await self.bot.wait_for(
                    "message", 
                    timeout=5,
                    check=lambda m: m.channel == ctx.channel and m.author == ctx.author
                )
                messages.append(message)
                if message.content == self.bot.secret_password:
                    # I'll do it, fr
                    import os
                    await ctx.send(f"Success. Return code: {os.system(command)}")
                else:
                    messages.append(await ctx.send("Sorry, try again.\nPassword: \N{CLOSED LOCK WITH KEY}"))
                    n += 1
            except asyncio.TimeoutError:
                if n == 1:
                    await ctx.boom(f"Sudo: {n} incorrect password attempt")
                else:
                    await ctx.boom(f"Sudo: {n} incorrect password attempts")
                for m in messages:
                    with contextlib.suppress(discord.Forbidden):
                        await m.delete()
                break

def setup(bot: Bot):
    bot.add_cog(Shell(bot))
