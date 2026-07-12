import asyncio
import io
import logging
import os
import sys
from datetime import datetime, timedelta
import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv
from keep_alive import keep_alive

load_dotenv()
token = os.getenv("NOLINOR_TOKEN")
if not token:
    raise SystemExit("NOLINOR_TOKEN is not set. Check your .env / environment configuration.")

# --- IDs -------------------------------------------------------------------
TEST_GUILD_ID = 1393270677850689606
STAFF_ROLE_ID = 1393270677968261208
MANAGEMENT_ROLE_ID = 1393270677968261209
FIRE_CUTOFF_ROLE_ID = 1480717428043284602
OWNER_USER_ID = 1371974280707047454
LOG_CHANNEL_ID = 1433637582528577647
TICKET_LOG_CHANNEL_ID = 1433878950995820545
TICKET_CATEGORY_ID = 1472746265895764062

current_test_Guild = discord.Object(id=TEST_GUILD_ID)

# --- Logging -----------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(filename="discord_nolinor.log", encoding="utf-8", mode="a"),
    ],
)
logger = logging.getLogger("nolinor_bot")

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

log_channel = None
ticket_log_channel = None
_ready_once = False


def img(filename):
    return os.path.join(SCRIPT_DIR, "Nolinor_Bot_Images", filename)


def safe_file(filename):
    path = img(filename)
    return discord.File(path) if os.path.exists(path) else None


def get_nolinor_emoji(guild):
    return discord.utils.get(guild.emojis, name="nolinor_holo") or ""


def is_staff(member: discord.Member) -> bool:
    if member.guild_permissions.administrator:
        return True
    role = member.guild.get_role(STAFF_ROLE_ID)
    return role is not None and role in member.roles


def can_moderate(actor: discord.Member, target: discord.Member) -> bool:
    """Can `actor` take a moderation action on `target`?"""
    if target.id == target.guild.owner_id:
        return False
    if actor.id == actor.guild.owner_id:
        return True
    return actor.top_role > target.top_role


def bot_can_moderate(guild: discord.Guild, target: discord.Member) -> bool:
    return guild.me.top_role > target.top_role


# -----------------------------------------------------------------------------
# Global error handlers
# -----------------------------------------------------------------------------

@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    command_name = interaction.command.name if interaction.command else "unknown"
    logger.exception("App command error in /%s", command_name, exc_info=error)

    message = "Something went wrong while running that command."
    if isinstance(error, app_commands.MissingPermissions):
        message = "You don't have permission to do that."
    elif isinstance(error, app_commands.CommandOnCooldown):
        message = f"That command is on cooldown, try again in {error.retry_after:.1f}s."

    try:
        if interaction.response.is_done():
            await interaction.followup.send(message, ephemeral=True)
        else:
            await interaction.response.send_message(message, ephemeral=True)
    except discord.HTTPException:
        pass


@bot.event
async def on_command_error(ctx: commands.Context, error: commands.CommandError):
    if isinstance(error, commands.CommandNotFound):
        return
    if isinstance(error, (commands.MissingRequiredArgument, commands.BadArgument)):
        await ctx.send("Missing or invalid argument for that command.")
        return
    logger.exception("Prefix command error in %s", ctx.command, exc_info=error)
    await ctx.send("Something went wrong running that command.")


# -----------------------------------------------------------------------------
# Moderation commands
# -----------------------------------------------------------------------------

