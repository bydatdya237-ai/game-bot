import os
import discord
from discord.ext import commands


# =========================================================
# التوكن
# =========================================================

TOKEN = os.getenv("DISCORD_TOKEN")

if not TOKEN:
    raise RuntimeError(
        "❌ لم يتم العثور على DISCORD_TOKEN في Railway."
    )


# =========================================================
# إعدادات البوت
# =========================================================

intents = discord.Intents.default()
intents.message_content = True
intents.members = True


bot = commands.Bot(
    command_prefix="",
    intents=intents,
    help_command=None
)


# =========================================================
# تحميل جميع الـ Cogs تلقائياً
# =========================================================

async def load_extensions():

    if not os.path.exists("./cogs"):
        os.makedirs("./cogs")

    for filename in os.listdir("./cogs"):

        if not filename.endswith(".py"):
            continue

        if filename.startswith("_"):
            continue

        try:

            await bot.load_extension(
                f"cogs.{filename[:-3]}"
            )

            print(
                f"✅ تم تحميل Cog: {filename}"
            )

        except Exception as e:

            print(
                f"❌ فشل تحميل Cog: {filename}"
            )

            print(
                f"الخطأ: {e}"
            )


# =========================================================
# تحميل الـ Cogs قبل تشغيل البوت
# =========================================================

@bot.event
async def setup_hook():

    await load_extensions()


# =========================================================
# عند تشغيل البوت
# =========================================================

@bot.event
async def on_ready():

    print("=" * 50)

    print(
        f"✅ البوت دخل بنجاح: {bot.user}"
    )

    print(
        f"🆔 ID: {bot.user.id}"
    )

    print(
        "🎮 نظام Cogs يعمل"
    )

    print(
        "⌨️ الأوامر تعمل بدون Prefix"
    )

    print("=" * 50)


# =========================================================
# تشغيل البوت
# =========================================================

bot.run(TOKEN)
