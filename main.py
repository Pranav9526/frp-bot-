import discord
from discord.ext import commands
from discord import app_commands
from discord import ui, Interaction, TextStyle, Embed, Color
import os
from keep_alive import keep_alive
import datetime
import re

# === CONFIG ===
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GUILD_ID = 1169251155721846855  # Replace with your server ID
PROOF_CHANNEL_ID = 1393423615432720545  # Channel where proofs will be sent
ALLOWED_ROLE_ID = 1346488365608079452  # Role allowed to use forwardproof
SAY_ROLE_ID = 1346488355486961694  # Role allowed to use say commands
ADMIN_LOG_ROLE_ID = 1346488363053482037 # Role allowed to use log commands
TICKET_CHANNEL_PREFIX = "ticket-"

BAN_LOG_CHANNEL_ID = 1346488664917671946
JAIL_LOG_CHANNEL_ID = 1382895763717226516
FC_LOG_CHANNEL_ID = 1377862821924044860
MENTION_ROLE_ID = 1346488379734491196

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Remove default help command to avoid conflict
bot.remove_command("help")

@bot.event
async def on_ready():
    try:
        await bot.tree.sync()  # Global sync
        print("✅ Globally synced all slash commands.")
    except Exception as e:
        print(f"Error syncing slash commands: {e}")

#----------Date TIme Handler ----------
def format_datetime(dt: datetime.datetime):
    return dt.strftime("%Y-%m-%d %H:%M:%S")

# -------- Shared Forwardproof Handler --------
async def handle_forward_proof(ctx, reporter, accused, replied_msg):
    is_interaction = isinstance(ctx, discord.Interaction)

    if not replied_msg:
        msg = "❌ Please reply to the message containing the proof."
        return await ctx.response.send_message(msg, ephemeral=True) if is_interaction else await ctx.send(msg)

    if not replied_msg.attachments:
        msg = "❌ No attachments found in the replied message."
        return await ctx.response.send_message(msg, ephemeral=True) if is_interaction else await ctx.send(msg)

    if not replied_msg.channel.name.startswith(TICKET_CHANNEL_PREFIX):
        msg = "❌ This command can only be used in ticket channels."
        return await ctx.response.send_message(msg, ephemeral=True) if is_interaction else await ctx.send(msg)

    attachments = replied_msg.attachments
    image_preview = None
    files = []

    for i, attachment in enumerate(attachments):
        file = await attachment.to_file()
        if i == 0 and attachment.content_type.startswith("image"):
            image_preview = attachment.url
            files.append(file)
        else:
            files.append(file)

    embed = discord.Embed(
        title="FRP Report",
        color=discord.Color.red(),
        timestamp=datetime.datetime.utcnow()
    )
    embed.add_field(name="Reporter", value=reporter, inline=True)
    embed.add_field(name="Accused", value=accused, inline=True)
    embed.add_field(name="Message", value=replied_msg.content or "(No text provided)", inline=False)
    embed.add_field(
    name="Handled By",
    value=(ctx.user.mention if is_interaction else ctx.author.mention),
    inline=False
    )
    embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/1372059707694645360/1393578650015760516/491878536_605875318625766_7662976636025833179_n.png")

    if image_preview:
        embed.set_image(url=image_preview)

    try:
        channel = bot.get_channel(PROOF_CHANNEL_ID)
        await channel.send(embed=embed, files=files)
        success_msg = "✅ Proof forwarded successfully!"
        await ctx.response.send_message(success_msg, ephemeral=True) if is_interaction else await ctx.send(success_msg)
    except Exception as e:
        err_msg = f"❌ Failed to forward proof.\nError: `{e}`"
        await ctx.response.send_message(err_msg, ephemeral=True) if is_interaction else await ctx.send(err_msg)


# --------- Emoji Say Handler ---------
def resolve_emojis(message: discord.Message) -> str:
    content = message.content

    # Match <a:name:id> or <:name:id>
    custom_emoji_pattern = r'<a?:\w+:\d+>'
    matches = re.findall(custom_emoji_pattern, content)

    for match in matches:
        content = content.replace(match, match)  # Leave it as-is so it renders in embed

    return content

