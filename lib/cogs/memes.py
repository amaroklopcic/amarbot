import random

import discord
from discord.ext import commands

from lib.cogs.cog import CommonCog
from lib.ytdl import YTDLSource


class MemeCog(CommonCog):
    """Commands suggested by my friends/community just for fun."""

    # -vvv- commands suggested by me (very, very annoying) -vvv-
    @commands.command()
    async def roulette(self, ctx: commands.Context):
        """Plays a gunshot sounds and kicks a random user from the voice channel."""
        await self.acknowledge(ctx)

        # validate user is in voice channel
        voice_channel = None
        if ctx.author.voice:
            voice_channel = ctx.author.voice.channel
        else:
            await self.react_error(ctx)
            return

        if len(voice_channel.members) < 1:
            await self.react_error(ctx)
            return

        gun_sound = YTDLSource.from_file("sounds/roulette.wav")

        # connect to voice channel and play sound
        await self.join_authors_vc(ctx)
        ctx.voice_client.play(gun_sound)

        # sleep so user can hear gunshot before they go
        await self.sleep(gun_sound.data["duration"])

        chosen_one = random.choice(voice_channel.members)
        await chosen_one.edit(voice_channel=None)

        await self.disconnect_vc(ctx)
        await self.finish(ctx)

    @commands.command()
    async def driveby(self, ctx: commands.Context):
        """Plays machine gun sound while kicking multiple people from the voice channel."""
        await self.acknowledge(ctx)

        # validate user is in voice channel
        voice_channel = None
        if ctx.author.voice:
            voice_channel = ctx.author.voice.channel
        else:
            await self.react_error(ctx)
            return

        if len(voice_channel.members) < 1:
            await self.react_error(ctx)
            return

        # join voice_channel and play machine gun sound
        machine_gun_sound = YTDLSource.from_file("sounds/machine_gun.wav")

        await self.join_authors_vc(ctx)
        ctx.voice_client.play(machine_gun_sound)

        # initial wait so everyone can here the "CHK CHK"
        await self.sleep(1)

        targets = [member for member in voice_channel.members if not member.bot]

        # keep going until everyone has been kicked
        while targets:
            await self.sleep(random.uniform(0.5, 1.5))
            user = random.choice(targets)
            await user.edit(voice_channel=None)
            targets.remove(user)
            if len(targets) == 0:
                break

        await self.disconnect_vc(ctx)
        await self.finish(ctx)

    @commands.command()
    async def grenade(self, ctx: commands.Context):
        """Plays grenade sound while everyone is scattered across various channels."""
        await self.acknowledge(ctx)

        # validate user is in voice channel
        voice_channel = None
        if ctx.author.voice:
            voice_channel = ctx.author.voice.channel
        else:
            await self.react_error(ctx)
            return

        if len(voice_channel.members) < 1:
            await self.react_error(ctx)
            return

        # join voice_channel and play grenade sound
        grenade_sound = YTDLSource.from_file("sounds/grenade_oh_fudge.wav")

        await self.join_authors_vc(ctx)
        ctx.voice_client.play(grenade_sound)

        all_voice_channels = voice_channel.guild.voice_channels

        # sleep so users can hear grenade and "OH FUDGE"
        await self.sleep(3)

        # avoid kicking them into a channel they dont have access to
        for member in voice_channel.members:
            if member.bot:
                continue

            available_channels = []
            for channel in all_voice_channels:
                if channel.permissions_for(member).connect:
                    available_channels.append(channel)

            await member.edit(voice_channel=random.choice(available_channels))

        await self.disconnect_vc(ctx)
        await self.finish(ctx)
