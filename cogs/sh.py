# -*- coding: utf-8 -*-

from datetime import datetime
from random import randint
from discord.ext import commands
import discord
from .utils.models import Context, Bot
import random as r
import json
from . import utils
from typing import *

class Sh(commands.Cog):
    '''Assorted shell commands'''

    def __init__(self, bot: Bot):
        self.bot = bot
        with open("data/icons.json") as fp:
            self.icons: Dict[str, str] = json.load(fp)
            self.distros = [*self.icons.keys()]
        self.instruction_sets = (
            "6502","6809","680x0","8080","8051",
            "x86","x86_64","Alpha","ARC","ARM",
            "Thumb","Arm64","AVR","AVR32","Blackfin",
            "Crusoe","Elbrus","DLX","eSi-RISC",
            "Itanium","M32R","Micro32","MIPS","MMIX",
            "NS320xx","OpenRISC","PA-RISC","PDP-8",
            "PDP-11","POWER","RISC-V","RX","S+core",
            "SPARC","SuperH","System/360","Transputer",
            "VAX","Z80"
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
            "vera","Weston","Zorin"
        )
        self.wms = (
            "2bwm","9wm","aewm","awesome","Berry","Blackbox","bspwm",
            "Compiz","cwm","dwm","Enlightenment","evilwm","EXWM","Fluxbox",
            "FLWM","FVWM","i3","IceWM","Ion","JWM","KWin (KDE)","Matchbox",
            "Metacity","Mutter","mwm","Openbox","PekWM","PlayWM","Ratpoison",
            "Sawfish","sithWM","spectrwm","steamcompmgr","StumpWM","twm",
            "WMFS","Window Maker","Wingo","wmii","Xfwm","xmonad","uwm",
            "Quartz Compositor"
        )

    @commands.group(invoke_without_command=True)
    async def neofetch(self, ctx: Context):
        '''Shows the user's system information.'''
    
    @neofetch.command()
    async def mobile(self, ctx: Context):
        '''Returns mobile-friendly output for `neofetch`.'''
        icon, fields = self.get_neofetch(ctx)
        output = "\n".join([
            "```",
            icon,
            *fields,
            "```"
        ])
        await ctx.send(output)

    def get_neofetch(self, ctx: Context) -> Tuple[str, List[str]]:
        '''OBTAIN THE NEOFETCH'''
        if ctx.guild:
            title = f"{ctx.author.display_name} @ {ctx.channel.name}"
        else:
            title = f"{ctx.author.display_name}@Direct Message"
        distro = r.choice(self.distros)
        pacmans = set(r.choices(self.package_managers, k=r.randint(1, 3)))
        if ctx.guild:
            host = "Host: " + ctx.guild.name
        else:
            host = "Host: Direct Message"
        fields = [
            title,
            len(title) * "-",
            f"OS: {distro} v{r.randint(0,4)}.{r.randint(0,16)}.{r.randint(0,256)} {r.choice(self.instruction_sets)}",
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
        return (self.icons[distro], fields)

    @commands.command()
    async def cat(self, ctx: Context, fp: str):
        '''Reads the content of arbitrary files.'''
    
    @commands.command()
    async def ls(self, ctx: Context, fp: str):
        '''Lists accessible files.'''
    
def setup(bot: Bot):
    bot.add_cog(Sh(bot))