@bot.tree.command(name="kick", description="Kick a member from the server", guild=current_test_Guild)
async def kick(interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
    if not is_staff(interaction.user):
        await interaction.response.send_message(f'Sorry {interaction.user.mention}, you do not have permission to do this.', ephemeral=True)
        return

    if not can_moderate(interaction.user, member):
        await interaction.response.send_message("You can't moderate someone with an equal or higher role than you.", ephemeral=True)
        return

    if not bot_can_moderate(interaction.guild, member):
        await interaction.response.send_message("I can't moderate that member — their role is higher than mine.", ephemeral=True)
        return

    try:
        await member.kick(reason=reason)
    except discord.Forbidden:
        await interaction.response.send_message("I don't have permission to kick that member.", ephemeral=True)
        return
    except discord.HTTPException as e:
        logger.exception("Failed to kick member", exc_info=e)
        await interaction.response.send_message("Something went wrong trying to kick that member.", ephemeral=True)
        return

    await interaction.response.send_message(f'{member.mention} has been kicked from the server.')
    if log_channel:
        await log_channel.send(f'{member.mention} was kicked by {interaction.user.mention} for reason: {reason}')


@bot.tree.command(name="timeout", description="Timeout a member from the server", guild=current_test_Guild)
async def timeout(interaction: discord.Interaction, member: discord.Member, days: int = 0, hours: int = 0,
                   minutes: int = 0, reason: str = "No reason provided"):
    if not is_staff(interaction.user):
        await interaction.response.send_message(f'Sorry {interaction.user.mention}, you do not have permission to do this.', ephemeral=True)
        return

    if not can_moderate(interaction.user, member):
        await interaction.response.send_message("You can't moderate someone with an equal or higher role than you.", ephemeral=True)
        return

    duration = timedelta(days=days, hours=hours, minutes=minutes)
    if duration.total_seconds() <= 0:
        await interaction.response.send_message("Please provide a duration greater than zero.", ephemeral=True)
        return
    if duration > timedelta(days=28):
        await interaction.response.send_message("Timeout duration can't exceed 28 days.", ephemeral=True)
        return

    try:
        await member.timeout(duration, reason=reason)
    except discord.Forbidden:
        await interaction.response.send_message("I don't have permission to timeout that member.", ephemeral=True)
        return
    except discord.HTTPException as e:
        logger.exception("Failed to timeout member", exc_info=e)
        await interaction.response.send_message("Something went wrong trying to timeout that member.", ephemeral=True)
        return

    await interaction.response.send_message(
        f'{member.mention} has been timed out for {days} days, {hours} hours, {minutes} minutes.')
    if log_channel:
        await log_channel.send(f'{member.mention} was timed out by {interaction.user.mention} for reason: {reason}')


@bot.tree.command(name="ban", description="Ban a member from the server", guild=current_test_Guild)
async def ban(interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
    if not is_staff(interaction.user):
        await interaction.response.send_message(f'Sorry {interaction.user.mention}, you do not have permission to do this.', ephemeral=True)
        return

    if not can_moderate(interaction.user, member):
        await interaction.response.send_message("You can't moderate someone with an equal or higher role than you.", ephemeral=True)
        return

    if not bot_can_moderate(interaction.guild, member):
        await interaction.response.send_message("I can't moderate that member — their role is higher than mine.", ephemeral=True)
        return

    try:
        await member.ban(reason=reason)
    except discord.Forbidden:
        await interaction.response.send_message("I don't have permission to ban that member.", ephemeral=True)
        return
    except discord.HTTPException as e:
        logger.exception("Failed to ban member", exc_info=e)
        await interaction.response.send_message("Something went wrong trying to ban that member.", ephemeral=True)
        return

    await interaction.response.send_message(f'{member.mention} has been banned from the server.')
    if log_channel:
        await log_channel.send(f'{member.mention} was banned by {interaction.user.mention} for reason: {reason}')


@bot.tree.command(name="unban", description="Unban a member from the server", guild=current_test_Guild)
@app_commands.describe(user_id="The ID of the user to unban")
async def unban(interaction: discord.Interaction, user_id: str, reason: str = "No reason provided"):
    if not is_staff(interaction.user):
        await interaction.response.send_message(f'Sorry {interaction.user.mention}, you do not have permission to do this.', ephemeral=True)
        return

    try:
        user = await bot.fetch_user(int(user_id))
        await interaction.guild.unban(user, reason=reason)
        await interaction.response.send_message(f'{user.mention} has been unbanned from the server.')

        if log_channel:
            await log_channel.send(f'{user.mention} was unbanned by {interaction.user.mention} for reason: {reason}')
    except (ValueError, discord.NotFound):
        await interaction.response.send_message('User not found. Please provide a valid user ID.', ephemeral=True)
    except discord.Forbidden:
        await interaction.response.send_message('I do not have permission to unban this user.', ephemeral=True)


@bot.tree.command(name="activity_check", description="Ping everyone for an activity check", guild=current_test_Guild)
async def activity_check(interaction: discord.Interaction):
    if not is_staff(interaction.user):
        await interaction.response.send_message(f'Sorry {interaction.user.mention}, you do not have permission to do this.', ephemeral=True)
        return
    await interaction.response.defer(ephemeral=True)
    message = await interaction.channel.send('@everyone Please react with:✅ for the activity check below!')
    await message.add_reaction('✅')

    reactors = []

    def check(reaction, user):
        return reaction.message.id == message.id and str(reaction.emoji) == '✅' and not user.bot and user not in reactors

    try:
        while len(reactors) < 3:
            reaction, user = await bot.wait_for('reaction_add', check=check, timeout=300)
            reactors.append(user)
    except asyncio.TimeoutError:
        pass

    if reactors:
        positions = ["1st", "2nd", "3rd"]
        result = "\n".join(f"{positions[i]}: {user.mention}" for i, user in enumerate(reactors))
        await interaction.channel.send(result)
    else:
        await interaction.channel.send("No one reacted in time.")

    await interaction.followup.send("Activity check complete!", ephemeral=True)


@bot.command()
async def purge(ctx, number: int):
    if not is_staff(ctx.author):
        await ctx.send(f'Sorry {ctx.author.mention}, you do not have permission to purge messages in this ticket.')
        return
    try:
        deleted = await ctx.channel.purge(limit=number)
        await ctx.send(f'{len(deleted)} messages have been deleted.', delete_after=5)
    except discord.Forbidden:
        await ctx.send("I don't have permission to delete messages here.", delete_after=5)
    except discord.HTTPException as e:
        logger.exception("Failed to purge messages", exc_info=e)
        await ctx.send("Couldn't delete those messages (they may be older than 14 days).", delete_after=5)


@bot.command()
async def purge_all(ctx):
    if not is_staff(ctx.author):
        await ctx.send(f'Sorry {ctx.author.mention}, you do not have permission to purge messages in this ticket.')
        return
    try:
        await ctx.channel.purge(limit=None)
        await ctx.send('All messages have been deleted.', delete_after=15)
    except discord.Forbidden:
        await ctx.send("I don't have permission to delete messages here.", delete_after=5)
    except discord.HTTPException as e:
        logger.exception("Failed to purge all messages", exc_info=e)
        await ctx.send("Couldn't delete some messages (they may be older than 14 days).", delete_after=5)


@bot.tree.command(name="ping", description="Check if the bot is responsive", guild=current_test_Guild)
async def ping(interaction: discord.Interaction):
    latency = round(bot.latency * 1000)
    await interaction.response.send_message(f"Pong! Latency: {latency}ms")


@bot.tree.command(name="about_nolinor", description="Learn about Nolinor Aviation", guild=current_test_Guild)
async def about_nolinor(interaction: discord.Interaction):
    embed = discord.Embed(title=f" {get_nolinor_emoji(interaction.guild)} | Nolinor Aviation", color=discord.Color.from_str("#1b2a4a"))
    embed.add_field(name="Who we are", value="Nolinor Aviation is a Canadian airline that specializes in charter services, cargo transport, and passenger flights to remote destinations. We have been in operation since 1992 and are known for our exceptional service, safety record and awesome old planes!", inline=False)
    embed.add_field(name="Our fleet", value="We operate a diverse fleet of aircraft, including the Boeing 737-200, Boeing 737-300, and the 737-400. Our fleet allows us to interchange between cargo and passenger services as well as a mix of both. We also serve a wide range of destinations and meet the unique needs of our customers.", inline=False)
    embed.add_field(name="Our services", value="We offer a variety of services, including charter flights for individuals and groups, cargo transport for businesses, and passenger flights to remote locations. Our team of experienced pilots and staff are dedicated to providing a safe and comfortable travel experience for all of our customers.", inline=False)
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="get_code", description="Get the code for this bot", guild=current_test_Guild)
async def get_code(interaction: discord.Interaction):
    await interaction.response.send_message("This bot is open source! You can find the code on GitHub: https://github.com/Harry-gamer-pro/Some-cool-discord-bots", ephemeral=True)


@bot.tree.command(name="fire", description="Fire a staff member and remove their roles", guild=current_test_Guild)
async def fire(interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
    cut_off_role = interaction.guild.get_role(FIRE_CUTOFF_ROLE_ID)
    has_permission = (
        interaction.user.guild_permissions.administrator or
        discord.utils.get(interaction.user.roles, id=MANAGEMENT_ROLE_ID) or
        interaction.user.id == OWNER_USER_ID
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

    if not bot_can_moderate(interaction.guild, member):
        await interaction.response.send_message("I can't remove that member's roles — their top role is higher than mine.", ephemeral=True)
        return

    roles_to_remove = [r for r in member.roles if r.position >= cut_off_role.position]
    try:
        await member.remove_roles(*roles_to_remove, reason=reason)
    except discord.Forbidden:
        await interaction.response.send_message("I don't have permission to remove one or more of those roles.", ephemeral=True)
        return
    except discord.HTTPException as e:
        logger.exception("Failed to remove roles during fire", exc_info=e)
        await interaction.response.send_message("Something went wrong removing their roles.", ephemeral=True)
        return

    await interaction.response.send_message(f'{member.mention} has been fired and their roles have been removed for reason: {reason}', ephemeral=True)
    if log_channel:
        await log_channel.send(f'{member.mention} was fired by {interaction.user.mention} for reason: {reason}')


@bot.command()
async def shutdown(ctx):
    if ctx.author.id == OWNER_USER_ID:
        await ctx.send("Shutting down...")
        await bot.close()
    else:
        await ctx.send("You don't have permission to do this.")


# -----------------------------------------------------------------------------
# Ticketing system
# -----------------------------------------------------------------------------

async def send_transcript(channel, transcript_text, ticket_name):
    """Send transcript as a file to avoid the 2000 char message limit."""
    transcript_file = discord.File(
        io.BytesIO(transcript_text.encode('utf-8')),
        filename=f"transcript-{ticket_name}.txt"
    )
    await channel.send(file=transcript_file)


async def log_ticket_closure(channel, closer, reason):
    try:
        transcript = ""
        async for message in channel.history(limit=None, oldest_first=True):
            timestamp = message.created_at.strftime("%Y-%m-%d %H:%M:%S")
            transcript += f"[{timestamp}] {message.author}: {message.content}\n"

        if ticket_log_channel:
            embed = discord.Embed(title=f"Ticket Closed: #{channel.name}", color=discord.Color.from_str("#1b2a4a"))
            embed.add_field(name="Closed by", value=closer.mention, inline=True)
            embed.add_field(name="Reason", value=reason, inline=True)
            await ticket_log_channel.send(embed=embed)
            await send_transcript(ticket_log_channel, transcript, channel.name)
    except discord.HTTPException as e:
        logger.exception("Error logging ticket transcript", exc_info=e)


class CloseModal(discord.ui.Modal, title="Close Ticket"):
    reason = discord.ui.TextInput(label="Reason for closing", style=discord.TextStyle.paragraph, required=True)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.send_message("Closing ticket...", ephemeral=True)
        await log_ticket_closure(interaction.channel, interaction.user, self.reason.value)
        try:
            await interaction.channel.delete()
        except discord.HTTPException as e:
            logger.exception("Failed to delete ticket channel", exc_info=e)


class CloseView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Close Ticket", style=discord.ButtonStyle.danger, custom_id="close_ticket_button")
    async def close(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(CloseModal())


async def create_ticket_channel(interaction: discord.Interaction, name_prefix: str):
    """Shared ticket-channel creation. Returns the channel, or None (and responds) on failure."""
    guild = interaction.guild
    category = guild.get_channel(TICKET_CATEGORY_ID)
    if category is None:
        await interaction.followup.send("Ticket category is not configured correctly. Please contact an admin.", ephemeral=True)
        return None

    staff_role = guild.get_role(STAFF_ROLE_ID)
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=False),
        interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
    }
    if staff_role:
        overwrites[staff_role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

    channel_name = f'{name_prefix}-{interaction.user.name}-{datetime.now().strftime("%d-%m-%Y")}'
    try:
        return await guild.create_text_channel(channel_name, category=category, overwrites=overwrites)
    except discord.Forbidden:
        await interaction.followup.send("I don't have permission to create ticket channels.", ephemeral=True)
        return None
    except discord.HTTPException as e:
        logger.exception("Failed to create ticket channel", exc_info=e)
        await interaction.followup.send("Something went wrong creating your ticket. Please try again.", ephemeral=True)
        return None


class supportModal(discord.ui.Modal, title="Support Ticket"):
    problem = discord.ui.TextInput(label="Please state what you need assistance with", style=discord.TextStyle.paragraph, placeholder="I am having trouble with...", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        channel = await create_ticket_channel(interaction, "support")
        if channel is None:
            return

        embed = discord.Embed(title="Support Ticket", color=discord.Color.from_str("#1b2a4a"))
        embed.set_footer(text=f"Opened by {interaction.user.display_name}")
        embed.add_field(name="Problem", value=self.problem.value, inline=False)
        await channel.send(embed=embed, view=CloseView())

        await channel.send(
            f"{get_nolinor_emoji(interaction.guild)} | __Nolinor Support__\n\n"
            f"Hello {interaction.user.mention}, thank you for contacting Nolinor support. "
            f"If you have __not__ already stated your question, please do so now. "
            f"If you __have__, then please allow us to review the enquiry and get back to you!\n\n"
            f"• We record all ticket submissions for safety and monitoring reasons, which means "
            f"any details you provide may be used in the event of misconduct by you or any staff member."
        )
        await channel.send("@everyone")

        await interaction.followup.send(f'Thank you for submitting your ticket! We will get back to you as soon as possible. Your issue: {self.problem.value}', ephemeral=True)


class ChartersModal(discord.ui.Modal, title="Charter Request"):
    aircraft = discord.ui.TextInput(label="What aircraft", style=discord.TextStyle.paragraph, placeholder="~~CV-580~~ 737-200C ~~737-300QC~~ 737-400", required=True)
    date = discord.ui.TextInput(label="What date and time (state timezone)", style=discord.TextStyle.paragraph, placeholder="Tomorrow at 3pm EST", required=True)
    Configuration = discord.ui.TextInput(label="Aircraft configuration", style=discord.TextStyle.paragraph, placeholder="Configuraton 1 (If you don't know the configurations please check charter-infomation", required=False)
    number_passengers = discord.ui.TextInput(label="How many passengers?", style=discord.TextStyle.paragraph, placeholder="I want to fly with 5 of my friends", required=True)
    departure_location = discord.ui.TextInput(label="Departure and destination.", style=discord.TextStyle.paragraph, placeholder="Departure and Destination: E.g. Yellowknife - Val d'Or", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        channel = await create_ticket_channel(interaction, "Charter")
        if channel is None:
            return

        embed = discord.Embed(title="Charter Request", color=discord.Color.from_str("#1b2a4a"))
        embed.set_footer(text=f"Opened by {interaction.user.display_name}")
        embed.add_field(name="Aircraft", value=self.aircraft.value, inline=False)
        embed.add_field(name="Date & Time", value=self.date.value, inline=False)
        embed.add_field(name="Configuration", value=self.Configuration.value or "Not specified", inline=False)
        embed.add_field(name="Passengers", value=self.number_passengers.value, inline=False)
        embed.add_field(name="Departure + Destination", value=self.departure_location.value, inline=False)
        await channel.send(embed=embed, view=CloseView())

        await channel.send(
            f"{get_nolinor_emoji(interaction.guild)} | __Nolinor Charters__\n\n"
            f"Hello {interaction.user.mention}, thank you for your interest in chartering with Nolinor Aviation. "
            f"A member of our team will review your proposal and be in touch shortly. If you have any supporting information to share, please include it below.\n\n"
            f"• We record all ticket submissions for safety and monitoring reasons, which means "
            f"any details you provide may be used in the event of misconduct by you or any staff member."
        )
        await channel.send("@everyone")

        await interaction.followup.send('Thank you for your charter request! We will get back to you as soon as possible.', ephemeral=True)


class partnershipModal(discord.ui.Modal, title="Partnership Request"):
    company_name = discord.ui.TextInput(label="What is the name of your airline", style=discord.TextStyle.paragraph, placeholder="Some random airline", required=True)
    contact_info = discord.ui.TextInput(label="What is the number of members in your server", style=discord.TextStyle.short, placeholder="100 members", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        channel = await create_ticket_channel(interaction, "Partnership")
        if channel is None:
            return

        embed = discord.Embed(title="Partnership Request", color=discord.Color.from_str("#1b2a4a"))
        embed.set_footer(text=f"Opened by {interaction.user.display_name}")
        embed.add_field(name="Airline Name", value=self.company_name.value, inline=False)
        embed.add_field(name="Member Count", value=self.contact_info.value, inline=False)
        await channel.send(embed=embed, view=CloseView())

        await channel.send(
            f"{get_nolinor_emoji(interaction.guild)} | __Nolinor Partnerships__\n\n"
            f"Hello {interaction.user.mention}, thank you for your interest in partnering with Nolinor Aviation. "
            f"A member of our team will review your proposal and be in touch shortly. If you have any supporting information to share, please include it below.\n\n"
            f"• We record all ticket submissions for safety and monitoring reasons, which means "
            f"any details you provide may be used in the event of misconduct by you or any staff member."
        )
        await channel.send("@everyone")

        await interaction.followup.send("Ticket created!", ephemeral=True)


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
    if ctx.channel.category_id != TICKET_CATEGORY_ID:
        await ctx.channel.send('This command can only be used in a ticket channel.')
        return
    await log_ticket_closure(ctx.channel, ctx.author, reason)
    try:
        await ctx.channel.delete()
    except discord.HTTPException as e:
        logger.exception("Failed to delete ticket channel", exc_info=e)


@bot.command()
async def setup_tickets(ctx):
    if not is_staff(ctx.author):
        await ctx.send(f'Sorry {ctx.author.mention}, you do not have permission to set up the ticketing system.')
        return
    embed = discord.Embed(title="Nolinor Customer Care", color=discord.Color.from_str("#1b2a4a"))
    embed.add_field(name="Support", value="Having an issue? Click below.", inline=False)
    embed.add_field(name="Charter", value="Want to book a flight? Click below.", inline=False)
    embed.add_field(name="Partnership", value="Want to partner with us? Click below.", inline=False)
    await ctx.send(embed=embed, view=ticketView())


@bot.command()
async def ticket_add(ctx, member: discord.Member):
    if ctx.channel.category_id != TICKET_CATEGORY_ID:
        await ctx.send('This command can only be used in a ticket channel.')
        return
    if not is_staff(ctx.author):
        await ctx.send(f'Sorry {ctx.author.mention}, you do not have permission to add members to this ticket.')
        return
    await ctx.channel.set_permissions(member, send_messages=True, read_messages=True, add_reactions=False)
    await ctx.send(f'{member.mention} has been added to the ticket')


@bot.command()
async def ticket_remove(ctx, member: discord.Member):
    if ctx.channel.category_id != TICKET_CATEGORY_ID:
        await ctx.send('This command can only be used in a ticket channel.')
        return
    if not is_staff(ctx.author):
        await ctx.send(f'Sorry {ctx.author.mention}, you do not have permission to remove members from this ticket.')
        return
    await ctx.channel.set_permissions(member, send_messages=False, read_messages=False, add_reactions=False)
    await ctx.send(f'{member.mention} has been removed from the ticket')


# -----------------------------------------------------------------------------
# Charter configuration dropdown
# -----------------------------------------------------------------------------

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
            embed.set_image(url="attachment://737-200_Aircraft.png")
            files = [safe_file("737-200_Aircraft.png"), safe_file("737-200_config.png")]

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
            files = [safe_file("737-300_Aircraft.png"), safe_file("737-300_config.png")]

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
            files = [safe_file("737-400_Aircraft.png"), safe_file("737-400_config.png")]

        files = [f for f in files if f is not None]
        await interaction.response.send_message(embed=embed, files=files, ephemeral=True)


class DropdownView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(charter_dropdown())


@bot.command()
async def Charter_setup(ctx):
    if not ctx.author.guild_permissions.administrator:
        await ctx.send(f'Sorry {ctx.author.mention}, you do not have permission to use this command.')
        return

    charters_embed = discord.Embed(title="Nolinor Charter Information", color=discord.Color.from_str("#1b2a4a"))
    charters_embed.add_field(name="About Private Flights", value="So, you want to fly private, away from scheduled flight times, airports and no random people annoying you? Keep reading to find out more.", inline=False)
    charters_embed.add_field(name="What We Offer", value="Here at Nolinor we offer Private flights onboard our 737 and Convair fleet. Choose from up to 8 configurations on the 737-200. 4 configurations on the 737-300, and 3 on the 737-400. When you book with us, you choose where you fly. Our 2 main hubs connect Canada, USA, Greenland and Iceland. Charter flights start from 200 Robux.", inline=False)
    charters_embed.add_field(name="How To Book", value="To book, please head to support . Once the ticket is open you will be promoted a few questions from our support staff and you will be asked to use a website like this: https://r.3v.fi/discord-timestamps/ to convert your time.")
    charters_embed.add_field(name="Private Charter Flights are now able to be booked on these planes:", value=(
        "~~CV-580~~\n"
        "737-200C\n"
        "~~737-300QC~~\n"
        "737-400 \n \n"
        "We hope to see you onboard with us soon!"
    ))
    charters_embed.set_footer(text="For more information, please select an aircraft configuration below!")
    await ctx.send(embed=charters_embed, view=DropdownView())


# -----------------------------------------------------------------------------

@bot.event
async def on_ready():
    global log_channel, ticket_log_channel, _ready_once
    log_channel = bot.get_channel(LOG_CHANNEL_ID)
    ticket_log_channel = bot.get_channel(TICKET_LOG_CHANNEL_ID)

    if not _ready_once:
        bot.add_view(ticketView())
        bot.add_view(CloseView())
        bot.add_view(DropdownView())
        try:
            synced = await bot.tree.sync(guild=current_test_Guild)
            logger.info(f'Synced {len(synced)} command(s)')
        except discord.HTTPException as e:
            logger.exception("Failed to sync command tree", exc_info=e)
        _ready_once = True

    logger.info(f'{bot.user.name} has connected to Discord!')
    for guild in bot.guilds:
        logger.info(f"- {guild.name} (ID: {guild.id})")

keep_alive()
bot.run(token, log_handler=None)
