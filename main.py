import discord
from discord.ext import commands
from discord import app_commands
import os
import datetime
import traceback
from keep_alive import keep_alive

# === CONFIGURATION ===
TOKEN = os.environ["DISCORD_BOT_TOKEN"]
GUILD_ID = 1169251155721846855  # server ID
PROOF_CHANNEL_ID = 1393423615432720545 
FORWARDPROOF_ROLE_ID = 1346488365608079452  # Role for proof forwarding
SAYEMBED_ROLE_ID = 1346488355486961694  # Role for announcement embeds (higher role)
THUMBNAIL_URL = "https://cdn.discordapp.com/attachments/1372059707694645360/1393578650015760516/491878536_605875318625766_7662976636025833179_n.png?ex=6873aec1&is=68725d41&hm=e83988dc1a3f58e4839f31e74d1ec5b00c1ca930aaf7d3dcdc9837b4472fbf0a&"  # Set a default thumbnail if desired

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# Embed color map
color_map = {
    "red": discord.Color.red(),
    "blue": discord.Color.blue(),
    "green": discord.Color.green(),
    "orange": discord.Color.orange(),
    "yellow": discord.Color.gold(),
    "purple": discord.Color.purple(),
    "black": discord.Color.darker_grey(),
    "white": discord.Color.lighter_grey(),
    "cyan": discord.Color.from_rgb(0, 255, 255),
    "pink": discord.Color.from_rgb(255, 105, 180),
    "gold": discord.Color.gold(),
    "grey": discord.Color.greyple(),
    "navy": discord.Color.from_rgb(0, 0, 128),
    "teal": discord.Color.teal(),
}


async def handle_proof_forward(source, reporter, accused, replied_msg, is_slash):
    try:
        if not replied_msg or not replied_msg.attachments:
            msg = "❌ No attachments found in the replied message."
            if is_slash:
                await source.response.send_message(msg, ephemeral=True)
            else:
                await source.send(msg)
            return

        embed = discord.Embed(
            title="FRP Proof Submitted",
            description=f"**Reporter:** {reporter}\n**Accused:** {accused}",
            color=discord.Color.red(),
            timestamp=datetime.datetime.utcnow()
        )
        embed.set_footer(text="FRP BOT")
        embed.set_image(url=replied_msg.attachments[0].url)
        embed.set_thumbnail(url=THUMBNAIL_URL)

        files = [await attachment.to_file() for attachment in replied_msg.attachments[1:]]
        target_channel = bot.get_channel(PROOF_CHANNEL_ID)

        if target_channel:
            await target_channel.send(embed=embed, files=files)
            if is_slash:
                await source.response.send_message("✅ Proof forwarded.", ephemeral=True)
            else:
                await source.send("✅ Proof forwarded.")
        else:
            raise Exception("Target proof channel not found.")

    except Exception as e:
        err_msg = f"⚠️ Failed to forward: {str(e)}\n```{traceback.format_exc()}```"
        if is_slash:
            await source.response.send_message(err_msg, ephemeral=True)
        else:
            await source.send(err_msg)


@bot.tree.command(name="forwardproof", description="Forward a proof message to the proof channel.")
@app_commands.describe(reporter="Name of the reporter", accused="Name of the accused player")
async def forwardproof_slash(interaction: discord.Interaction, reporter: str, accused: str):
    if not any(role.id == FORWARDPROOF_ROLE_ID for role in interaction.user.roles):
        await interaction.response.send_message("❌ You don’t have permission to use this.", ephemeral=True)
        return

    replied_msg = await interaction.channel.fetch_message(interaction.target.id) if interaction.target else None
    await handle_proof_forward(interaction, reporter, accused, replied_msg, is_slash=True)


@bot.command()
async def forwardproof(ctx, reporter: str, accused: str):
    if not any(role.id == FORWARDPROOF_ROLE_ID for role in ctx.author.roles):
        await ctx.send("❌ You don’t have permission to use this.")
        return

    if not ctx.message.reference:
        await ctx.send("❌ You must reply to a message with proof attachments.")
        return

    replied_msg = await ctx.channel.fetch_message(ctx.message.reference.message_id)
    await handle_proof_forward(ctx, reporter, accused, replied_msg, is_slash=False)


