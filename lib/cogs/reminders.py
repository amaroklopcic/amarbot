import asyncio
from datetime import datetime, timedelta
from typing import List

import dateparser
from discord.ext import commands

from lib.cogs.cog import CommonCog
from lib.firebase import get_firestore


class Reminder:
    """A wrapper for reminder data. Use `RemindersCog.create_reminder` to create these."""

    def __init__(
        self,
        firestore_doc_id: str,
        channel_id: str,
        message_id: str,
        user_id: str,
        dt: datetime,
    ) -> None:
        self.firestore_doc_id = firestore_doc_id
        self.channel_id = channel_id
        self.message_id = message_id
        self.user_id = user_id
        self.dt = dt


class RemindersCog(CommonCog):
    """Commands related to reminders."""

    # TODO: add command to remove reminders

    def __init__(self, bot: commands.Bot) -> None:
        super().__init__(bot)
        self.loop = self.bot.loop
        self.reminder_tasks: List[asyncio.Task] = []

        # TODO: add a task to clean up any past/old reminders that didn't get deleted

        # fetch reminders
        self._sync_reminders_task = self.loop.create_task(self.sync_reminders())

    def schedule_reminder(self, reminder: Reminder):
        """Schedules a new reminder to be run."""
        task = self.loop.create_task(self.run_reminder(reminder))
        self.reminder_tasks.append(task)

    async def sync_reminders(self):
        """Checks Firestore to see which reminders need to be pulled in, and then
        schedules them. Any reminder tasks that are currently scheduled are cancelled,
        repulled from Firestore, and rescheduled.
        """
        print("syncing reminders...")
        print("clearing existing reminders...")
        for reminder in self.reminder_tasks:
            reminder.cancel()

        self.reminder_tasks = []

        print("fetching reminders from the db...")
        db = get_firestore()
        reminder_docs = await db.collection("reminders").get()

        print(f"resyncing {len(reminder_docs)} reminders...")
        for reminder_doc in reminder_docs:
            doc_id = reminder_doc.id
            data = reminder_doc.to_dict()

            reminder = Reminder(
                doc_id,
                data["channel_id"],
                data["message_id"],
                data["user_id"],
                data["dt"],
            )

            self.schedule_reminder(reminder)

    async def run_reminder(self, reminder: Reminder):
        sleep_time = (reminder.dt - datetime.utcnow()).total_seconds()
        if sleep_time <= 0:
            print("attempted to run reminder that is in the past, skipping")
            return
        await asyncio.sleep(sleep_time)

        channel = await self.bot.fetch_channel(reminder.channel_id)
        message = await channel.fetch_message(reminder.message_id)
        await message.reply(
            f"<@{reminder.user_id}> Hey! You told me to remind you of this message."
        )

        db = get_firestore()
        doc_ref = db.collection("reminders").document(reminder.firestore_doc_id)
        await doc_ref.delete()

    async def create_reminder(
        self,
        channel_id: str,
        message_id: str,
        user_id: str,
        dt: datetime,
    ):
        """Creates and returns a `Reminder` instance, uploading it to Firestore in the
        process.
        """
        db = get_firestore()
        result = await db.collection("reminders").add(
            {
                "channel_id": channel_id,
                "message_id": message_id,
                "user_id": user_id,
                "dt": dt,
            }
        )
        doc_ref = result[1]
        return Reminder(doc_ref.id, channel_id, message_id, user_id, dt)

    @commands.command()
    async def remind(self, ctx: commands.Context, who: str, *, when: str):
        target_member_id = None
        if who == "me":
            target_member_id = ctx.author.id
        elif who.startswith("<@") and who.endswith(">"):
            target_member_id = who[2:-1]
        else:
            await ctx.send(
                f'Not sure what "{who}" is, try `remind me <timeframe>` or '
                "`remind @user <timeframe>`"
            )
            return

        now = datetime.utcnow()
        parsed_dt = dateparser.parse(when, settings={"RELATIVE_BASE": now})
        delta: timedelta = abs(now - parsed_dt)
        target_dt = now + delta

        reminder = await self.create_reminder(
            ctx.channel.id, ctx.message.id, target_member_id, target_dt
        )
        self.schedule_reminder(reminder)

        async with ctx.typing():
            # TODO: make the delta string nicer (e.g. "I'll remind you in 1 day", or
            # "I'll remind you in 2 hours", or "... in 15 days, 6 hours, and 15 minutes")
            await ctx.send(f"Gotcha! I'll remind you in {delta}.")

    @commands.command()
    async def reminders(self, ctx: commands.Context):
        """Shows current reminders for this guild, ordered by upcoming reminders first."""
        target_member_id = ctx.author.id

        db = get_firestore()
        docs = (
            await db.collection("reminders")
            .where("user_id", "==", target_member_id)
            .order_by("dt")
            .get()
        )

        reminders = []
        for doc in docs:
            data = doc.to_dict()
            channel = await ctx.guild.fetch_channel(data["channel_id"])
            message = await channel.fetch_message(data["message_id"])
            reminders.append(
                {"jump_url": message.jump_url, "channel_name": channel.name, **data}
            )

        if len(reminders) == 0:
            await ctx.send("You don't have reminders.")
            return

        list_str = "Here are your current reminders:\n"
        for index, reminder in enumerate(reminders):
            list_str += f"> {index + 1}. {reminder['jump_url']}\n"

        async with ctx.typing():
            await ctx.send(list_str.strip())

    @commands.command()
    async def delete_reminder(self, ctx: commands.Context, reminder_index: int):
        """Deletes a reminder by using the reminder index (run `reminders` first to get
        the reminder index).
        """
        target_member_id = ctx.author.id

        db = get_firestore()
        docs = (
            await db.collection("reminders")
            .where("user_id", "==", target_member_id)
            .order_by("dt")
            .get()
        )

        if len(docs) == 0:
            await ctx.send("You don't have any reminders.")
            return

        try:
            await docs[reminder_index - 1].reference.delete()
        except Exception as e:
            print(f"Caught exception when trying to delete reminder:\n{e}")
            await ctx.send(f"Couldn't delete reminder at index {reminder_index}.")
            return

        reminders = []
        for index, doc in enumerate(docs):
            if index + 1 == reminder_index:
                continue
            data = doc.to_dict()
            channel = await ctx.guild.fetch_channel(data["channel_id"])
            message = await channel.fetch_message(data["message_id"])
            reminders.append(
                {"jump_url": message.jump_url, "channel_name": channel.name, **data}
            )

        list_str = (
            f"Successfully deleted reminder #{reminder_index}! "
            "Here are your current reminders:\n"
        )
        for index, reminder in enumerate(reminders):
            list_str += f"> {index + 1}. {reminder['jump_url']}\n"

        await self.sync_reminders()

        async with ctx.typing():
            await ctx.send(list_str.strip())
