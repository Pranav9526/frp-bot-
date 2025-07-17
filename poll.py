import discord
from discord.ext import commands
from discord import app_commands
import re
import asyncio
from typing import Optional

LOG_CHANNEL_ID = 1395449524570423387

class PollView(discord.ui.View):
    def __init__(self, options, author_id, multiple_votes, *, timeout=None):
        super().__init__(timeout=timeout)
        self.options = options
        self.author_id = author_id
        self.multiple_votes = multiple_votes
        self.votes = {i: [] for i in range(len(options))}
        self.poll_ended = False

        for i, option in enumerate(options):
            self.add_item(PollButton(label=option, index=i, view=self))

        self.add_item(PollCancelButton(view=self))

    def get_results_embed(self, question: str, author: discord.User) -> discord.Embed:
        total_votes = sum(len(voters) for voters in self.votes.values())
        embed = discord.Embed(title=f"📊 Poll Results: {question}", color=discord.Color.blurple())
        for i, option in enumerate(self.options):
            vote_count = len(self.votes[i])
            percent = (vote_count / total_votes) * 100 if total_votes > 0 else 0
            embed.add_field(name=f"{option}", value=f"{vote_count} votes ({percent:.1f}%)", inline=False)
        embed.set_footer(text=f"Poll by {author.name}")
        return embed

class PollButton(discord.ui.Button):
    def __init__(self, label, index, view: PollView):
        super().__init__(label=label, style=discord.ButtonStyle.secondary)
        self.index = index
        self.view_obj = view

    async def callback(self, interaction: discord.Interaction):
        if self.view_obj.poll_ended:
            return await interaction.response.send_message("This poll has already ended.", ephemeral=True)

        user_id = interaction.user.id

        if self.view_obj.multiple_votes:
            if user_id in self.view_obj.votes[self.index]:
                return await interaction.response.send_message("You've already voted for this option.", ephemeral=True)
        else:
            # Remove vote from all other options
            for voters in self.view_obj.votes.values():
                if user_id in voters:
                    voters.remove(user_id)

        self.view_obj.votes[self.index].append(user_id)
        await interaction.response.send_message("✅ Vote recorded!", ephemeral=True)

class PollCancelButton(discord.ui.Button):
    def __init__(self, view: PollView):
        super().__init__(label="❌ Cancel Poll", style=discord.ButtonStyle.danger)
        self.view_obj = view

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.view_obj.author_id:
            return await interaction.response.send_message("Only the poll creator can cancel this poll.", ephemeral=True)

        self.view_obj.poll_ended = True
        for child in self.view_obj.children:
            child.disabled = True
        await interaction.message.edit(view=self.view_obj)

        log_channel = interaction.client.get_channel(LOG_CHANNEL_ID)
        if log_channel:
            await log_channel.send(embed=discord.Embed(
                title="❌ Poll Cancelled",
                description=f"The poll was cancelled by {interaction.user.mention}.",
                color=discord.Color.red()
            ))

        await interaction.response.send_message("Poll cancelled.", ephemeral=True)

class Poll(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="poll", description="Create a poll")
    @app_commands.describe(
        question="The question to ask in the poll.",
        options="Comma-separated list of options (2-10).",
        duration="Poll duration (e.g., 1d2h30m or 'never').",
        multiple_votes="Allow users to vote for multiple options?"
    )
    async def poll(
        self,
        interaction: discord.Interaction,
        question: str,
        options: str,
        duration: str = "5m",
        multiple_votes: bool = False
    ):
        raw_options = [opt.strip() for opt in options.split(",") if opt.strip()]
        if len(raw_options) < 2 or len(raw_options) > 10:
            return await interaction.response.send_message("❌ You must provide between 2 and 10 options.", ephemeral=True)

        # Duration handling
        if duration.lower() == "never":
            poll_duration = None
        else:
            match = re.findall(r"(\d+)([dhm])", duration.lower())
            if not match:
                return await interaction.response.send_message("❌ Invalid duration format. Use like `1d2h30m` or `never`.", ephemeral=True)
            poll_duration = sum(
                int(value) * (86400 if unit == "d" else 3600 if unit == "h" else 60)
                for value, unit in match
            )
            if poll_duration == 0:
                return await interaction.response.send_message("❌ Poll duration must be greater than 0.", ephemeral=True)

        view = PollView(raw_options, interaction.user.id, multiple_votes, timeout=poll_duration)
        embed = discord.Embed(title=f"📊 {question}", color=discord.Color.blurple())
        for i, option in enumerate(raw_options):
            embed.add_field(name=f"Option {i+1}", value=option, inline=False)
        embed.set_footer(text=f"Poll by {interaction.user.name}")

        await interaction.response.send_message(embed=embed, view=view)
        message = await interaction.original_response()

        if poll_duration:
            await asyncio.sleep(poll_duration)
            if not view.poll_ended:
                view.poll_ended = True
                for child in view.children:
                    child.disabled = True
                await message.edit(view=view)
                result_embed = view.get_results_embed(question, interaction.user)
                log_channel = self.bot.get_channel(LOG_CHANNEL_ID)
                if log_channel:
                    await log_channel.send(embed=result_embed)

async def setup(bot):
    await bot.add_cog(Poll(bot))