# -------- Shared Say Handler --------
async def handle_say(ctx, title, channel, replied_msg):
    is_interaction = isinstance(ctx, discord.Interaction)

    if not replied_msg:
        msg = "❌ Please reply to a message to use this command."
        return await ctx.response.send_message(msg, ephemeral=True) if is_interaction else await ctx.send(msg)

    embed = discord.Embed(
        title=title,
        description=resolve_emojis(replied_msg) or "(No content provided)",
        color=discord.Color.from_rgb(0, 255, 255)
    )
    embed.set_footer(text="UNDERCITY ROLEPLAY")
    embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/1372059707694645360/1393578650015760516/491878536_605875318625766_7662976636025833179_n.png")

    try:
        await channel.send(embed=embed)
        success_msg = f"✅ Embed sent to {channel.mention}"
        await ctx.response.send_message(success_msg, ephemeral=True) if is_interaction else await ctx.send(success_msg)
    except Exception as e:
        err_msg = f"❌ Failed to send embed.\nError: `{e}`"
        await ctx.response.send_message(err_msg, ephemeral=True) if is_interaction else await ctx.send(err_msg)


# -------- Prefix Commands --------
@bot.command()
@commands.has_role(ALLOWED_ROLE_ID)
async def forwardproof(ctx, reporter: str = None, accused: str = None):
    if not reporter or not accused:
        return await ctx.send("❌ Usage: `!forwardproof <reporter> <accused>` (reply to the proof message)")

    if ctx.message.reference:
        replied_msg = await ctx.channel.fetch_message(ctx.message.reference.message_id)
        await handle_forward_proof(ctx, reporter, accused, replied_msg)
    else:
        await ctx.send("❌ Please reply to the proof message.")

@bot.command()
async def userinfo(ctx, member: discord.Member = None):
    member = member or ctx.author

    embed = discord.Embed(
        title=f"User Info – {member}",
        color=discord.Color.blue(),
        timestamp=datetime.datetime.utcnow()
    )
    embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
    embed.add_field(name="👤 Username", value=member.mention, inline=True)
    embed.add_field(name="🆔 User ID", value=member.id, inline=True)
    embed.add_field(name="🎖 Top Role", value=member.top_role.mention, inline=True)
    embed.add_field(name="🤖 Bot?", value="Yes" if member.bot else "No", inline=True)
    embed.add_field(name="📆 Account Created", value=format_datetime(member.created_at), inline=False)
    embed.add_field(name="📥 Joined Server", value=format_datetime(member.joined_at), inline=False)

    await ctx.send(embed=embed)


@bot.command()
@commands.has_role(SAY_ROLE_ID)
async def say(ctx, channel: discord.TextChannel = None, *, title: str = None):
    if not title or not channel:
        return await ctx.send("❌ Usage: `!say <#channel> <title>` (reply to a message)")

    if ctx.message.reference:
        replied_msg = await ctx.channel.fetch_message(ctx.message.reference.message_id)
        await handle_say(ctx, title, channel, replied_msg)
    else:
        await ctx.send("❌ Please reply to a message.")

# -------- Log Commands ----------

@bot.command()
@commands.has_role(ADMIN_LOG_ROLE_ID)
async def banlog(ctx, player_name: str = None, ban_days: str = None, unban: str = None, *, reason: str = None):
    if not all([player_name, ban_days, unban, reason]):
        return await ctx.send("❌ Usage: `!banlog <player_name> <ban_days> <unban> <reason>`")

    msg = (
        f"# PLAYER BAN\n\n"
        f"> **`PLAYER NAME: {player_name}`   \n"
        f"> BAN DAYS: {ban_days} \n"
        f"> UNBAN: {unban} \n"
        f"> BANNED BY: {ctx.author.mention}**\n"
        f"> \n"
        f"> **REASON: {reason}**\n"
        f"<@&{MENTION_ROLE_ID}>"
    )

    try:
        channel = bot.get_channel(BAN_LOG_CHANNEL_ID)
        await channel.send(msg)
        await ctx.send("✅ Ban log sent.")
    except Exception as e:
        await ctx.send(f"❌ Failed to send.\n`{str(e)}`")


@bot.command()
@commands.has_role(ADMIN_LOG_ROLE_ID)
async def jaillog(ctx, player_name: str = None, discord_user: discord.Member = None, minutes: str = None, *, reason: str = None):
    if not all([player_name, discord_user, minutes, reason]):
        return await ctx.send("❌ Usage: `!jaillog <player_name> <@user> <minutes> <reason>`")

    msg = (
        f"# PLAYER JAIL\n\n"
        f"> **`PLAYER NAME: {player_name}\n"
        f"> `DISCORD:` {discord_user.mention}  \n"
        f"> \n"
        f"> Was Prisoned For {minutes} Min's by {ctx.author.mention} \n"
        f"> \n"
        f"> Reason: {reason}"
    )

    try:
        channel = bot.get_channel(JAIL_LOG_CHANNEL_ID)
        await channel.send(msg)
        await ctx.send("✅ Jail log sent.")
    except Exception as e:
        await ctx.send(f"❌ Failed to send.\n`{str(e)}`")


