import asyncio
from datetime import datetime, timedelta, timezone
from typing import List, Tuple

import dateparser
from discord import Interaction, app_commands
from discord.ext import commands
from google.cloud.firestore import DocumentReference, DocumentSnapshot, FieldFilter

from lib.firebase import get_firestore
from lib.logging import get_logger


class Member:
    def __init__(self, id: int, name: str) -> None:
        self.id = id
        self.name = name
        self.mention = f"<@{self.id}>"

    def to_dict(self):
        return {"id": self.id, "name": self.name}


class Reminder:
    """A wrapper for reminder data. Use `RemindersCog.create_reminder` to create these."""

    def __init__(
        self,
        guild_id: int,
        channel_id: int,
        user: Member,
        target_user: Member,
        content: str,
        dt: datetime,
        _firestore_doc_ref: DocumentReference = None,
    ) -> None:
        self.guild_id = guild_id
        self.channel_id = channel_id
        self.user = user
        self.target_user = target_user
        self.content = content
        self.dt = dt

        self._firestore_doc_ref = _firestore_doc_ref

    @classmethod
    def from_firestore(cls, snap: DocumentSnapshot):
        data = snap.to_dict()
        user = Member(data["user"]["id"], data["user"]["name"])
        target_user = Member(data["target_user"]["id"], data["target_user"]["name"])
        return cls(
            data["guild_id"],
            data["channel_id"],
            user,
            target_user,
            data["content"],
            data["dt"],
            snap.reference,
        )

    def to_dict(self):
        return {
            "guild_id": self.guild_id,
            "channel_id": self.channel_id,
            "user": self.user.to_dict(),
            "target_user": self.target_user.to_dict(),
            "content": self.content,
            "dt": self.dt,
        }

    async def create(self) -> DocumentReference:
        """Update or create the document if it doesn't exist. Soft fail if we are in an
        environment where Firebase/Firestore don't exist or can't be reached.
        """
        # TODO: move get_firestore to the top of document so we aren't creating new
        # instances every time we update a doc
        db = get_firestore()
        # TODO: check if self._firestore_doc_id is set and update, else create the doc
        result = await db.collection("reminders").add(self.to_dict())
        self._firestore_doc_ref = result[1]
        return result[1]

    async def delete(self):
        """Delete the document from Firestore. Soft fail if we are in an environment
        where Firebase/Firestore don't exist or can't be reached.
        """
        if not self._firestore_doc_ref:
            # no firestore doc reference set, do nothing
            return

        db = get_firestore()
        return await db.document("reminders", self._firestore_doc_ref.id).delete()


