# -*- coding: utf-8 -*-

from __future__ import annotations

import asyncio
import contextlib
import hashlib
import json
from datetime import datetime, timedelta
from random import choice, choices, gauss, randint, random, shuffle
from typing import TYPE_CHECKING, Dict, Optional, TypeVar

import discord
from discord.ext import commands

from . import utils

if TYPE_CHECKING:
    from bot import Bot, Ctx
else:
    Ctx = commands.Context

def to_bottom(string: str, length: int, blanks: bool = False) -> str:
    '''The official specification gives too much verbosity'''
    units = [
        ",", # ,
        "\U0001f97a", # plead
        "\U0001fac2", # hug
        "\u2728", # sparkle
        "\U0001f449\U0001f448", # point
        "\U0001f496", # sparkling heart
        ",", # , again
        "\U0001f97a", # plead again
        "",
        "",
    ]
    # This picks [length] bytes from the hash and only picks the 
    # bottom 3 bits from each byte - plenty of fun collisions
    return "{:.>{length}}".format("".join(
        units[((value & 0b1110) >> 1) + 2 * blanks] 
        for value in hashlib.sha1(
            string.encode("utf-8"),
            usedforsecurity=False
        ).digest()[:length]
    )[:length] or "\U0001f97a", length=length).replace(",", ",,")

def keysmash(length: int, energy: float) -> str:
    '''No I will not elaborate'''
    keymap_qwerty_us = [
        "1234567890-",
        "qwertyuiop[",
        "asdfghjkl;'",
        "zxcvbnm,.//", 
        "           ", 
        # the last slash is not accurate but it's very rarely hit so it's fine
    ]
    # the keysmash, on a physical keyboard, operates on the following behaviors:
    # - wrist placement stays roughly constant
    # - the more energy exerted, the greater distance the fingers will travel
    # from their rest position
    #
    # there are four primary movements:
    #
    # - the "hammer", using all fingers as a single unit around their hover points.
    # energy makes little of a difference here (the thumb may sometimes be omitted)
    #
    # low-energy example: asfljsd fljsd lkj;sd alkj
    # high-energy example: as fjksdfa ljsdf ajlds fl;
    #
    # - the "swing", alternating between the index finger, thumb, and the other fingers 
    # operating together as one unit (the thumb may sometimes be omitted)
    #
    # low-energy example: jfioewjfo; js;f djiso;f jwio;f jewiofj owi;aejf
    # high-energy example: sfdjskf fp jioewj feqjf xoquj p0 ujt290
    #
    # - the "wave", a motion across the fingers propagating outwards
    # low-energy example: fjdsakl;fj sdkl;f jsdakl
    # high-energy example: fjdsal; fhiewo[ jfiewoj iwo jfwio
    #
    # - the "flop", flattening the hands around the point of contact
    # by the joints
    # low-energy example: asfjdkslafj,xcnad,vkjsn
    # high-energy example: adsasdjkf.kszvkfjh.waeg,f-dk.;_nj
    #
    # - the "drill peck", where (usually) the index finger scatters around the keyboard
    # low-energy example: dhssdkfjdjwif
    # high-energy example: ajsgbei3eusjflrfolwsjdxna
    #
    # each of these methods may be performed with one or both hands

    layouts = [keymap_qwerty_us]
    # I only implemented these because I'm boring
    methods = [hammer, drill_peck]

    method = choice(methods)
    layout = choice(layouts)
    string = "".join(layout[y][x] for x, y in method(energy))
    return string[:length]

_T = TypeVar("_T", bound=float)
def minmax(n: _T, minimum: _T, maximum: _T) -> _T:
    return min(maximum, max(minimum, n))

def drill_peck(energy: float) -> list[tuple[int, int]]:
    out: list[tuple[int, int]] = []
    right_hand = random() < 0.8
    l_x, l_y = 1.5, 2
    r_x, r_y = 6.5, 2
    for _ in range(20):
        dx = (random() * 3 - 2) * (energy)
        dy = (random() - 0.75) * energy
        x, y = minmax(round(l_x + dx), 0, 9), minmax(round(l_y + dy), 0, 2)
        out.append((x, y))
        if right_hand:
            dx = (random() * 3 - 2) * (energy)
            dy = (random() - 0.75) * energy
            x, y = minmax(round(r_x + dx), 0, 9), minmax(round(r_y + dy), 0, 2)
            out.append((x, y))
    return out