@bot.command()
@commands.has_role(ADMIN_LOG_ROLE_ID)
async def fclog(ctx, ign: str = None, reason: str = None, cooldown_end: str = None, discord_user: discord.Member = None):
    if not all([ign, reason, cooldown_end, discord_user]):
        return await ctx.send("❌ Usage: `!fclog <in_game_name> <reason> <cooldown_end_date> <@user>`")

    msg = (
        f"## FACTION COOLDOWN NOTICE\n"
        f"> `In-Game Name: {ign}`\n"
        f"> Reason: ` {reason}`\n"
        f"> Cooldown End: ` {cooldown_end}`\n"
        f"> Player Mention {discord_user.mention} \n"
        f"> **OPEN TICKET AFTER COOLDOWN END**"
    )

    try:
        channel = bot.get_channel(FC_LOG_CHANNEL_ID)
        await channel.send(msg)
        await ctx.send("✅ FC log sent.")
    except Exception as e:
        await ctx.send(f"❌ Failed to send.\n`{str(e)}`")

# -------- force re-sync ---------
@bot.command()
@commands.is_owner()
async def sync(ctx):
    try:
        synced = await bot.tree.sync(guild=discord.Object(id=GUILD_ID))
        await ctx.send(f"✅ Synced {len(synced)} slash commands to this server.")
    except Exception as e:
        await ctx.send(f"❌ Sync failed.\n`{e}`")

# -------- help command ------------
@bot.command(name="help")
async def help_command(ctx):
    embed = discord.Embed(
        title="🤖 UCRP MANAGER – Help Guide",
        description=(
            "**UCRP MANAGER** is the official bot of **UNDERCITY ROLEPLAY (UCRP)**.\n"
            "It helps staff with proof handling, announcements, user tools, and more.\n\n"
            "### 📌 Commands\n"
            "- `/forward-proof` or `!forwardproof`\n"
            "- `/say` or `!say`\n"
            "- `/sayembed`\n"
            "- `/userinfo` or `!userinfo`\n"
            "- `/about` or `!about`\n"
            "- `/help` or `!help`"
        ),
        color=discord.Color.from_rgb(0, 255, 255)
    )
    await ctx.send(embed=embed)


#--------- about command -----------
@bot.command(name="about")
async def about(ctx):
    embed = discord.Embed(
        title="🔷 About UCRP MANAGER",
        description=(
            "**UCRP MANAGER** is the official bot of **UNDERCITY ROLEPLAY**, Kerala’s most immersive and professionally managed SAMP roleplay server.\n\n"
            "Designed exclusively for UCRP staff, this bot empowers the team with advanced tools for:\n"
            "🔹 Ticket proof management\n"
            "🔹 Announcement broadcasting\n"
            "🔹 Ban, jail & faction log automation\n"
            "🔹 User tracking and embed customization\n\n"
            "🎮 **UNDERCITY ROLEPLAY (UCRP)** is not just a server — it's a serious RP experience built for dedicated roleplayers.\n"
            "With active law enforcement, gang/faction systems, realistic economy, and strict RP rules, UCRP offers the **ultimate roleplay journey** in the SAMP world.\n\n"
            "👥 Join UCRP: https://discord.gg/mCgAQcdZFE"
        ),
        color=discord.Color.from_rgb(0, 255, 255)
    )
    await ctx.send(embed=embed)

# -------- Slash Commands --------
@bot.tree.command(name="forward-proof", description="Forward proofs to Ticket-Proofs channel.")
@app_commands.describe(reporter="Name of reporter", accused="Name of accused", message_id="Message ID of the proof")
async def forward_proof_slash(interaction: discord.Interaction, reporter: str, accused: str, message_id: str):
    if not any(role.id == ALLOWED_ROLE_ID for role in interaction.user.roles):
        return await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)

    try:
        replied_msg = await interaction.channel.fetch_message(int(message_id))
        await handle_forward_proof(interaction, reporter, accused, replied_msg)
    except Exception:
        await interaction.response.send_message("❌ Could not fetch the message. Check the message ID.", ephemeral=True)


