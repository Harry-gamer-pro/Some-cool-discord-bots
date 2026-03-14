import discord
from discord.ext import commands
from discord import app_commands
import logging
from dotenv import load_dotenv
import os
import asyncio
from datetime import datetime, timedelta


load_dotenv()
token = os.getenv("NOLINOR_TOKEN")

handler = logging.FileHandler(filename='discord_nilinor.log', encoding='utf-8', mode='w')
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

current_test_Guild = discord.Object(id=1393270677850689606)

bot = commands.Bot(command_prefix='!', intents=intents)


def get_nolinor_emoji(guild):
    return discord.utils.get(guild.emojis, name="nolinor_holo") or ""





@bot.tree.command(name="kick", description="Kick a member from the server", guild=current_test_Guild)
async def kick(interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
    staff_role = discord.utils.get(interaction.guild.roles, id=1393270677968261208)
    if staff_role not in interaction.user.roles and not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message(f'Sorry {interaction.user.mention}, you do not have permission to do this.', ephemeral=True)
        return
    elif staff_role in interaction.user.roles or interaction.user.guild_permissions.administrator:
        if member:
            await member.kick()
            await interaction.response.send_message(f'{member.mention} has been kicked from the server.')

            if log_channel:
                await log_channel.send(f'{member.mention} was kicked by {interaction.user.mention} for reason: {reason}')
        else:
            await interaction.response.send_message('Member not found.')


@bot.tree.command(name="timeout", description="Timeout a member from the server", guild=current_test_Guild)
async def timeout(interaction: discord.Interaction, member: discord.Member, days: int = 0, hours: int = 0,
                  minutes: int = 0, reason: str = "No reason provided"):
    staff_role = discord.utils.get(interaction.guild.roles, id=1393270677968261208)
    if staff_role not in interaction.user.roles and not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message(f'Sorry {interaction.user.mention}, you do not have permission to do this.', ephemeral=True)
        return
    elif staff_role in interaction.user.roles or interaction.user.guild_permissions.administrator:

        if member:
            await member.timeout(timedelta(days=days, hours=hours, minutes=minutes), reason=reason)
            await interaction.response.send_message(
                f'{member.mention} has been timed out for {days} days, {hours} hours, {minutes} minutes.')

            if log_channel:
                await log_channel.send(f'{member.mention} was timed out by {interaction.user.mention} for reason: {reason}')
        else:
            await interaction.response.send_message('Member not found.')


@bot.tree.command(name="ban", description="Ban a member from the server", guild=current_test_Guild)
async def ban(interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
    staff_role = discord.utils.get(interaction.guild.roles, id=1393270677968261208)
    if staff_role not in interaction.user.roles and not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message(f'Sorry {interaction.user.mention}, you do not have permission to do this.', ephemeral=True)
        return
    elif staff_role in interaction.user.roles or interaction.user.guild_permissions.administrator:
        if  member:
            await member.ban()
            await interaction.response.send_message(f'{member.mention} has been banned from the server.')

            if log_channel:
                await log_channel.send(f'{member.mention} was banned by {interaction.user.mention} for reason: {reason}')
        else:
            await interaction.response.send_message('Member not found.')

@bot.tree.command(name="unban", description="Unban a member from the server", guild=current_test_Guild)
async def unban(interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
    staff_role = discord.utils.get(interaction.guild.roles, id=1393270677968261208)
    if staff_role not in interaction.user.roles and not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message(f'Sorry {interaction.user.mention}, you do not have permission to do this.', ephemeral=True)
        return
    elif staff_role in interaction.user.roles or interaction.user.guild_permissions.administrator:
        if member:
            await interaction.guild.unban(member)
            await interaction.response.send_message(f'{member.mention} has been unbanned from the server.')

            if log_channel:
                await log_channel.send(f'{member.mention} was unbanned by {interaction.user.mention} for reason: {reason}')
        else:
            await interaction.response.send_message('Member not found.')


#this wasn't coded by me but by AI
@bot.tree.command(name="activity_check", description="Ping everyone for an activity check", guild=current_test_Guild)
async def activity_check(interaction: discord.Interaction):
    staff_role = discord.utils.get(interaction.guild.roles, id=1393270677968261208)
    if staff_role not in interaction.user.roles and not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message(f'Sorry {interaction.user.mention}, you do not have permission to do this.', ephemeral=True)
        return
    await interaction.response.defer(ephemeral=True)
    message = await interaction.channel.send('@everyone Please react with:✅ for the activity check below!')
    await message.add_reaction('✅')

    reactors = []

    def check(reaction, user):
        return reaction.message.id == message.id and str(reaction.emoji) == '✅' and not user.bot and user not in reactors

    while len(reactors) < 3:
        reaction, user = await bot.wait_for('reaction_add', check=check)
        reactors.append(user)

    positions = ["1st", "2nd", "3rd"]
    result = "\n".join(f"{positions[i]}: {user.mention}" for i, user in enumerate(reactors))
    await interaction.channel.send(result)

@bot.command()
async def purge(ctx, number: int):
    staff_role = discord.utils.get(ctx.guild.roles, id=1393270677968261208)
    if staff_role in ctx.author.roles or ctx.author.guild_permissions.administrator:
            deleted = await ctx.channel.purge(limit=number)
            await ctx.send(f'{len(deleted)} messages have been deleted.', delete_after=5)
    else:
        await ctx.send(f'Sorry {ctx.author.mention}, you do not have permission to purge messages in this ticket.')


@bot.command()
async def purge_all(ctx):
    staff_role = discord.utils.get(ctx.guild.roles, id=1393270677968261208)
    if staff_role in ctx.author.roles or ctx.author.guild_permissions.administrator:
        await ctx.channel.purge(limit=None)
        await ctx.send(f'All messages have been deleted.', delete_after=15)
    else:
        await ctx.send(f'Sorry {ctx.author.mention}, you do not have permission to purge messages in this ticket.')

@bot.tree.command(name="ping", description="Check if the bot is responsive", guild=current_test_Guild)
async def ping(interaction: discord.Interaction):
    latency = round(bot.latency * 1000)
    await interaction.response.send_message(f"Pong! {latency} ms")
    await interaction.edit_original_response(content=f"Pong! Latency: {latency} ms,")

@bot.tree.command(name="about_nilinor", description="Learn about Nolinor Aviation", guild=current_test_Guild)
async def about_nolinor(interaction: discord.Interaction):
    embed = discord.Embed(title=f" {get_nolinor_emoji(interaction.guild)} | Nolinor Aviation", color=discord.Color.from_str("#1b2a4a"))
    embed.add_field(name="Who we are", value="Nolinor Aviation is a Canadian airline that specializes in charter services, cargo transport, and passenger flights to remote destinations. We have been in operation since 1992 and are known for our exceptional service, safety record and awesome old planes!", inline=False)
    embed.add_field(name="Our fleet", value="We operate a diverse fleet of aircraft, including the Boeing 737-200, Boeing 737-300, and the 737-400. Our fleet allows us to interchange between cargo and passenger services as well as a mix of both. We also serve a wide range of destinations and meet the unique needs of our customers.", inline=False)
    embed.add_field(name="Our services", value="We offer a variety of services, including charter flights for individuals and groups, cargo transport for businesses, and passenger flights to remote locations. Our team of experienced pilots and staff are dedicated to providing a safe and comfortable travel experience for all of our customers.", inline=False)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="get_code", description="Get the code for this bot", guild=current_test_Guild)
async def get_code(interaction: discord.Interaction):
    await interaction.response.send_message("This was my first discord bot i preatty much ever coded for a client so i decided to open source it! You can find the code for this bot on my GitHub: https://github.com/Harry-gamer-pro/Some-cool-discord-bots", ephemeral=True)

#Ai wrote the Fire script, i am not smart enought for " roles_to_remove = [r for r in member.roles if r.position >= cut_off_role.position]"
@bot.tree.command(name="fire", description="Fire a staff member and remove their roles", guild=current_test_Guild)
async def fire(interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
      cut_off_role = discord.utils.get(interaction.guild.roles, id=1480717428043284602)
      has_permission = (
          interaction.user.guild_permissions.administrator or
          discord.utils.get(interaction.user.roles, id=1393270677968261209) or
          interaction.user.id == 1371974280707047454
      )

      if not has_permission:
          await interaction.response.send_message(f'Sorry {interaction.user.mention}, you do not have permission to do this.', ephemeral=True)
          return

      if member.guild_permissions.administrator:
            await interaction.response.send_message(f'Sorry {interaction.user.mention}, you cannot fire an administrator.', ephemeral=True)
            return

      if not cut_off_role:
          await interaction.response.send_message('Staff role not found.', ephemeral=True)
          return

      if cut_off_role not in member.roles:
          await interaction.response.send_message(f'{member.mention} does not have the staff role.', ephemeral=True)
          return

      roles_to_remove = [r for r in member.roles if r.position >= cut_off_role.position]
      await member.remove_roles(*roles_to_remove, reason=reason)
      await interaction.response.send_message(f'{member.mention} has been fired and their roles have been removed for reason: {reason}', ephemeral=True)

      if log_channel:
          await log_channel.send(f'{member.mention} was fired by {interaction.user.mention} for reason: {reason}')


@bot.command()
async def shutdown(ctx):
      if ctx.author.id == 1371974280707047454:  # only you can shut it down
          await ctx.send("Shutting down...")
          await bot.close()
      else:
          await ctx.send("You don't have permission to do this.")





#Mod commands are above, and needed end commands are below, so they can be used in the ticket channels created by the ticket commands.

#-----------------------------------------------------------------------------------------------------------------------

#Ticketing system commands are below, and end commands for the ticket channels are above, so they can be used in the ticket channels created by the ticket commands.

class CloseModal(discord.ui.Modal, title="Close Ticket"):
    reason = discord.ui.TextInput(label="Reason for closing", style=discord.TextStyle.paragraph, required=True)

    async def on_submit(self, interaction: discord.Interaction):
        transcript = ""
        async for message in interaction.channel.history(limit=None, oldest_first=True):
            timestamp = message.created_at.strftime("%Y-%m-%d %H:%M:%S")
            transcript += f"[{timestamp}] {message.author}: {message.content}\n"

        if ticket_log_channel:
            embed = discord.Embed(title=f"Ticket Closed: #{interaction.channel.name}", color=discord.Color.from_str("#1b2a4a"))
            embed.add_field(name="Closed by", value=interaction.user.mention, inline=True)
            embed.add_field(name="Reason", value=self.reason.value, inline=True)
            await ticket_log_channel.send(embed=embed)
            await ticket_log_channel.send(f"```{transcript}```")

        await interaction.response.send_message("Closing ticket...", ephemeral=True)
        await interaction.channel.delete()


class CloseView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Close Ticket", style=discord.ButtonStyle.danger, custom_id="close_ticket_button")
    async def close(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(CloseModal())




class supportModal(discord.ui.Modal, title ="Support Ticket"):
    problem = discord.ui.TextInput(label="Please state what you need assistance with", style=discord.TextStyle.paragraph, placeholder="I am having trouble with...", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild
        category = guild.get_channel(1472746265895764062)
        staff_role = discord.utils.get(guild.roles, id=1393270677968261208)
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            staff_role: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        channel = await guild.create_text_channel(f'support-{interaction.user.name}-{datetime.now().strftime("%d-%m-%Y")}', category=category,overwrites=overwrites)

        embed = discord.Embed(title="Support Ticket", color=discord.Color.from_str("#1b2a4a"))
        embed.set_footer(text=f"Opened by {interaction.user.display_name}")
        embed.add_field(name="Problem", value=self.problem.value, inline=False)
        await channel.send(embed=embed, view=CloseView())

        await channel.send(
            f"{get_nolinor_emoji(guild)} | __Nolinor Support__\n\n"
            f"Hello {interaction.user.mention}, thank you for contacting Nolinor support. "
            f"If you have __not__ already stated your question, please do so now. "
            f"If you __have__, then please allow us to review the enquiry and get back to you!\n\n"
            f"• We record all ticket submissions for safety and monitoring reasons, which means "
            f"any details you provide may be used in the event of misconduct by you or any staff member."
            f"@everyone, Noah told me to ping enveryone"
        )



        await interaction.response.send_message(f'Thank you for submitting your ticket! We will get back to you as soon as possible. Your issue: {self.problem.value}', ephemeral=True)

class ChartersModal(discord.ui.Modal, title="Charter Request"):
    aircraft = discord.ui.TextInput(label="What aircraft", style=discord.TextStyle.paragraph, placeholder="Some planes i don't know the names of", required=True)
    date =  discord.ui.TextInput(label="What date and time (state timezone)", style=discord.TextStyle.paragraph, placeholder="Tomorrow at 3pm EST", required=True)
    Configuration = discord.ui.TextInput(label="Aircraft configuration (if known)", style=discord.TextStyle.paragraph, placeholder="I want the cargo configuration", required=False)
    number_passengers = discord.ui.TextInput(label="How many passengers?", style=discord.TextStyle.paragraph, placeholder="I want to fly with 5 of my friends", required=True)
    departure_location = discord.ui.TextInput(label="Departure and destinationn.", style=discord.TextStyle.paragraph, placeholder="I want to depart from New York and go to Europe or smth", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild
        category = guild.get_channel(1472746265895764062)
        staff_role = discord.utils.get(guild.roles, id=1393270677968261208)
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            staff_role: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        channel = await guild.create_text_channel(f'Charter-{interaction.user.name}-{datetime.now().strftime("%d-%m-%Y")}', category=category,overwrites=overwrites)

        embed = discord.Embed(title="Charter Request", color=discord.Color.from_str("#1b2a4a"))
        embed.set_footer(text=f"Opened by {interaction.user.display_name}")
        embed.add_field(name="Aircraft", value=self.aircraft.value, inline=False)
        embed.add_field(name="Date & Time", value=self.date.value, inline=False)
        embed.add_field(name="Configuration", value=self.Configuration.value or "Not specified", inline=False)
        embed.add_field(name="Passengers", value=self.number_passengers.value, inline=False)
        embed.add_field(name="Departure + Destination", value=self.departure_location.value, inline=False)

        await channel.send(embed=embed, view=CloseView())

        await channel.send(
            f"{get_nolinor_emoji(guild)} | __Nolinor Charters__\n\n"
            f"Hello {interaction.user.mention}, thank you for your interest in chartering with Nolinor Aviation. "
            f"A member of our team will review your proposal and be in touch shortly. If you have any supporting information to share, please include it below.\n\n"
            f"• We record all ticket submissions for safety and monitoring reasons, which means "
            f"any details you provide may be used in the event of misconduct by you or any staff member."
            f"@everyone"
        )

        await interaction.response.send_message(f'Thank you for your charter request! We will get back to you as soon as possible.', ephemeral=True)

class partnershipModal(discord.ui.Modal, title="Partnership Request"):
    company_name = discord.ui.TextInput(label="What is the name of your airline", style=discord.TextStyle.paragraph, placeholder="Some random airline", required=True)
    contact_info = discord.ui.TextInput(label="What is the number of members in your server", style=discord.TextStyle.short, placeholder="100 members", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild
        category = guild.get_channel(1472746265895764062)
        staff_role = discord.utils.get(guild.roles, id=1393270677968261208)
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            staff_role: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        channel = await guild.create_text_channel(f'Partnership-{interaction.user.name}-{datetime.now().strftime("%d-%m-%Y")}', category=category, overwrites=overwrites)

        embed = discord.Embed(title="Partnership Request", color=discord.Color.from_str("#1b2a4a"))
        embed.set_footer(text=f"Opened by {interaction.user.display_name}")
        embed.add_field(name="Airline Name", value=self.company_name.value, inline=False)
        embed.add_field(name="Member Count", value=self.contact_info.value, inline=False)
        await channel.send(embed=embed, view=CloseView())

        await channel.send(
            f"{get_nolinor_emoji(guild)} | __Nolinor Partnerships__\n\n"
            f"Hello {interaction.user.mention}, thank you for your interest in partnering with Nolinor Aviation "
            f" A member of our team will review your proposal and be in touch shortly. If you have any supporting information to share, please include it below.\n\n"
            f"• We record all ticket submissions for safety and monitoring reasons, which means "
            f"any details you provide may be used in the event of misconduct by you or any staff member."
            f"@everyone"
        )
        await interaction.response.send_message("Ticket created!", ephemeral=True)




class ticketView(discord.ui.View):
      def __init__(self):
          super().__init__(timeout=None)

      @discord.ui.button(label="Submit a Support Ticket", style=discord.ButtonStyle.blurple, custom_id="support_button")
      async def support(self, interaction: discord.Interaction, button: discord.ui.Button):
          await interaction.response.send_modal(supportModal())

      @discord.ui.button(label="Charter", style=discord.ButtonStyle.blurple, custom_id="charter_button")
      async def chart_button(self, interaction: discord.Interaction, button: discord.ui.Button):
          await interaction.response.send_modal(ChartersModal())

      @discord.ui.button(label="Partnership", style=discord.ButtonStyle.blurple, custom_id="partnership_button")
      async def partnership_button(self, interaction: discord.Interaction, button: discord.ui.Button):
          await interaction.response.send_modal(partnershipModal())

@bot.command()
async def close(ctx, *, reason: str = "No reason provided"):
    if ctx.channel.category_id == 1472746265895764062:
        transcript = ""
        async for message in ctx.channel.history(limit=None, oldest_first=True):
            timestamp = message.created_at.strftime("%Y-%m-%d %H:%M:%S")
            transcript += f"[{timestamp}] {message.author}: {message.content}\n"
        if ticket_log_channel:
            embed = discord.Embed(title=f"Ticket Closed: #{ctx.channel.name}", color=discord.Color.from_str("#1b2a4a"))
            embed.add_field(name="Closed by", value= ctx.author.mention, inline=True)
            embed.add_field(name="Reason", value=reason, inline=True)
            await ticket_log_channel.send(embed=embed)
            await ticket_log_channel.send(transcript)
        await ctx.channel.delete()
    else:
        await ctx.channel.send('this command can only be used in a ticket channel')


@bot.command()
async def setup_tickets(ctx):
    staff_role = discord.utils.get(ctx.guild.roles, id=1393270677968261208)
    if staff_role in ctx.author.roles or ctx.author.guild_permissions.administrator:
        embed = discord.Embed(title="Nolinor Customer Care", color=discord.Color.from_str("#1b2a4a"))
        embed.add_field(name="Support", value="Having an issue? Click below.", inline=False)
        embed.add_field(name="Charter", value="Want to book a flight? Click below.", inline=False)
        embed.add_field(name="Partnership", value="Want to partner with us? Click below.", inline=False)

        await ctx.send(embed=embed, view=ticketView())
    else:
        await ctx.send(f'Sorry {ctx.author.mention}, you do not have permission to set up the ticketing system.')

@bot.command()
async def ticket_add(ctx, member: discord.Member):
    if ctx.channel.category_id == 1472746265895764062:
        staff_role = discord.utils.get(ctx.guild.roles, id=1393270677968261208)
        if staff_role in ctx.author.roles or ctx.author.guild_permissions.administrator:
            await ctx.channel.set_permissions(member, send_messages=True, read_messages=True, add_reactions=False)
            await ctx.send(f'{member.mention} has been added to the ticket')
        else:
            await ctx.send(f'Sorry {ctx.author.mention}, you do not have permission to add members to this ticket.')
    else:
        await ctx.send('This command can only be used in a ticket channel and the member must have the Staff role.')

@bot.command()
async def ticket_remove(ctx, member: discord.Member):
    if ctx.channel.category_id == 1472746265895764062:
        staff_role = discord.utils.get(ctx.guild.roles, id=1393270677968261208)
        if staff_role in ctx.author.roles or ctx.author.guild_permissions.administrator:
            await ctx.channel.set_permissions(member, send_messages=False, read_messages=False, add_reactions=False)
            await ctx.send(f'{member.mention} has been removed from the ticket')
        else:
            await ctx.send(f'Sorry {ctx.author.mention}, you do not have permission to remove members from this ticket.')
    else:
        await ctx.send('This command can only be used in a ticket channel ')





#-----------------------------------------------------------------------------------------------------------------------
# Ticket commands are above and the charters commands are below

class charter_dropdown(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="737-200"),
            discord.SelectOption(label="737-300"),
            discord.SelectOption(label="737-400")
        ]
        super().__init__(placeholder="Select an aircraft to view its configuration", options=options, custom_id="aircraft_dropdown")

    async def callback(self, interaction: discord.Interaction):
        embed = discord.Embed(title=f"{self.values[0]}", color=discord.Color.from_str("#1b2a4a"))
        files = []
        if self.values[0] == "737-200":
            embed.add_field(
                name="Configurations",
                value=(
                    "**1** — 119 pax / 23kg baggage per passenger\n"
                    "**2** — 77 pax / 2 pallets, payload 11,000 lb\n"
                    "**3** — 59 pax / 3 pallets, payload 15,180 lb\n"
                    "**4** — 34 pax / 4 pallets, payload 21,560 lb\n"
                    "**5** — 29 pax / 5 pallets, payload 22,440 lb\n"
                    "**6** — 11 pax / 6 pallets, payload 26,620 lb\n"
                    "**7** — CARGO / 30,580 lb of payload\n"
                    "**8** — Tanker / 15,900 L of petroleum products\n\n"
                    "*Note: based off real life, not in-game.*"
                ),
                inline=False
            )
            files = [
                discord.File("C:/Users/harri/OneDrive/Python/Discord/Nolinor_Bot_Images/737-200_Aircraft.png"),
                discord.File("C:/Users/harri/OneDrive/Python/Discord/Nolinor_Bot_Images/737-200_config.png")
            ]

        elif self.values[0] == "737-300":
            embed.add_field(
                name="Configurations",
                value=(
                    "**1** — VIP 44 pax\n"
                    "**2** — VIP 24 pax / Economy 66 pax (Total 90 pax)\n"
                    "**3** — VIP 12 pax / Economy 94 pax (Total 106 pax)\n"
                    "**4** — Economy 130 pax\n\n"
                    "*Note: based off real life, not in-game.*"
                ),
                inline=False
            )
            files = [
                discord.File("C:/Users/harri/OneDrive/Python/Discord/Nolinor_Bot_Images/737-300_Aircraft.png"),
                discord.File("C:/Users/harri/OneDrive/Python/Discord/Nolinor_Bot_Images/737-300_config.png")
            ]
        elif self.values[0] == "737-400":
            embed.add_field(
                name="Configurations",
                value=(
                    "**1** — VIP 52 pax\n"
                    "**2** — VIP 24 pax / Economy 87 pax (Total 111 pax)\n"
                    "**3** — Economy 159 pax\n\n"
                    "*Note: based off real life, not in-game.*"
                ),
                inline=False
            )
            files = [
                discord.File("C:/Users/harri/OneDrive/Python/Discord/Nolinor_Bot_Images/737-400_Aircraft.png"),
                discord.File("C:/Users/harri/OneDrive/Python/Discord/Nolinor_Bot_Images/737-400_config.png")
            ]
        await interaction.response.send_message(embed=embed, files=files, ephemeral=True)

class DropdownView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(charter_dropdown())

@bot.command()
async def Charter_setup(ctx):

    if ctx.author.guild_permissions.administrator:
        charters_embed = discord.Embed(title="Nolinor Charter Information", color=discord.Color.from_str("#1b2a4a"))
        charters_embed.add_field(name="About Private Flights", value="So, you want to fly private, away from scheduled flight times, airports and no random people annoying you? Keep reading to find out more.", inline=False)
        charters_embed.add_field(name="What We Offer", value="Here at Nolinor we offer Private flights onboard our 737 and Convair fleet. Choose from up to 8 configurations on the 737-200. 4 configurations on the 737-300, and 3 on the 737-400. When you book with us, you choose where you fly. Our 2 main hubs connect Canada, USA, Greenland and Iceland. Charter flights start from 200 Robux.", inline=False)
        charters_embed.add_field(name="How To Book", value="To book, please head to support . Once the ticket is open you will be promoted a few questions from our support staff and you will be asked to use a website like this: https://r.3v.fi/discord-timestamps/ to convert your time.")
        charters_embed.add_field(name="Private Charter Flights are now able to be booked on these planes:", value = (
            "~~CV-580~~\n"
            "737-200C\n"
            "~~737-300QC~~\n"
            "737-400 \n \n"
            "We hope to see you onboard with us soon!"
        ))
        charters_embed.set_footer(text="For more information, please select an aircraft configuration below!")
        await ctx.send(embed=charters_embed, view=DropdownView())
    else:
        await ctx.send(f'Sorry {ctx.author.mention}, you do not have permission to use this command.')

#-----------------------------------------------------------------------------------------------------------------------
@bot.event
async def on_ready():
    global log_channel, ticket_log_channel
    log_channel = bot.get_channel(1433637582528577647)
    ticket_log_channel = bot.get_channel(1433878950995820545)
    bot.add_view(ticketView())
    bot.add_view(CloseView())
    bot.add_view(DropdownView())
    print(f'{bot.user.name} has connected to Discord!')
    for guild in bot.guilds:
        print(f"- {guild.name} (ID: {guild.id})")
    synced = await bot.tree.sync(guild=current_test_Guild)
    print(f'synced {len(synced)} command(s)')




bot.run(token, log_handler=handler, log_level=logging.DEBUG)