@bot.tree.command(name="sayembed", description="Send an embed to a specific channel.")
@app_commands.describe(title="Embed title", description="Embed body", channel="Target channel", color="Embed color", footer="Footer text", thumbnail="Thumbnail URL")
async def sayembed(interaction: discord.Interaction, title: str, description: str, channel: discord.TextChannel, color: str = "blue", footer: str = None, thumbnail: str = None):
    if not any(role.id == SAYEMBED_ROLE_ID for role in interaction.user.roles):
        await interaction.response.send_message("❌ You don’t have permission.", ephemeral=True)
        return

    embed_color = color_map.get(color.lower(), discord.Color.blue())
    embed = discord.Embed(title=title, description=description, color=embed_color, timestamp=datetime.datetime.utcnow())
    if footer:
        embed.set_footer(text=footer)
    else:
        embed.set_footer(text="FRP BOT")
    if thumbnail:
        embed.set_thumbnail(url=thumbnail)
    else:
        embed.set_thumbnail(url=THUMBNAIL_URL)

    try:
        await channel.send(embed=embed)
        await interaction.response.send_message("✅ Embed sent successfully.", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"❌ Failed to send embed: `{str(e)}`", ephemeral=True)


@bot.command()
async def say(ctx, *, args=None):
    if not any(role.id == SAYEMBED_ROLE_ID for role in ctx.author.roles):
        await ctx.send("❌ You don’t have permission.")
        return

    if not ctx.message.reference:
        await ctx.send("❌ You must reply to a message that will become the embed body.")
        return

    if not args:
        await ctx.send("❌ Invalid format.\n**Usage:** `!say <title> #channel-name`")
        return

    try:
        # Split args into title and channel
        parts = args.rsplit(" ", 1)
        if len(parts) != 2:
            raise ValueError("Missing title or channel.")
        
        title, channel_mention = parts
        channel = await commands.TextChannelConverter().convert(ctx, channel_mention)

        replied_msg = await ctx.channel.fetch_message(ctx.message.reference.message_id)
        embed = discord.Embed(
            title=title.strip(),
            description=replied_msg.content,
            color=color_map.get("cyan", discord.Color.blurple()),
            timestamp=datetime.datetime.utcnow()
        )
        embed.set_footer(text="FRP BOT")
        embed.set_thumbnail(url=THUMBNAIL_URL)

        await channel.send(embed=embed)
        await ctx.send("✅ Message sent.", delete_after=5)

    except Exception as e:
        await ctx.send(f"❌ Failed to send embed. Error:\n```{str(e)}```\n**Usage:** `!say <title> #channel-name`")

    if not any(role.id == SAYEMBED_ROLE_ID for role in ctx.author.roles):
        await ctx.send("❌ You don’t have permission.")
        return

    if not ctx.message.reference:
        await ctx.send("❌ You must reply to a message to use this.")
        return

    try:
        replied_msg = await ctx.channel.fetch_message(ctx.message.reference.message_id)
        embed = discord.Embed(
            title=title,
            description=replied_msg.content,
            color=color_map.get("cyan", discord.Color.blurple()),
            timestamp=datetime.datetime.utcnow()
        )
        embed.set_footer(text="FRP BOT")
        embed.set_thumbnail(url=THUMBNAIL_URL)
        await channel.send(embed=embed)
        await ctx.send("✅ Message sent.", delete_after=5)
    except Exception as e:
        await ctx.send(f"❌ Error: `{str(e)}`")


@bot.event
async def on_ready():
    await bot.tree.sync(guild=discord.Object(id=GUILD_ID))
    print(f"✅ Bot is online as {bot.user}")


# Start server to keep alive
keep_alive()
TOKEN = os.environ.get("DISCORD_BOT_TOKEN")
bot.run(TOKEN)