@bot.tree.command(name="say")
@app_commands.describe(title="Embed title", channel="Channel to send embed", message_id="Message ID to embed")
async def say_slash(interaction: discord.Interaction, title: str, channel: discord.TextChannel, message_id: str):
    if not any(role.id == SAY_ROLE_ID for role in interaction.user.roles):
        return await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)

    try:
        replied_msg = await interaction.channel.fetch_message(int(message_id))
        await handle_say(interaction, title, channel, replied_msg)
    except Exception:
        await interaction.response.send_message("❌ Could not fetch the message. Check the message ID.", ephemeral=True)

# ----------- /sayembed -------------
from discord import app_commands, ui, TextStyle, Interaction, Embed
import discord

# --- Modal to get basic input ---
class EmbedModal(ui.Modal, title="📦 Create Embed"):
    title_input = ui.TextInput(label="Embed Title", style=TextStyle.short, required=True, max_length=256)
    desc_input = ui.TextInput(label="Description", style=TextStyle.paragraph, required=True, max_length=2000)
    footer_input = ui.TextInput(label="Footer (optional)", style=TextStyle.short, required=False)
    thumb_input = ui.TextInput(label="Thumbnail URL (optional)", style=TextStyle.short, required=False)

    def __init__(self, bot, user, target_channel: discord.TextChannel, replied_msg=None):
        super().__init__()
        self.bot = bot
        self.user = user
        self.replied_msg = replied_msg
        self.target_channel = target_channel  # ✅ Store selected channel


    async def on_submit(self, interaction: Interaction):
        if not any(role.id == SAY_ROLE_ID for role in interaction.user.roles):
            await interaction.response.send_message("❌ You don't have permission to use this.", ephemeral=True)
            return

        view = EmbedView(
            self.bot, self.user,
            self.title_input.value,
            self.desc_input.value,
            self.footer_input.value,
            self.thumb_input.value,
            self.replied_msg,
            self.target_channel,  # ✅ pass selected channel here
            interaction
        )
        await interaction.response.send_message("🎨 Choose color below and confirm sending:", view=view, ephemeral=True)


# --- View with dropdowns & button ---
class EmbedView(discord.ui.View):
    def __init__(self, bot, user, title, desc, footer, thumbnail, replied_msg, channel, interaction):
        super().__init__(timeout=180)
        self.bot = bot
        self.user = user
        self.title = title
        self.desc = desc
        self.footer = footer
        self.thumbnail = thumbnail
        self.replied_msg = replied_msg
        self.interaction = interaction
        self.channel = channel  # ✅ use selected channel
        self.embed_color = discord.Color.from_rgb(0, 255, 255)

        self.add_item(ColorDropdown(self))
        self.add_item(discord.ui.Button(label="✅ Send Embed", style=discord.ButtonStyle.success, custom_id="send_embed_button"))


    @ui.button(label="✅ Send Embed", style=discord.ButtonStyle.success)
    async def send_embed_button(self, interaction: Interaction, button: ui.Button):
        if interaction.user.id != self.user.id:
            await interaction.response.send_message("❌ You're not allowed to use this.", ephemeral=True)
            return

        if not self.channel:
            await interaction.response.send_message("❌ Please select a channel first.", ephemeral=True)
            return

        # Create the embed
        embed = Embed(title=self.title, description=self.desc, color=self.embed_color)
        if self.footer:
            embed.set_footer(text=self.footer)
        if self.thumbnail:
            embed.set_thumbnail(url=self.thumbnail)

        await self.channel.send(embed=embed)
        await interaction.response.send_message(f"✅ Embed sent to {self.channel.mention}", ephemeral=True)


