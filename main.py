import os
import discord
from discord.ext import commands

TOKEN = os.getenv("TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(
command_prefix="!",
intents=intents,
help_command=None
)

@bot.event
async def on_ready():
print(f"✅ تم تشغيل البوت: {bot.user}")
print(f"🆔 ID: {bot.user.id}")

@bot.command()
async def ping(ctx):
await ctx.send("🏓 Pong!")

if name == "main":
if not TOKEN:
raise RuntimeError("❌ لم يتم العثور على TOKEN في متغيرات البيئة")

bot.run(TOKEN)
