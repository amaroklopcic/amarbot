import discord


class GuildPermissions:
    @staticmethod
    def is_owner(interaction: discord.Interaction):
        return interaction.user.id == interaction.guild.owner.id

    @staticmethod
    def is_admin(interaction: discord.Interaction):
        return interaction.user.guild_permissions.administrator

    @staticmethod
    def can_kick(interaction: discord.Interaction):
        return interaction.user.guild_permissions.kick_members
