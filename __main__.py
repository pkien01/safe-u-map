import discord
from .bot import DiscordBot
from safe_u import BOT_TOKEN
if __name__ == '__main__':
    intents = discord.Intents.default()
    intents.members = True
    bot = DiscordBot(intents=intents)
    bot.run(BOT_TOKEN)
            