def hammer(_energy: float) -> list[tuple[int, int]]:
    keys_pressed: list[tuple[float, tuple[int, int]]] = []
    left_hand = True
    right_hand = random() < 0.8
    thumbless = random() < 0.5
    if left_hand:
        # x, y
        positions = [
            (3, 4), (3, 2), (2, 2), (1, 2), (0, 2)
        ]
        time = 0
        for _ in range(5):
            fingers = [0, 1, 2, 3, 4]
            shuffle(fingers)
            for finger in fingers:
                keys_pressed.append((time, positions[finger]))
                time += random() * 0.025
            time += gauss(0.5, 0.125)   
    if right_hand:
        # x, y
        time = gauss(0.5, 0.25)
        positions = [
            (6, 4), (6, 2), (7, 2), (8, 2), (9, 2)
        ]
        for _ in range(5):
            fingers = [0, 1, 2, 3, 4]
            shuffle(fingers)
            for finger in fingers:
                keys_pressed.append((time, positions[finger]))
                time += random() * 0.025
            time += gauss(0.5, 0.125)
    keys_pressed.sort()
    # remove consecutive spaces
    last = (-1, -1)
    for i, (_, pos) in enumerate(keys_pressed):
        if last[1] == 4 and pos[1] == 4:
            del keys_pressed[i]
        last = pos

    if thumbless:
        return [pos for _, pos in keys_pressed if pos[1] != 4]
    else:
        return [pos for _, pos in keys_pressed]

class Shell(commands.Cog):
    '''Assorted shell commands'''

    def __init__(self, bot: Bot):
        self.bot = bot
        
        # Neofetch data
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
            distro_name = choice(self.distro_names)
        elif distro not in self.lower_distros:
            return await ctx.boom(
                f"Distro `{distro}` not found."
            )
        else:
            distro_name = self.lower_distros[distro]
        pacmans = set(choices(self.package_managers, k=randint(1, 3)))
        if ctx.guild:
            host = "Host: " + ctx.guild.name
        else:
            host = "Host: Direct Message"
        fields = [
            title,
            len(title) * "-",
            f"OS: {distro_name} v{randint(0,4)}.{randint(0,16)}.{randint(0,256)} {choice(self.instruction_sets)}",
            host,
            f"Kernel: {randint(0,32)}.{randint(0,8)}.{randint(0,3)}",
            "Uptime: " + utils.humanize_duration(datetime.utcnow() - self.bot.start_time),
            f"Packages: {randint(0, 1024)} ({', '.join(pacmans)})",
            f"Shell: {choice(self.shhh)} {randint(0,8)}.{randint(0,4)}.{randint(0,24)}",
            f"Resolution: {2**randint(0,12) * 3**randint(0,2)}x{2**randint(0,10) * 3**randint(0,3)}",
            "DE: " + choice(self.des),
            "WM: " + choice(self.wms),
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

    @commands.command()
    async def bottom(self, ctx: Ctx):
        '''Displays process information'''
        uptime = to_bottom(str(self.bot.start_time -  datetime.utcnow()), 5)
        load = to_bottom(str(random()), 6)
        tasks = to_bottom(str(random()), 20)
        cpus = to_bottom(str(random()), 19)
        mems = to_bottom(str(random()), 19)
        swap = to_bottom(str(random()), 19)
        users = ["root", "olivia", "bee"]
        commands = ["neofetch", "rm", "cargo", "man", "python2", "python2.6", "tmux", "sudo"]
        out = [
            "```",
            f"bottom - up {uptime}, load average: {load}",
            f"Tasks: {tasks}",
            f"%Cpu(s): {cpus}",
            f"MiB Mem: {mems}",
            f"MiB Swap: {swap}",
            "",
            "  PID      USER    %CPU    %MEM     TIME    COMMAND"
        ]
        for _ in range(10):
            pid = str(randint(0, 20000))
            user = choice(users)
            cpu = str(random() * 100)
            mem = str(random() * 100)
            time = str(timedelta(seconds=randint(0, 100000)))
            command = choice(commands)
            out.append(
                f"{to_bottom(pid, 3, True)}."
                f"{to_bottom(user, 3, True)}."
                f"{to_bottom(cpu, 3, True)}."
                f"{to_bottom(mem, 3, True)}."
                f"{to_bottom(time, 3, True)}."
                f"{to_bottom(command, 4, True)}.".replace(".", "  ")
            )

        out.append("```")
        await ctx.send(embed=discord.Embed(description="\n".join(out)))
        

def setup(bot: Bot):
    bot.add_cog(Shell(bot))
