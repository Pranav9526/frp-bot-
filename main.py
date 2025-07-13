import discord
from discord.ext import commands
from discord import app_commands
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
TICKET_CHANNEL_PREFIX = "ticket-"

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    try:
        guild = discord.Object(id=GUILD_ID)
        await bot.tree.sync(guild=guild)
        print("✅ Bot is ready. Slash commands synced.")
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


@bot.tree.command(name="sayembed", description="Send a styled embed to a channel.")
@app_commands.describe(
    title="Title of the embed",
    description="Description/body of the embed",
    color="Color name like red, blue, green (optional)",
    channel="Channel where the embed should be sent"
)
async def sayembed(
    interaction: discord.Interaction,
    title: str,
    description: str,
    color: str,
    channel: discord.TextChannel
):
    allowed_role_id = 1346488355486961694
    if not any(role.id == allowed_role_id for role in interaction.user.roles):
        return await interaction.response.send_message("❌ You don’t have permission to use this.", ephemeral=True)

    color_map = {
        "red": discord.Color.red(),
        "blue": discord.Color.blue(),
        "green": discord.Color.green(),
        "orange": discord.Color.orange(),
        "yellow": discord.Color.gold(),
        "purple": discord.Color.purple(),
        "black": discord.Color.darker_grey(),
        "white": discord.Color.lighter_grey(),
    }
    embed_color = color_map.get(color.lower(), discord.Color.blue())

    embed = discord.Embed(title=title, description=description, color=embed_color)
    embed.set_footer(text="UNDERCITY ROLEPLAY")
    embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/1372059707694645360/1393578650015760516/491878536_605875318625766_7662976636025833179_n.png")

    try:
        await channel.send(embed=embed)
        await interaction.response.send_message("✅ Embed sent successfully!", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"❌ Failed to send embed:\n`{str(e)}`", ephemeral=True)

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


# -------- Keep Alive & Run --------
keep_alive()
bot.run(TOKEN)
