import logging
import discord
import multiprocessing

from .config import AlertProviderConfig

class DiscordAlert(discord.Client):
    def __init__(self, config: AlertProviderConfig, queue: multiprocessing.Queue):
        discord.Client.__init__(self, intents=discord.Intents.default())
        self.config = config
        self.queue = queue
        self.logger = logging.getLogger("discord_alert")
 
    async def start(self):
        await discord.Client.start(self, self.config.app_token)
        self.logger.warn("startup complete")

    async def on_ready(self):
        channel = self.get_channel(self.config.channel_id)
        await channel.send("Discord Alert ready")

    async def background_task(self):
        await self.wait_until_ready()
        self.logger.info("loop setup complete")
        channel = self.get_channel(self.config.channel_id)
        while True:
            msg = self.queue.get()
            await channel.send(msg)

class AlertManager():
    def __init__(self, queue: multiprocessing.Queue):
        # TODO: for each alert provider, add a queue
        self.queue = queue
        self.logger = logging.getLogger("alert_manager")
    
    def alert(self, msg):
        # TODO: add to the corresponding queue for each alert provider
        self.logger.debug("alert called")
        self.queue.put(msg)
