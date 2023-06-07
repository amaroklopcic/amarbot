import asyncio

from discord.ext import commands

from lib.cogs.cog import CommonCog


class Acknowledge(CommonCog):
    """Attaches event listeners that react to commands"""

    developer_role_id = "385543611191787530"

    # -vvv- event listeners -vvv-
    @commands.Cog.listener()
    async def on_command(self, ctx: commands.Context):
        await self.acknowledge(ctx)

    @commands.Cog.listener()
    async def on_command_completion(self, ctx: commands.Context):
        await self.finish(ctx)

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.errors.CommandNotFound):
            await self.react_reject(ctx)
        else:
            await asyncio.gather(
                self.react_error(ctx),
                ctx.send(
                    "Something went wrong! Sorry :(\n" f"<@&{self.developer_role_id}>"
                ),
            )
