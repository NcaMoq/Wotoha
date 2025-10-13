import asyncio
from collections import defaultdict
from dataclasses import dataclass, field
import discord

@dataclass
class GuildState:
    queue: asyncio.Queue = field(default_factory=asyncio.Queue)
    voice: discord.VoiceClient = None
    looping: bool = False
    current: dict = None
    player_task: asyncio.Task = None
    play_finished: asyncio.Event = field(default_factory=asyncio.Event)
    stream_cache: dict = field(default_factory=dict)

guild_states = defaultdict(GuildState)