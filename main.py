import discord
from discord.ext import commands
from discord import app_commands
import os
from keep_alive import keep_alive

# === CONFIG ===
TOKEN = os.environ["DISCORD_BOT_TOKEN"]
GUILD_ID = 1169251155721846855  # 🔁 Replace with your actual server ID
PROOFS_CHANNEL_ID = 1393423615432720545  # 🔁 Replace with your #frp-proofs channel ID
ALLOWED_ROLE_ID = 1346488365608079452  # 🔒 Role allowed to use commands

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.guilds = True
intents.guild_messages = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ Logged in as {bot.user}")

async def handle_proof_forward(ctx_or_interaction, reporter, accused, replied_msg, is_slash=True):
    if not replied_msg.attachments:
        msg = "❌ No attachments found in the replied message."
        if is_slash:
            await ctx_or_interaction.response.send_message(msg, ephemeral=True)
        else:
            await ctx_or_interaction.send(msg)
        return

    target_channel = bot.get_channel(PROOFS_CHANNEL_ID)
    if not target_channel:
        msg = "❌ Proofs channel not found. Check channel ID."
        if is_slash:
            await ctx_or_interaction.response.send_message(msg, ephemeral=True)
        else:
            await ctx_or_interaction.send(msg)
        return

    embed = discord.Embed(
        title="📎 FRP Report Proof",
        description=(
            f"🧑‍💼 **Reporter:** {reporter}\n"
            f"🚫 **Accused:** {accused}\n"
            f"📂 **Channel:** {ctx_or_interaction.channel.mention}\n"
            f"👮 **Handled By:** {ctx_or_interaction.user.mention if is_slash else ctx_or_interaction.author.mention}"
        ),
        color=discord.Color.red()
    )
    embed.set_image(url=replied_msg.attachments[0].url)

    files = [await a.to_file() for a in replied_msg.attachments]

    await target_channel.send(embed=embed, files=files)

    if is_slash:
        await ctx_or_interaction.response.send_message("✅ Proof forwarded!", ephemeral=True)
    else:
        await ctx_or_interaction.send("✅ Proof forwarded!")

@bot.tree.command(name="forward-proof")
@app_commands.describe(reporter="Name of the reporter", accused="Name of the accused")
async def forward_proof_slash(interaction: discord.Interaction, reporter: str, accused: str):
    if ALLOWED_ROLE_ID not in [r.id for r in interaction.user.roles]:
        await interaction.response.send_message("❌ You don't have permission.", ephemeral=True)
        return

    if not interaction.channel or not interaction.message or not interaction.message.reference:
        await interaction.response.send_message("❌ You must reply to a message with attachments.", ephemeral=True)
        return

    replied_msg = await interaction.channel.fetch_message(interaction.message.reference.message_id)
    await handle_proof_forward(interaction, reporter, accused, replied_msg, is_slash=True)

@bot.command()
async def forwardproof(ctx, reporter: str = None, accused: str = None):
    if not any(role.id == ALLOWED_ROLE_ID for role in ctx.author.roles):
        await ctx.send("❌ You don't have permission.")
        return

    if not reporter or not accused:
        await ctx.send("❌ Usage: !forwardproof <reporter> <accused> (reply to message)")
        return

    if not ctx.message.reference:
        await ctx.send("❌ You must reply to a message with attachments.")
        return

    replied_msg = await ctx.channel.fetch_message(ctx.message.reference.message_id)
    await handle_proof_forward(ctx, reporter, accused, replied_msg, is_slash=False)

# Start server to keep alive
keep_alive()

TOKEN = os.environ.get("DISCORD_BOT_TOKEN")
bot.run(TOKEN)
