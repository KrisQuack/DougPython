import discord
from discord import app_commands
from discord.ext import commands


class Lockdown(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

    @app_commands.command(name="lockdown", description="Resrict a channel to stricter automod rules")
    @app_commands.checks.has_permissions(moderate_members=True)
    @app_commands.guild_only()
    @app_commands.describe(
        channel="The channel to lockdown"
    )
    async def lockdown(self, interaction: discord.Interaction, channel: discord.TextChannel):
        await interaction.response.defer(ephemeral=True)
        # Check if a message is already pinned with the channel id
        pinned_messages = await self.client.statics.mod_channel.pins()
        for message in pinned_messages:
            if message.embeds and message.embeds[0].footer.text == str(channel.id):
                await interaction.followup.send(f'Lockdown Menu Already Exists: {message.jump_url}', ephemeral=True)
                return
        embed = discord.Embed(
            title=f"Lockdown: {channel.name}",
            description="""
This menu is now persistent, You can revisit it at any time by clicking it in the pins. You can toggle the buttons any time to change access. Once you are done with the menu you can click Restore to sync the channels permissions and remove the menu.

**Strict Automod**: Applies discords over the top automod rules to the channel along side out own list of blocked emotes and words (including letters, numbers and commonly used combinations of offensive emotes)
**Slowmode**: Sets the channel to a 30 second slowmode (Removes all slow mods when toggled off)
**Ext. Emotes**: Removes the ability to use emotes from other servers
**Ext. Stickers**: Removes the ability to use stickers from other servers
**Reactions**: Removes the ability to react to messages
**Embeds**: Removes the ability to embed links in chat
**Attachments**: Removes the ability to send attachments in chat
**Restore**: Restores the channel to its original permissions and removes the menu
""",
            color=discord.Color.dark_purple()
        )
        embed.set_author(name=interaction.user.global_name, icon_url=interaction.user.avatar.url)
        embed.set_footer(text=str(channel.id))

        # Send the message
        view = LockdownView()
        synced = channel.permissions_synced
        if synced:
            # Set the button styles based on the original values
            overwrites = channel.overwrites_for(channel.guild.default_role)
            overwrites.update(external_emojis=True, external_stickers=True, embed_links=True, attach_files=True)
            await channel.set_permissions(channel.guild.default_role, overwrite=overwrites)
        else:
            # Disable the buttons for permissions
            view.children[2].disabled = True
            view.children[2].style = discord.ButtonStyle.grey
            view.children[3].disabled = True
            view.children[3].style = discord.ButtonStyle.grey
            view.children[4].disabled = True
            view.children[4].style = discord.ButtonStyle.grey
            view.children[5].disabled = True
            view.children[5].style = discord.ButtonStyle.grey
            view.children[6].label = "Restore channel (permissions not synced)"

        message: discord.Message = await self.client.statics.mod_channel.send(embed=embed, view=view)
        await message.pin()
        if synced:
            await interaction.followup.send(f'Lockdown Menu Generated: {message.jump_url}', ephemeral=True)
        else:
            await interaction.followup.send(
                f'Lockdown Menu Generated: {message.jump_url}\n\n**Channel permissions not synced to category, Permission options disabled**',
                ephemeral=True)


class LockdownView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Strict AutoMod Inactive", style=discord.ButtonStyle.red, custom_id="automod", row=1)
    async def automod(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Get the embed from the message
        channel_id = interaction.message.embeds[0].footer.text
        channel = interaction.guild.get_channel(int(channel_id))
        # Get automod rules
        rule1 = await interaction.guild.fetch_automod_rule(1194682146124738570)
        rule2 = await interaction.guild.fetch_automod_rule(1194684593119445134)
        # Toggle the button
        if channel in rule1.exempt_channels:
            # Remove the channel from the exceptions
            new_exceptions = rule1.exempt_channels
            if channel in new_exceptions:
                new_exceptions.remove(channel)
            await rule1.edit(exempt_channels=new_exceptions)
            await rule2.edit(exempt_channels=new_exceptions)
        else:
            # Add the channel back to the exceptions
            new_exceptions = rule1.exempt_channels
            if channel not in new_exceptions:
                new_exceptions.append(channel)
            await rule1.edit(exempt_channels=new_exceptions)
            await rule2.edit(exempt_channels=new_exceptions)
        # Edit the message
        await self.reload_buttons(interaction.message)
        await interaction.response.send_message("Updated", ephemeral=True)

    @discord.ui.button(label="Slowmode(30s) Inactive", style=discord.ButtonStyle.red, custom_id="slowmode", row=1)
    async def slowmode(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Get the embed from the message
        channel_id = interaction.message.embeds[0].footer.text
        channel = interaction.guild.get_channel(int(channel_id))
        # Toggle the button
        if channel.slowmode_delay != 30:
            await channel.edit(slowmode_delay=30)
        else:
            await channel.edit(slowmode_delay=0)
        # Edit the message
        await self.reload_buttons(interaction.message)
        await interaction.response.send_message("Updated", ephemeral=True)

    @discord.ui.button(label="Ext. Emotes Allowed", style=discord.ButtonStyle.green, custom_id="emotes", row=2)
    async def emotes(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Get the embed from the message
        channel_id = interaction.message.embeds[0].footer.text
        channel = interaction.guild.get_channel(int(channel_id))
        # Get the current permissions
        permissions = channel.overwrites_for(channel.guild.default_role)
        # Toggle the button
        if not permissions.external_emojis:
            permissions.update(external_emojis=True)
        else:
            permissions.update(external_emojis=False)
        # Update the permissions in the channel
        await channel.set_permissions(channel.guild.default_role, overwrite=permissions)
        # Edit the message
        await self.reload_buttons(interaction.message)
        await interaction.response.send_message("Updated", ephemeral=True)

    @discord.ui.button(label="Ext. Stickers Allowed", style=discord.ButtonStyle.green, custom_id="stickers", row=2)
    async def stickers(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Get the embed from the message
        channel_id = interaction.message.embeds[0].footer.text
        channel = interaction.guild.get_channel(int(channel_id))
        # Get the current permissions
        permissions = channel.overwrites_for(channel.guild.default_role)
        # Toggle the button
        if not permissions.external_stickers:
            permissions.update(external_stickers=True)
        else:
            permissions.update(external_stickers=False)
        # Update the permissions in the channel
        await channel.set_permissions(channel.guild.default_role, overwrite=permissions)
        # Edit the message
        await self.reload_buttons(interaction.message)
        await interaction.response.send_message("Updated", ephemeral=True)

    @discord.ui.button(label="Reactions Allowed", style=discord.ButtonStyle.green, custom_id="reactions", row=2)
    async def reactions(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Get the embed from the message
        channel_id = interaction.message.embeds[0].footer.text
        channel = interaction.guild.get_channel(int(channel_id))
        # Get the current permissions
        permissions = channel.overwrites_for(channel.guild.default_role)
        # Toggle the button
        if not permissions.add_reactions:
            permissions.update(add_reactions=True)
        else:
            permissions.update(add_reactions=False)
        # Update the permissions in the channel
        await channel.set_permissions(channel.guild.default_role, overwrite=permissions)
        # Edit the message
        await self.reload_buttons(interaction.message)
        await interaction.response.send_message("Updated", ephemeral=True)

    @discord.ui.button(label="Embeds Allowed", style=discord.ButtonStyle.green, custom_id="embeds", row=3)
    async def embeds(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Get the embed from the message
        channel_id = interaction.message.embeds[0].footer.text
        channel = interaction.guild.get_channel(int(channel_id))
        # Get the current permissions
        permissions = channel.overwrites_for(channel.guild.default_role)
        # Toggle the button
        if not permissions.embed_links:
            permissions.update(embed_links=True)
        else:
            permissions.update(embed_links=False)
        # Update the permissions in the channel
        await channel.set_permissions(channel.guild.default_role, overwrite=permissions)
        # Edit the message
        await self.reload_buttons(interaction.message)
        await interaction.response.send_message("Updated", ephemeral=True)

    @discord.ui.button(label="Attachments Allowed", style=discord.ButtonStyle.green, custom_id="attachments", row=3)
    async def attachments(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Get the embed from the message
        channel_id = interaction.message.embeds[0].footer.text
        channel = interaction.guild.get_channel(int(channel_id))
        # Get the current permissions
        permissions = channel.overwrites_for(channel.guild.default_role)
        # Toggle the button
        if not permissions.attach_files:
            permissions.update(attach_files=True)
        else:
            permissions.update(attach_files=False)
        # Update the permissions in the channel
        await channel.set_permissions(channel.guild.default_role, overwrite=permissions)
        # Edit the message
        await self.reload_buttons(interaction.message)
        await interaction.response.send_message("Updated", ephemeral=True)

    @discord.ui.button(label="Sync permissions and restore channel", style=discord.ButtonStyle.blurple, custom_id="restore", row=4)
    async def restore(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Get the embed from the message
        embed = interaction.message.embeds[0]
        channel_id = embed.footer.text
        channel = interaction.guild.get_channel(int(channel_id))
        # Restore each setting to its original value
        # Restore automod
        rule1 = await interaction.guild.fetch_automod_rule(1194682146124738570)
        rule2 = await interaction.guild.fetch_automod_rule(1194684593119445134)
        new_exceptions = rule1.exempt_channels
        if channel not in new_exceptions:
            new_exceptions.append(channel)
        await rule1.edit(exempt_channels=new_exceptions)
        await rule2.edit(exempt_channels=new_exceptions)
        # Sync the channels permissions
        if button.label == 'Sync permissions and restore channel':
            await channel.edit(sync_permissions=True)
        # Set slowmode if it was changed
        await channel.edit(slowmode_delay=0)

        # Delete the message
        await interaction.message.delete()

    async def reload_buttons(self, message: discord.Message):
        # Get the message
        embed = message.embeds[0]
        channel_id = embed.footer.text
        channel = message.guild.get_channel(int(channel_id))
        permissions = channel.overwrites_for(channel.guild.default_role)
        # Check if automod is active
        rule1 = await message.guild.fetch_automod_rule(1194682146124738570)
        def set_button_style_and_label(button, condition, active_label, inactive_label):
            if condition:
                button.style = discord.ButtonStyle.green
                button.label = active_label
            else:
                button.style = discord.ButtonStyle.red
                button.label = inactive_label

        set_button_style_and_label(self.children[0], channel not in rule1.exempt_channels, "Strict AutoMod Active", "Strict AutoMod Inactive")
        set_button_style_and_label(self.children[1], channel.slowmode_delay == 30, "Slowmode(30s) Active", "Slowmode(30s) Inactive")
        set_button_style_and_label(self.children[2], permissions.external_emojis, "Ext. Emotes Allowed", "Ext. Emotes Blocked")
        set_button_style_and_label(self.children[3], permissions.external_stickers, "Ext. Stickers Allowed", "Ext. Stickers Blocked")
        set_button_style_and_label(self.children[4], permissions.add_reactions, "Reactions Allowed", "Reactions Blocked")
        set_button_style_and_label(self.children[5], permissions.embed_links, "Embeds Allowed", "Embeds Blocked")
        set_button_style_and_label(self.children[6], permissions.attach_files, "Attachments Allowed", "Attachments Blocked")
        await message.edit(embed=embed, view=self)


async def setup(self: commands.Bot) -> None:
    await self.add_cog(Lockdown(self))
    self.add_view(LockdownView())
