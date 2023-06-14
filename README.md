# AmarBot
A custom, non-serious, utility, and music featuring Discord bot I use for my
Discord server.
It features whatever fun commands I wanted to add or stuff that was requested
by the community. I have a small community, so I felt comfortable enough not adding
any priveledge checks yet. If you plan on using this in your own server, please keep 
that in mind. Also, this bot is only hosted for my community's own personal use; if you
want to use this bot, you'll have to host it yourself.


## Features
### Music Player Commands
- `play {query}` --> Plays from a query or url (almost anything youtube_dl supports).
- `queue` --> Shows the current queue.
- `queue {query}` --> Add a song to the queue.
- `pop` --> Remove the most recent added song from the queue.
- `pop {index}` --> Remove a song from the queue at index.
- `skip` --> Skip the current playing song.
- `stop` --> Stops the music player and disconnects the bot from the voice channel.
- `pause` --> Pause the music player.
- `resume` --> Resume the music player.
- `volume {1-100}` --> Changes the music player's volume.

### Utility Commands
- `utils count` --> Returns total number of text messages from author in a channel.
- `utils channel_count` --> Returns total number of text messages in a channel.
- `utils guild_export` --> Returns all the messages from all the channels in a Discord 
guild, as a JSON file in your DMs. For owners only.

### Fun / Meme Commands
For obvious reasons, these commands are likely to be removed or disabled in a
future release. Funny at first, but they get annoying after a while.
- `roulette` --> Plays a gunshot sounds and kicks a random user from the voice
channel.
- `driveby` --> Plays machine gun sound while kicking multiple people from the
voice channel.
- `grenade` --> Plays grenade sound while everyone connected to the current voice
channel is scattered across various channels.
- `minecraft` --> Plays the
["Mining - Minecraft Parody of Drowning"](https://www.youtube.com/watch?v=kMlLz7stjwc) 
music video.
- `smd` --> Plays the grapefruit technique video. I'm sorry.
- `goggins` --> Drops a motivational quote from
[David Goggins](https://en.wikipedia.org/wiki/David_Goggins).

### Daily Inspirational Quotes
A scheduled cron job that posts inspirational quotes to a `#quote-of-the-day` channel if
it exists. Possible by the [theysaidso](https://theysaidso.com/) API.

## Development Quickstart
If you want to test out this bot in your own Discord server, here's how:
1. Start by creating an account & application on the [Discord developer portal](https://discord.com/developers/applications).
2. In the "Bot" section, give access to all "Gateway Intents" and create a token. Copy the
token and keep it somewhere safe for now.
3. Invite the bot to your Discord server. Do this by going to the "OAuth2" section, then
under "URL Generator", check the "bot" scope checkbox and "Administrator" permission
checkbox. The generated URL at the bottom of the page should take you through the steps 
to invite the bot to your Discord server.
4. Clone the repository locally.
```bash
git clone https://github.com/amaroklopcic/amarbot
```
5. Create a Python virtual environment and install the required dependencies.
```bash
python -m venv .venv;
source .venv/bin/activate;
pip install -U pip setuptools wheel;
pip install -r requirements.txt;
```
8. Create an `.env` file in the root of the project and add the following line to it,
replacing the fake key below with the one you copied from the Discord developer portal.
```bash
AMARBOT_TOKEN=sbhidihBISDIbihdsbihibsidSI29H9SXx.SDU99SDISD
```
9. Run it.
```bash
python amarbot.py
```
