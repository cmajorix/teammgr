import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import Button, View, Modal
from dotenv import load_dotenv
import os
import sys

# THINGS I WANT TO ADD
# - slash commands
# - make it work w multiple teams/servers
# - add team roles
# - ping managers when enough ppl react yes or no
# - auto add to events and gcal

load_dotenv()

DEVMODE = "-D" in sys.argv
DEVGUILD = discord.Object(id=int(os.getenv("TESTGUILD")))
TOKEN = os.getenv("TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

client = commands.Bot(command_prefix='!', intents=intents)

@client.event
async def on_ready():
    client.tree.add_command(Team(), guild=(DEVGUILD if DEVMODE else None))
    await client.tree.sync(guild=(DEVGUILD if DEVMODE else None))
    print(f'Bot is ready and logged in as {client.user}')

class ConfirmView(View):
    def __init__(self, date, embed: discord.Embed, members: list[str]):
        super().__init__(timeout=None)
        self.date = date
        self.embed = embed
        self.members = members
        self.responses = {member: "No response" for member in members}

    async def update_embed(self, interaction: discord.Interaction):
        self.embed.clear_fields()
        for member in self.members:
            self.embed.add_field(name=member, value=self.responses[member], inline=False)
        await interaction.message.edit(embed=self.embed, view=self)

    @discord.ui.button(label="Yes", style=discord.ButtonStyle.green)
    async def yes_button(self, interaction: discord.Interaction, button: Button):
        member = interaction.user
        if member.name in self.members:
            self.responses[member.name] = "Yes"
            await self.update_embed(interaction)
            await interaction.response.defer()
        else:
            await interaction.response.send_message("You are not on this team!", ephemeral=True)

    @discord.ui.button(label="No", style=discord.ButtonStyle.red)
    async def no_button(self, interaction: discord.Interaction, button: Button):
        member = interaction.user
        if member.name in self.members:
            self.responses[member.name] = "No"
            await self.update_embed(interaction)
            await interaction.response.defer()
        else:
            await interaction.response.send_message("You are not on this team!", ephemeral=True)


@client.tree.command(description="Creates a poll to confirm a scrim time", guild=DEVGUILD)
@app_commands.guild_only()
async def confirm(ctx: discord.Interaction, team_name: str, date: str):
    guild = ctx.guild

    role = discord.utils.get(guild.roles, name=team_name)
    manager_role = discord.utils.get(guild.roles, name="val")

    if manager_role not in ctx.user.roles:
        await ctx.response.send_message(f"You need the '{manager_role.name}' role.", ephemeral=True)
        return

    if role is None:
        await ctx.response.send_message(f"Role '{team_name}' not found.", ephemeral=True)
        return
    
    members = [member.name for member in role.members]

    # Create an embed for the poll
    embed = discord.Embed(title=f"{team_name} Scrim for {date}", color=discord.Color.dark_purple())
    for member in members:
        embed.add_field(name=member, value="No response", inline=False)

    view = ConfirmView(date, embed, members)

    await ctx.response.send_message(embed=embed, view=view)

class Team(app_commands.Group):
    def __init__(self):
        super().__init__()
        self.description = "Commands for managing and creating teams"
        self.guild_only = True

    @app_commands.command(description="Create a new team")
    async def create(self, interaction: discord.Interaction, role: discord.Role):
        team_roles = {}
        await interaction.response.send_message("Creating new team.", ephemeral=True)
        for member in role.members:
            await interaction.followup.send(f"Please type the role for {member}:", ephemeral=True)
            def check(msg):
                return msg.author == interaction.user and msg.channel == interaction.channel
            response = await client.wait_for("message", check=check)
            team_roles[member.id] = response.content
            await response.delete()
        

client.run(TOKEN)