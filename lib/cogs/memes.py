import asyncio
import random

from discord import Interaction, app_commands
from discord.ext import commands

from lib.common import join_users_vc
from lib.logging import get_logger
from lib.permissions import GuildPermissions
from lib.ytdl import YTDLSource


class MemeCog(commands.GroupCog, group_name="memes"):
    """Commands suggested by my friends/community just for fun."""

    def __init__(self, bot: commands.Bot) -> None:
        super().__init__()
        self.bot = bot
        self.logger = get_logger(__name__)
        self.logger.debug("Initializing MemeCog...")

    def _on_song_finish(self, error):
        if error:
            self.logger.error(f"Player error:\n{error}")

    # -vvv- commands suggested by me (very, very annoying) -vvv-
    @app_commands.command()
    @app_commands.check(GuildPermissions.can_kick)
    async def roulette(self, interaction: Interaction):
        """Plays a gunshot sounds and kicks a random user from the voice channel."""

        voice_client = await join_users_vc(self.bot, interaction)

        if not voice_client:
            await interaction.response.send_message("Something went wrong :(")
            return

        await interaction.response.send_message("Someone's fate has been sealed!")

        gun_sound = YTDLSource.from_file("sounds/roulette.wav")
        voice_client.play(gun_sound)

        # sleep so user can hear gunshot before they go
        await asyncio.sleep(gun_sound.data["duration"])

        targets = [member for member in voice_client.channel.members if not member.bot]
        chosen_one = random.choice(targets)
        await chosen_one.edit(voice_channel=None)

        await voice_client.disconnect()

    @app_commands.command()
    @app_commands.check(GuildPermissions.can_kick)
    async def driveby(self, interaction: Interaction):
        """Plays machine gun sound while kicking multiple people from the voice channel."""

        voice_client = await join_users_vc(self.bot, interaction)

        if not voice_client:
            await interaction.response.send_message("Something went wrong :(")
            return

        await interaction.response.send_message(
            "**Yo this black car just pulled up...**"
        )

        gun_sound = YTDLSource.from_file("sounds/machine_gun.wav")
        voice_client.play(gun_sound)

        # initial wait so everyone can here the "CHK CHK"
        await asyncio.sleep(1)

        targets = [member for member in voice_client.channel.members if not member.bot]

        # keep going until everyone has been kicked
        # TODO: refactor this. while loop will block until the entire 5 seconds is done
        while targets:
            await asyncio.sleep(random.uniform(0.5, 1.5))
            user = random.choice(targets)
            await user.edit(voice_channel=None)
            targets.remove(user)
            if len(targets) == 0:
                break

        await voice_client.disconnect()

    @app_commands.command()
    @app_commands.check(GuildPermissions.can_kick)
    async def grenade(self, interaction: Interaction):
        """Plays grenade sound while everyone is scattered across various channels."""

        voice_client = await join_users_vc(self.bot, interaction)

        if not voice_client:
            await interaction.response.send_message("Something went wrong :(")
            return

        await interaction.response.send_message("**GRENAAAADDEEE!!**")

        grenade_sound = YTDLSource.from_file("sounds/grenade_oh_fudge.wav")
        voice_client.play(grenade_sound)

        # sleep so users can hear grenade and "OH FUDGE"
        await asyncio.sleep(3)

        all_voice_channels = interaction.guild.voice_channels

        # avoid kicking them into a channel they dont have access to
        for member in voice_client.channel.members:
            if member.bot:
                continue

            available_channels = []
            for channel in all_voice_channels:
                if channel.permissions_for(member).connect:
                    available_channels.append(channel)

            await member.edit(voice_channel=random.choice(available_channels))

        await voice_client.disconnect()

    # -vvv- commands suggested by Tunu -vvv-
    @app_commands.command()
    async def minecraft(self, interaction: Interaction):
        """Plays the "Mining - Minecraft Parody of Drowning" music video."""

        voice_client = await join_users_vc(self.bot, interaction)

        if not voice_client:
            await interaction.response.send_message("Something went wrong :(")
            return

        await interaction.response.send_message("NOW PLAYING: TUNUS FAVORITE SONG")

        # join voice_channel and play minecraft music video
        url = "https://www.youtube.com/watch?v=kMlLz7stjwc"
        minecraft_meme_music = await YTDLSource.from_url(
            url, loop=self.bot.loop, stream=True
        )
        voice_client.play(minecraft_meme_music, after=lambda e: self._on_song_finish(e))

    # -vvv- commands suggested by Sandi -vvv-
    @app_commands.command()
    async def smd(self, interaction: Interaction):
        """Plays the grapefruit technique video. I'm sorry."""

        voice_client = await join_users_vc(self.bot, interaction)

        if not voice_client:
            await interaction.response.send_message("Something went wrong :(")
            return

        await interaction.response.send_message(
            "NOW PLAYING: SANDIS FAVORITE TECHNIQUE"
        )

        # join voice_channel and play minecraft music video
        url = "https://www.youtube.com/watch?v=VmBMxMivJXQ&t=4s"
        grapefruit_video = await YTDLSource.from_url(
            url, loop=self.bot.loop, stream=True
        )
        voice_client.play(grapefruit_video, after=lambda e: self._on_song_finish(e))

    # -vvv- commands suggested by Amar -vvv-
    @app_commands.command()
    async def outro(self, interaction: Interaction):
        """Plays an outro song before you leave."""

        voice_client = await join_users_vc(self.bot, interaction)

        if not voice_client:
            await interaction.response.send_message("Something went wrong :(")
            return

        await interaction.response.send_message(
            "Now playing the outro song", ephemeral=True
        )

        # join voice_channel and play "TheFatRat - Xenogenesis"
        outro_song = YTDLSource.from_file("sounds/outro_meme.mp3")
        voice_client.play(outro_song, after=lambda e: self._on_song_finish(e))

    # -vvv- commands suggested by Aladin -vvv-
    @app_commands.command()
    async def goggins(self, interaction: Interaction):
        """Drops a motivational quote from David Goggins."""

        goggins_quotes = [
            "The most important conversations you’ll ever have are the ones you’ll have with yourself. You wake up with them, you walk around with them, you go to bed with them, and eventually, you act on them. Whether they be good or bad. We are all our own worst haters and doubters because self-doubt is a natural reaction to any bold attempt to change your life for the better. You can’t stop it from blooming in your brain, but you can neutralize it, and all the other external chatter by asking, What if?",
            "Motivation is crap. Motivation comes and goes. When you’re driven, whatever is in front of you will get destroyed.",
            "The things that we decide to run from are the truth. When you make excuses, you’re running from the truth.",
            "In life, there is no gift as overlooked or inevitable as failure. I’ve had quite a few and have learned to relish them because if you do the forensics you’ll find clues about where to make adjustments and how to eventually accomplish your task.",
            "It’s easier to accept the fact that you’re just not good enough. We all have a lot more than we think we have.",
            "Life is one big tug of war between mediocrity and trying to find your best self.",
            "Suffering is a test. That’s all it is. Suffering is the true test of life.",
            "You’re gonna fail, you’re gonna be in your head, and you’re gonna be saying I’m not good enough. It’s about how you overcome that.",
            "The Buddha famously said that life is suffering. I’m not a Buddhist, but I know what he meant and so do you. To exist in this world, we must contend with humiliation, broken dreams, sadness, and loss. That’s just nature. Each specific life comes with its own personalized portion of pain. It’s coming for you. You can’t stop it. And you know it.",
            "Then I thought of an English middle-distance runner from back in the day named Roger Bannister. When Bannister was trying to break the four-minute mile in the 1950s, experts told him it couldn’t be done, but that didn’t stop him. He failed again and again, but he persevered, and when he ran his historic mile in 3:59.4 on May 6, 1954, he didn’t just break a record, he broke open the floodgates simply by proving it possible. Six weeks later, his record was eclipsed, and by now over 1,000 runners have done what was once thought to be beyond human capability.",
            "To make fun of or try to intimidate someone they didn’t even know based on race alone was a clear indication that something was very wrong with them, not me.",
            "You gotta start your journey. It may suck, but eventually, you will come out the other side on top.",
            "Don’t worry about the elements around you and what’s going on. You gotta get out there and get it.",
            "Life is one long motherf**king imaginary game that has no scoreboard, no referee, and isn’t over until we’re dead and buried",
            "A true leader stays exhausted, abhors arrogance, and never looks down on the weakest link. He fights for his men and leads by example. That’s what it meant to be uncommon among uncommon. It meant being one of the best and helping your men find their best too.",
            "The worst thing that can happen to a man is to become civilized.",
            "Pain unlocks a secret doorway in the mind, one that leads to both peak performance, and beautiful silence.",
            "But what put distance between me and almost everybody else in that platoon is that I didn’t let my desire for comfort rule me.",
            "Your entitled mind is dead weight. Cut it loose. Don’t focus on what you think you deserve. Take aim on what you are willing to earn!",
            "If you’re not physically and mentally prepared for what life is going to throw at you, then you’re just going to crumble, And then, you’re no good to nobody.",
            "The vast majority of us are slaves to our minds. Most don’t even make the first effort when it comes to mastering their thought process because it’s a never-ending chore and impossible to get right every time.",
            "Insanity is doing the same thing over and over again and expecting a different result.",
            "We all like to take this four-lane highway, but we always step over the shovel. All I did was pick up that shovel and made my own path.",
            "But visualization isn’t simply about daydreaming of some trophy ceremony—real or metaphorical. You must also visualize the challenges that are likely to arise and determine how you will attack those problems when they do. That way you can be as prepared as possible on the journey.",
            "A lot of us don’t know about another world that exists for us because it’s on the other side of suffering. That’s the real growth in life.",
            "Most of this generation quits the second they get talked to. It’s so easy to be great nowadays because most people are just weak, If you have any mental toughness, any fraction of self-discipline – the ability to not want to do it, but still do it – you’ll be successful.",
            "The most important conversations you’ll ever have are the ones you’ll have with yourself.",
            "By the time I graduated, I knew that the confidence I’d managed to develop didn’t come from a perfect family or God-given talent. It came from personal accountability which brought me self-respect, and self-respect will always light a way forward.",
            "There is no more time to waste. Hours and days evaporate like creeks in the desert. That’s why it’s okay to be cruel to yourself as long as you realize you’re doing it to become better.",
            "You want to be uncommon amongst uncommon people. Period.",
            "Be more than motivated, be more than driven, become literally obsessed to the point where people think you’re f*cking nuts.",
            "Most wars are won or lost in our own heads, and when we’re in a foxhole we usually aren’t alone, and we need to be confident in the quality of the heart, mind, and dialogue of the person hunkered down with us. Because at some point we will need some empowering words to keep us focused and deadly.",
            "The only reason why I became successful was because I went towards the truth. As painful and as brutal as it is, it changed me. It allowed me, in my own right, to become the person who I am today.",
            "I understand the temptation to sell short, but I also know that impulse is driven by your mind’s desire for comfort, and it’s not telling you the truth.",
            "Everyone fails sometimes and life isn’t supposed to be fair, much less bend to your every whim.",
            "I don’t stop when I’m tired. I stop when I’m done.",
            "Everybody wants a quick fix like 6-minute abs – you may get some results from it, but those results won’t be permanent. The permanent results come from you having to suffer. You have to make that a tattoo on your brain so that when the hard time comes again, you don’t forget it.",
            "To those people who say ‘I’m good’ – You ain’t good man, you ain’t never (expletive) arrived. That’s just my mentality… You may have more than I do, but you’ve never (expletive) arrived.",
            "There’s a bunch of guys that don’t like me and I don’t give a (expletive). I’m a warrior.",
            "You can push yourself to a place that is beyond the current capability or temporal mindset of the people you work with, and that’s okay. Just know that your supposed superiority is a figment of your own ego. So don’t lord it over them, because it won’t help you advance as a team or as an individual in your field. Instead of getting angry that your colleagues can’t keep up, help pick your colleagues up and bring them with you!",
            "You can’t let a simple failure derail your mission, or let it worm so far up your ass it takes over your brain and sabotages your relationships with people who are close to you. Everyone fails sometimes and life isn’t supposed to be fair, much less bend to your every whim.",
            "You are giving up instead of getting hard! Tell the truth about the real reasons for your limitations and you will turn that negativity, which is real, into jet fuel. Those odds stacked against you will become a damn runway!",
            "Everybody wants a quick fix like 6-minute abs – you may get some results from it, but those results won’t be permanent. The permanent results come from you having to suffer. You have to make that a tattoo on your brain so that when the hard time comes again, you don’t forget it.",
            "A warrior is a guy that goes ‘I’m here again today. I’ll be here again tomorrow and the next day.’ It’s a person who puts no limit on what’s possible.",
            "You can be born in a f*cking sewer and still be the baddest motherf*cker on earth.",
            "People take classes on self-help, mental toughness, breathing control – the only way to get tougher is to put yourself in hellacious situations.",
            "When you’re exhausted, weak, and tired and everyone around you looks just as bad as you or even worse – that’s the perfect time for you to make a statement. You let everyone around you know that when their life ends, that’s when yours begins.",
            "This life is all a f*cking mind game. Realize that. Own it!",
            "The mind is the most powerful thing in the world. The mind has capabilities that are so unknown, and being able to tap into that is on the other side of suffering.",
            "The only person who was going to turn my life around was me. The only way I could get turned around was to put myself through the worst things possible that a human being could ever endure.",
            "Denial is the ultimate comfort zone.",
            "STAY HARD",
            "STAY HARD",
            "STAY HARD",
            "STAY HARD",
            "STAY HARD",
            "YOU DONT KNOW ME SON",
            "YOU DONT KNOW ME SON",
            "YOU DONT KNOW ME SON",
            "YOU DONT KNOW ME SON",
            "YOU DONT KNOW ME SON",
        ]

        await interaction.response.send_message(
            f'> "{random.choice(goggins_quotes)}" - **David Goggins**'
        )
