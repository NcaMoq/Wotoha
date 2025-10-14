import asyncio
import logging
import random

import discord
from discord import app_commands, Embed
from discord.ext import commands
from discord.ui import View, button, Button

from utils.state import guild_states
from utils.helpers import (
    is_allowed_url,
    extract_full_info,
    prepare_audio_source,
    set_bot_nickname,
)

logger = logging.getLogger(__name__)

#PlayerView
class PlayerView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @button(label="⏭️Skip", style=discord.ButtonStyle.secondary, custom_id="player_skip")
    @app_commands.checks.cooldown(1, 5.0, key=lambda i: (i.guild_id, i.user.id))
    async def skip_button(self, interaction: discord.Interaction, button: Button):
        state = guild_states[interaction.guild.id]
        if state.voice is None or not state.voice.is_playing():
            embed = Embed(description="再生中の曲がありません。", color=0xE74C3C)
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            was_looping = state.looping
            state.looping = False
            state.voice.stop()
            if was_looping:
                await set_bot_nickname(interaction.guild, None)
            await interaction.response.defer()

    @button(label="🔂Loop", style=discord.ButtonStyle.secondary, custom_id="player_loop")
    @app_commands.checks.cooldown(1, 15.0, key=lambda i: (i.guild_id, i.user.id))
    async def loop_button(self, interaction: discord.Interaction, button: Button):
        state = guild_states[interaction.guild.id]
        state.looping = not state.looping
        nick = "音葉 🔁" if state.looping else None
        await set_bot_nickname(interaction.guild, nick)
        await interaction.response.defer()

    @button(label="🔀Shuffle", style=discord.ButtonStyle.secondary, custom_id="player_shuffle")
    @app_commands.checks.cooldown(1, 5.0, key=lambda i: (i.guild_id, i.user.id))
    async def shuffle_button(self, interaction: discord.Interaction, button: Button):
        state = guild_states[interaction.guild.id]
        if state.queue.qsize() < 2:
            embed = Embed(description="シャッフルできる曲がありません。", color=0xE74C3C)
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        
        queue_list = list(state.queue._queue)
        random.shuffle(queue_list)
        
        new_queue = asyncio.Queue()
        for item in queue_list:
            await new_queue.put(item)
        state.queue = new_queue
        
        embed = Embed(description="プレイリストをシャッフルしました！", color=0x49b0e4)
        await interaction.response.send_message(embed=embed)

    @button(label="🎵", style=discord.ButtonStyle.success, custom_id="player_now")
    @app_commands.checks.cooldown(1, 5.0, key=lambda i: (i.guild_id, i.user.id))
    async def now_button(self, interaction: discord.Interaction, button: Button):
        cur = guild_states[interaction.guild.id].current
        if cur:
            embed = Embed(
                title="🎵 Now Playing",
                description=f"[{cur.get('title')}]({cur.get('webpage_url')})",
                color=0x49b0e4
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            embed = Embed(description="再生中の曲がありません。", color=0xE74C3C)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
    @button(label="🗒️List", style=discord.ButtonStyle.primary, custom_id="player_queue")
    @app_commands.checks.cooldown(1, 5.0, key=lambda i: (i.guild_id, i.user.id))
    async def queue_button(self, interaction: discord.Interaction, button: Button):
        state = guild_states[interaction.guild.id]
        current_song = state.current
        queued_songs = list(state.queue._queue)

        if not current_song and not queued_songs:
            embed = Embed(description="プレイリストは空です。", color=0xE74C3C)
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        embed = Embed(title="🗒️Playlist", color=0x49b0e4)
        if current_song:
            embed.add_field(
                name=f"Now playing: {current_song.get('title')}",
                value=f"[{current_song.get('uploader')}]({current_song.get('webpage_url')})",
                inline=False
            )

        if queued_songs:
            queue_text = "\n".join([f"{idx+1}. [{info.get('title')}]({info.get('webpage_url')})" for idx, info in enumerate(queued_songs[:10])])
            if len(queued_songs) > 10:
                queue_text += f"\n...and {len(queued_songs) - 10} more songs"
            embed.add_field(name="Next Up", value=queue_text, inline=False)

        await interaction.response.send_message(embed=embed, ephemeral=True)


class MusicCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def player_loop(self, guild_id: int):
        state = guild_states[guild_id]
        while True:
            try:
                if state.looping and state.current:
                    info = state.current
                else:
                    info = await state.queue.get()

                if state.voice is None or not state.voice.is_connected():
                    break
                
                state.play_finished.clear()
                
                try:
                    source = await prepare_audio_source(info)
                except Exception as e:
                    logger.info("Skipping a track due to preparation error: %s", type(e).__name__)
                    continue
                
                state.voice.play(source, after=lambda e: state.play_finished.set())
                state.current = info
                
                await state.play_finished.wait()

                if not state.looping:
                    state.current = None

            except asyncio.CancelledError:
                logger.info(f"Player loop for guild {guild_id} cancelled.")
                break
            except Exception as e:
                logger.error(f"Error in player loop for guild {guild_id}: {e}")
                await asyncio.sleep(5)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if before.channel == after.channel:
            return
        vc = member.guild.voice_client
        if not vc or not vc.is_connected():
            return
        if len(vc.channel.members) == 1 and vc.channel.members[0].id == self.bot.user.id:
            state = guild_states.pop(member.guild.id, None)
            if state and state.player_task:
                state.player_task.cancel()
            await vc.disconnect()
            await set_bot_nickname(member.guild, None)
            logger.info(f"Automatically disconnected from voice channel in Guild {member.guild.id}.")

    @app_commands.command(name="play", description="おんがくをさいせい")
    @app_commands.checks.cooldown(1, 5.0, key=lambda i: (i.guild_id, i.user.id))
    async def play(self, interaction: discord.Interaction, url: str):
        # 参加していない場合
        if interaction.user.voice is None:
            embed = Embed(description="ボイスチャンネルに参加してください。", color=0xE74C3C)
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        # URL無効
        if not is_allowed_url(url):
            embed = Embed(description="このURLは使用できません。", color=0xE74C3C)
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        await interaction.response.defer()

        guild_id = interaction.guild.id
        state = guild_states[guild_id]

        try:
            if not interaction.guild.voice_client:
                state.voice = await interaction.user.voice.channel.connect()
            else:
                await interaction.guild.voice_client.move_to(interaction.user.voice.channel)
                state.voice = interaction.guild.voice_client
        except Exception as e:
            logger.error(f"Voice connection error: {e}")
            embed = Embed(description="ボイスチャンネルへの接続に失敗しました。", color=0xE74C3C)
            return await interaction.followup.send(embed=embed)
        
        if state.player_task is None or state.player_task.done():
            state.player_task = self.bot.loop.create_task(self.player_loop(guild_id))

        try:
            info = await extract_full_info(url)
        except Exception:
            embed = Embed(description="楽曲情報の取得に失敗しました。", color=0xE74C3C)
            return await interaction.followup.send(embed=embed)

        was_empty = state.queue.empty() and state.current is None
        await state.queue.put(info)
        
        detail = Embed(
            title=f"{info['title']}",
            url=info['webpage_url'],
            description=info['uploader'],
            color=0x49b0e4
        )

        m, s = divmod(int(info['duration']), 60)
        detail.add_field(name="Time", value=f"{m}m {s}s", inline=True)
        detail.add_field(name="Views", value=f"{info['view_count']:,}", inline=True)
        detail.set_thumbnail(url=info.get('thumbnail'))
        
        await interaction.followup.send(embed=detail, view=PlayerView())


async def setup(bot: commands.Bot):
    await bot.add_cog(MusicCog(bot))
