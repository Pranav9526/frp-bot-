import discord
from discord.ext import commands
from discord import app_commands
import os

# === CONFIG ===
TOKEN = os.environ["DISCORD_BOT_TOKEN"]
GUILD_ID = 123456789012345678  # 🔁 Replace with your actual server ID
PROOFS_CHANNEL_ID = 987654321098765432  # 🔁 Replace with your #frp-proofs channel ID
STAFF_ROLE_ID = 1346488365608079452  # 🔒 Role allowed to use commands

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    try:
        synced = await bot.tree.sync(guild=discord.Object(id=GUILD_ID))
        print(f"✅ Synced {len(synced)} slash command(s).")
    except Exception as e:
        print("❌ Failed to sync slash commands:", e)

# === Shared Function for Forwarding Proof ===
async def handle_proof_forward(ctx_or_interaction, reporter, accused, replied_msg, is_slash=True):
    if not replied_msg.attachments:
        msg = "❌ No attachments found in that message."
        if is_slash:
            await ctx_or_interaction.response.send_message(msg, ephemeral=True)
        else:
            await ctx_or_interaction.send(msg)
        return

    target_channel = bot.get_channel(PROOFS_CHANNEL_ID)

    embed = discord.Embed(
        title="📎 FRP Report Proof",
        description=(
            f"🧑‍💼 **Reporter:** {reporter}\n"
            f"🚫 **Accused:** {accused}\n"
            f"🗂 **Ticket Channel:** {ctx_or_interaction.channel.mention}\n"
            f"👮 **Handled By:** {ctx_or_interaction.user.mention if is_slash else ctx_or_interaction.author.mention}"
        ),
        color=discord.Color.red() if is_slash else discord.Color.orange()
    )

    timestamp = ctx_or_interaction.created_at if is_slash else ctx_or_interaction.message.created_at
    embed.set_footer(text=timestamp.strftime("Time: %d %B %Y, %I:%M %p"))

    files = []
    for i, attachment in enumerate(replied_msg.attachments):
        if i == 0:
            embed.set_image(url=attachment.url)
        else:
            embed.add_field(name=f"📎 Attachment {i+1}", value=attachment.url, inline=False)
        file = await attachment.to_file()
        files.append(file)

    await target_channel.send(embed=embed, files=files)

    success_msg = "✅ Proof forwarded successfully!"
    if is_slash:
        await ctx_or_interaction.response.send_message(success_msg, ephemeral=True)
    else:
        await ctx_or_interaction.send(success_msg)

# === Slash Command ===
@bot.tree.command(name="forward-proof", description="Forward proof to frp-proofs channel")
@app_commands.describe(reporter="Name of the reporter", accused="Name of the reported player")
async def forward_proof(interaction: discord.Interaction, reporter: str, accused: str):
    if not any(role.id == STAFF_ROLE_ID for role in interaction.user.roles):
        await interaction.response.send_message("❌ You are not authorized to use this command.", ephemeral=True)
        return

    if not interaction.channel.name.startswith("ticket"):
        await interaction.response.send_message("❌ Use this only in a ticket channel.", ephemeral=True)
        return

    if not interaction.message or not interaction.message.reference:
        await interaction.response.send_message("❌ You must reply to a message with the proof!", ephemeral=True)
        return

    replied_msg = await interaction.channel.fetch_message(interaction.message.reference.message_id)
    await handle_proof_forward(interaction, reporter, accused, replied_msg, is_slash=True)

# === Prefix Command ===
@bot.command(name="forwardproof")
async def forwardproof(ctx, reporter: str = None, accused: str = None):
    if STAFF_ROLE_ID not in [role.id for role in ctx.author.roles]:
        await ctx.send("❌ You are not authorized to use this command.")
        return

    if not ctx.channel.name.startswith("ticket"):
        await ctx.send("❌ Use this only in a ticket channel.")
        return

    if not ctx.message.reference:
        await ctx.send("❌ You must reply to a message with proof!")
        return

    if not reporter or not accused:
        await ctx.send("❌ Usage: `!forwardproof <reporter> <accused>`")
        return

    replied_msg = await ctx.channel.fetch_message(ctx.message.reference.message_id)
    await handle_proof_forward(ctx, reporter, accused, replied_msg, is_slash=False)

# === Start the Bot ===
bot.run(TOKEN)