# --- Dropdown for color ---
class ColorDropdown(ui.Select):
    def __init__(self, parent_view):
        self.parent_view = parent_view
        options = [
            discord.SelectOption(label="Red", value="red"),
            discord.SelectOption(label="Green", value="green"),
            discord.SelectOption(label="Orange", value="orange"),
            discord.SelectOption(label="Yellow", value="yellow"),
            discord.SelectOption(label="Purple", value="purple"),
            discord.SelectOption(label="Black", value="black"),
            discord.SelectOption(label="White", value="white"),
            discord.SelectOption(label="Cyan", value="cyan")
        ]
        super().__init__(placeholder="🎨 Choose a color", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        color_map = {
            "red": discord.Color.red(),
            "green": discord.Color.green(),
            "orange": discord.Color.orange(),
            "yellow": discord.Color.gold(),
            "purple": discord.Color.purple(),
            "black": discord.Color.darker_grey(),
            "white": discord.Color.lighter_grey(),
            "cyan": discord.Color.from_rgb(0, 255, 255)
        }
        self.parent_view.embed_color = color_map[self.values[0]]
        await interaction.response.send_message(f"✅ Color set to {self.values[0].capitalize()}", ephemeral=True)


# --- Dropdown for channels ---
class ChannelDropdown(ui.Select):
    def __init__(self, parent_view):
        self.parent_view = parent_view
        guild = parent_view.bot.get_guild(GUILD_ID)

        # Max 25 channels
        options = [
            discord.SelectOption(label=ch.name, value=str(ch.id))
            for ch in guild.text_channels
            if ch.permissions_for(guild.me).send_messages
        ][:25]

        super().__init__(placeholder="📨 Choose a channel", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.parent_view.user.id:
            await interaction.response.send_message("❌ You can't use this.", ephemeral=True)
            return

        channel_id = int(self.values[0])
        self.parent_view.channel = self.parent_view.bot.get_channel(channel_id)
        await interaction.response.send_message(f"✅ Channel set to {self.parent_view.channel.mention}", ephemeral=True)


# --- Slash Command ---
@bot.tree.command(name="sayembed", description="Send a styled embed to a selected channel using a UI builder")
@app_commands.describe(channel="The channel where the embed will be sent")
async def sayembed_ui(interaction: discord.Interaction, channel: discord.TextChannel):
    if not any(role.id == SAY_ROLE_ID for role in interaction.user.roles):
        await interaction.response.send_message("❌ You don’t have permission to use this.", ephemeral=True)
        return

    # Store the selected channel inside the interaction context using EmbedModal
    await interaction.response.send_modal(EmbedModal(bot, interaction.user, target_channel=channel))

# ------------- /userinfo -------------

@bot.tree.command(name="userinfo", description="Get information about a user.")
@app_commands.describe(user="Select the user to view info for")
async def userinfo_slash(interaction: discord.Interaction, user: discord.Member = None):
    member = user or interaction.user

    embed = discord.Embed(
        title=f"User Info – {member}",
        color=discord.Color.blue(),
        timestamp=datetime.datetime.utcnow()
    )
    embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
    embed.add_field(name="👤 Username", value=member.mention, inline=True)
    embed.add_field(name="🆔 User ID", value=member.id, inline=True)
    embed.add_field(name="🎖 Top Role", value=member.top_role.mention, inline=True)
    embed.add_field(name="🤖 Bot?", value="Yes" if member.bot else "No", inline=True)
    embed.add_field(name="📆 Account Created", value=format_datetime(member.created_at), inline=False)
    embed.add_field(name="📥 Joined Server", value=format_datetime(member.joined_at), inline=False)

    await interaction.response.send_message(embed=embed)

# ------------/logs -------------
@bot.tree.command(name="banlog", description="Post a player ban log")
@app_commands.describe(
    player_name="Player's in-game name",
    ban_days="Ban duration (Permanent, 3 days, etc.)",
    unban="Unban info (e.g. No Unban, or date)",
    reason="Reason for the ban"
)
async def banlog_slash(interaction: discord.Interaction, player_name: str, ban_days: str, unban: str, reason: str):
    if not any(role.id == ADMIN_LOG_ROLE_ID for role in interaction.user.roles):
        return await interaction.response.send_message("❌ You don’t have permission.", ephemeral=True)

    msg = (
        f"# PLAYER BAN\n\n"
        f"> **`PLAYER NAME: {player_name}`   \n"
        f"> BAN DAYS: {ban_days} \n"
        f"> UNBAN: {unban} \n"
        f"> BANNED BY: {interaction.user.mention}**\n"
        f"> \n"
        f"> **REASON: {reason}**\n"
        f"<@&{MENTION_ROLE_ID}>"
    )

    try:
        channel = bot.get_channel(BAN_LOG_CHANNEL_ID)
        await channel.send(msg)
        await interaction.response.send_message("✅ Ban log sent.", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"❌ Failed to send log.\n`{e}`", ephemeral=True)


@bot.tree.command(name="jaillog", description="Post a player jail log")
@app_commands.describe(
    player_name="Player's in-game name",
    discord_user="Tag the player",
    minutes="Time in minutes",
    reason="Reason for jail"
)
async def jaillog_slash(interaction: discord.Interaction, player_name: str, discord_user: discord.Member, minutes: str, reason: str):
    if not any(role.id == ADMIN_LOG_ROLE_ID for role in interaction.user.roles):
        return await interaction.response.send_message("❌ You don’t have permission.", ephemeral=True)

    msg = (
        f"# PLAYER JAIL\n\n"
        f"> **`PLAYER NAME: {player_name}\n"
        f"> `DISCORD:` {discord_user.mention}  \n"
        f"> \n"
        f"> Was Prisoned For {minutes} Min's by {interaction.user.mention} \n"
        f"> \n"
        f"> Reason: {reason}"
    )

    try:
        channel = bot.get_channel(JAIL_LOG_CHANNEL_ID)
        await channel.send(msg)
        await interaction.response.send_message("✅ Jail log sent.", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"❌ Failed to send log.\n`{e}`", ephemeral=True)


@bot.tree.command(name="fclog", description="Post a faction cooldown notice")
@app_commands.describe(
    ign="In-game name",
    reason="Reason for cooldown",
    cooldown_end="Cooldown end date (e.g. 5/7/2025)",
    discord_user="Tag the player"
)
async def fclog_slash(interaction: discord.Interaction, ign: str, reason: str, cooldown_end: str, discord_user: discord.Member):
    if not any(role.id == ADMIN_LOG_ROLE_ID for role in interaction.user.roles):
        return await interaction.response.send_message("❌ You don’t have permission.", ephemeral=True)

    msg = (
        f"## FACTION COOLDOWN NOTICE\n"
        f"> `In-Game Name: {ign}`\n"
        f"> Reason: ` {reason}`\n"
        f"> Cooldown End: ` {cooldown_end}`\n"
        f"> Player Mention {discord_user.mention} \n"
        f"> **OPEN TICKET AFTER COOLDOWN END**"
    )

    try:
        channel = bot.get_channel(FC_LOG_CHANNEL_ID)
        await channel.send(msg)
        await interaction.response.send_message("✅ FC log sent.", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"❌ Failed to send log.\n`{e}`", ephemeral=True)

# -------- /help command ----------
@bot.tree.command(name="help", description="Show a list of bot commands and their use")
async def help_slash(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🤖 UCRP MANAGER – Help Guide",
        description=(
            "**UCRP MANAGER** is the official bot of **UNDERCITY ROLEPLAY (UCRP)**.\n"
            "It helps staff with proof handling, announcements, user tools, and more.\n\n"
            "### 📌 Commands\n"
            "- `/forward-proof` or `!forwardproof` – Forward proof replies in tickets\n"
            "- `/say` or `!say` – Send embed of a replied message\n"
            "- `/sayembed` – Create custom embeds with title, message & color\n"
            "- `/userinfo` or `!userinfo` – Get user info\n"
            "- `/about` or `!about` – Info about the bot & UCRP\n"
            "- `/help` or `!help` – Show this help message"
        ),
        color=discord.Color.from_rgb(0, 255, 255)
    )
    await interaction.response.send_message(embed=embed)

# -------- /about command ---------
@bot.tree.command(name="about", description="Information about UCRP MANAGER and UNDERCITY ROLEPLAY")
async def about_slash(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🔷 About UCRP MANAGER",
        description=(
            "**UCRP MANAGER** is the official bot of **UNDERCITY ROLEPLAY**, Kerala’s most immersive and professionally managed SAMP roleplay server.\n\n"
            "Designed exclusively for UCRP staff, this bot empowers the team with advanced tools for:\n"
            "🔹 Ticket proof management\n"
            "🔹 Announcement broadcasting\n"
            "🔹 Ban, jail & faction log automation\n"
            "🔹 User tracking and embed customization\n\n"
            "🎮 **UNDERCITY ROLEPLAY (UCRP)** is not just a server — it's a serious RP experience built for dedicated roleplayers.\n"
            "With active law enforcement, gang/faction systems, realistic economy, and strict RP rules, UCRP offers the **ultimate roleplay journey** in the SAMP world.\n\n"
            "👥 Join UCRP: https://discord.gg/mCgAQcdZFE"
        ),
        color=discord.Color.from_rgb(0, 255, 255)
    )
    await interaction.response.send_message(embed=embed)


# -------- Keep Alive & Run --------
keep_alive()
bot.run(TOKEN)
