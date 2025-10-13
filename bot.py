import os
import logging
import asyncio

import discord
from discord.ext import commands
from dotenv import load_dotenv

from cogs.music import PlayerView

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)-7s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logging.getLogger("discord").setLevel(logging.INFO)
logging.getLogger("yt_dlp").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    raise RuntimeError("Environment variable DISCORD_TOKEN is not set.")

class WotohaBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.voice_states = True
        super().__init__(command_prefix="!", intents=intents)
        self.persistent_views_added = False

    async def setup_hook(self):
        await self.load_extension("cogs.music")
        logger.info("Loaded cog 'cogs.music'.")
        
        if not self.persistent_views_added:
            self.add_view(PlayerView())
            self.persistent_views_added = True
            logger.info("Registered persistent view 'PlayerView'.")

    async def on_ready(self):
        logger.info(f"Bot has started: {self.user} (ID: {self.user.id})")
        
        await self.change_presence(activity=discord.CustomActivity(name='まるまるもりもり'))
        
        try:
            synced = await self.tree.sync()
            logger.info(f"Synced {len(synced)} command(s).")
        except Exception as e:
            logger.exception(f"Failed to sync commands: {e}")

async def main():
    bot = WotohaBot()
    await bot.start(TOKEN)

if __name__ == "__main__":
    try:
        discord.opus.load_opus('libopus.so')
        logger.debug("Successfully loaded Opus library.")
    except Exception:
        logger.warning("Failed to load Opus library. Voice playback may be unavailable.")

    asyncio.run(main())