class RemindersCog(commands.GroupCog, group_name="reminders"):
    """Commands related to reminders."""

    def __init__(self, bot: commands.Bot) -> None:
        super().__init__()

        self.logger = get_logger(__name__)
        self.logger.debug("Initializing RemindersCog...")

        self.bot = bot
        self.loop = bot.loop
        self.reminder_tasks: List[Tuple[Reminder, asyncio.Task]] = []

        # TODO: add a task to clean up any past/old reminders that didn't get deleted

        # fetch reminders
        self._sync_reminders_task = self.loop.create_task(self.sync_reminders())

    def schedule_reminder(self, reminder: Reminder):
        """Schedules a new reminder to be run."""
        self.logger.debug(f"scheduling new reminder to run at {reminder.dt}...")
        task = self.loop.create_task(self.run_reminder(reminder))
        self.reminder_tasks.append((reminder, task))

    async def sync_reminders(self):
        """Checks Firestore to see which reminders need to be pulled in, and then
        schedules them. Any reminder tasks that are currently scheduled are cancelled,
        repulled from Firestore, and rescheduled.
        """
        try:
            self.logger.debug("waiting until bot is ready before synchronizing...")
            while True:
                await asyncio.sleep(1)
                if self.bot.is_ready():
                    break
            self.logger.debug("bot is ready! synchronizing reminders...")

            for reminder_task in self.reminder_tasks:
                reminder_task[1].cancel()

            self.reminder_tasks = []

            self.logger.debug(f"pulling reminders for {len(self.bot.guilds)} guilds...")
            db = get_firestore()
            reminders_count = 0
            for guild in self.bot.guilds:
                reminders_snap_list = (
                    await db.collection("reminders")
                    .where(filter=FieldFilter("guild_id", "==", guild.id))
                    .order_by("dt")
                    .get()
                )
                for reminder_snap in reminders_snap_list:
                    reminder = Reminder.from_firestore(reminder_snap)
                    reminders_count += 1
                    self.schedule_reminder(reminder)
            self.logger.debug(
                f"successfully pulled {reminders_count} reminders for {len(self.bot.guilds)} guilds!"
            )
        except:
            self.logger.exception(
                f"Something went wrong when trying to synchronize reminders!"
            )
            raise

    async def run_reminder(self, reminder: Reminder):
        try:
            sleep_time = (
                reminder.dt.replace(tzinfo=timezone.utc) - datetime.now(timezone.utc)
            ).total_seconds()
            self.logger.debug(f"running reminder after {sleep_time} seconds...")

            if sleep_time <= 0:
                self.logger.warning(
                    "Attempted to run a reminder that is in the past, skipping! This "
                    "is an indicator that reminders are not getting removed from the "
                    "db after they've been ran."
                )
                return

            await asyncio.sleep(sleep_time)

            guild = await self.bot.fetch_guild(reminder.guild_id)
            channel = await guild.fetch_channel(reminder.channel_id)

            message = None
            if reminder.target_user.id == reminder.user.id:
                message = await channel.send(
                    f"Hey, <@{reminder.user.id}>, you set a reminder for your self to "
                    f"{reminder.content}"
                )
            else:
                self.logger.debug(
                    (type(reminder.target_user.id), type(reminder.user.id))
                )
                self.logger.debug((reminder.target_user.id, reminder.user.id))
                message = await channel.send(
                    f"Hey, <@{reminder.target_user.id}>, <@{reminder.user.id}> is "
                    f"reminding you to: *{reminder.content}*"
                )

            await reminder.delete()

            # remove the reminder from the reminder tasks
            reminder_index = None
            for index, reminder_task in enumerate(self.reminder_tasks):
                if (
                    reminder._firestore_doc_ref.id
                    == reminder_task[0]._firestore_doc_ref.id
                ):
                    reminder_index = index
                    break
            self.reminder_tasks.pop(reminder_index)

            self.logger.debug("Reminder successfully sent!")
        except asyncio.exceptions.CancelledError:
            self.logger.debug("Successfully cancelled a reminder")
        except Exception:
            self.logger.exception(
                f"Something went wrong when trying to run a reminder!"
            )
            raise

    async def create_reminder(
        self,
        guild_id: int,
        channel_id: int,
        user: Member,
        target_user: Member,
        content: str,
        dt: datetime,
    ):
        """Creates and returns a `Reminder` instance, uploading it to Firestore in the
        process.
        """
        reminder = Reminder(guild_id, channel_id, user, target_user, content, dt)
        await reminder.create()
        return reminder

    def get_reminders(self, user_id: int):
        """Get a list of reminders for `user_id`."""
        return [
            r
            for r in self.reminder_tasks
            if r[0].user.id == user_id or r[0].target_user.id == user_id
        ]

    @app_commands.command()
    async def add(self, interaction: Interaction, who: str, content: str, *, when: str):
        """Add a reminder for later.
        Example usage: `/reminders add @John make spaghetti in 1 hour`
        """
        guild_id = interaction.guild.id
        channel_id = interaction.channel.id
        user = Member(interaction.user.id, interaction.user.name)
        target_user = None
        if who == "me":
            target_user = user
        elif who.startswith("<@") and who.endswith(">"):
            id = int(who[2:-1])
            name = (await interaction.guild.fetch_member(id)).display_name
            target_user = Member(id, name)
        else:
            await interaction.response.send_message(
                f'Not sure who "{who}" is, try `/reminders add me <content> '
                "<timeframe>` or `/reminders add @user <content> <timeframe>`",
                ephemeral=True,
            )
            return

        self.logger.debug(
            f"Creating new reminder in {interaction.guild.name}.{interaction.channel.name}"
        )

        # invert negative delta so that all reminders are in the future (even when
        # client submits something like !remind me 1 hour ago)
        now = datetime.utcnow()
        parsed_dt = dateparser.parse(when, settings={"RELATIVE_BASE": now})
        delta: timedelta = abs(now - parsed_dt)
        target_dt = now + delta

        reminder = await self.create_reminder(
            guild_id, channel_id, user, target_user, content, target_dt
        )
        self.schedule_reminder(reminder)

        # TODO: make the delta string nicer (e.g. "I'll remind you in 1 day", or
        # "I'll remind you in 2 hours", or "... in 15 days, 6 hours, and 15 minutes")
        if user == target_user:
            await interaction.response.send_message(
                f"Gotcha! I'll remind you to {content} in {delta}.", ephemeral=True
            )
        else:
            await interaction.response.send_message(
                f"Gotcha! I'll remind {target_user.name} to {content} in {delta}.",
                ephemeral=True,
            )

    @app_commands.command()
    async def list(self, interaction: Interaction):
        """Shows current reminders for this guild, ordered by upcoming reminders first."""
        user_id = interaction.user.id

        reminders = self.get_reminders(user_id)

        channel_jump_urls = {}
        list_str = "Here are your current reminders:\n"
        for index, reminder in enumerate(reminders):
            reminder = reminder[0]

            jump_url = channel_jump_urls.get(reminder.channel_id)
            if jump_url is None:
                channel = await self.bot.fetch_channel(reminder.channel_id)
                channel_jump_urls[reminder.channel_id] = channel.jump_url
                jump_url = channel.jump_url

            list_str += (
                f"> {index + 1}. Remind <@{reminder.target_user.id}> to "
                f"{reminder.content} in {jump_url} (created by <@{reminder.user.id}>)\n"
            )

        if len(reminders) == 0:
            await interaction.response.send_message(
                "You don't have reminders.", ephemeral=True
            )
        else:
            await interaction.response.send_message(list_str.strip(), ephemeral=True)

    @app_commands.command()
    async def delete(self, interaction: Interaction, reminder_index: int):
        """Deletes a reminder by using the reminder index (run `reminders` first to get
        the reminder index).
        """
        user_id = interaction.user.id

        reminders = self.get_reminders(user_id)

        if len(reminders) == 0:
            await interaction.response.send_message(
                "You don't have reminders.", ephemeral=True
            )
            return

        if reminder_index > len(reminders):
            await interaction.response.send_message(
                f"Reminder index is out of bounds, you only have {len(reminders)}.",
                ephemeral=True,
            )
            return

        reminder = self.reminder_tasks.pop(reminder_index - 1)
        reminder[1].cancel()
        await reminder[0].delete()

        await interaction.response.send_message(
            f"Successfully deleted reminder: *{reminder[0].content}* (#{reminder_index}).",
            ephemeral=True,
        )
