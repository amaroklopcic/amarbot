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
        """Randomly selects a user and disconnects them from the channel, while playing a gunshot sound."""
        self.acknowledge(ctx)

        vc = ctx.message.author.voice.channel

        if len(vc.members) > 0:
            chosen_one = random.choice(vc.members)
            gun_sound = YTDLSource.from_file("sounds/roulette.wav")

            # connect to voice channel and play sound
            voice_client = await self.join_vc(ctx, channel=vc)
            voice_client.play(gun_sound)

            # sleep so user can hear gunshot before they go
            await self.sleep(gun_sound.data["duration"])

            await chosen_one.edit(voice_channel=None)

            await self.disconnect_vc(ctx)
            await self.finish(ctx)
