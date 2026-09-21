import os
import asyncio
import discord
from discord.ext import commands

# =========================================================
# الإعدادات
# =========================================================

TOKEN = os.getenv("DISCORD_TOKEN")

if not TOKEN:
    raise RuntimeError(
        "❌ لم يتم العثور على DISCORD_TOKEN في متغيرات الاستضافة."
    )

# =========================================================
# إعدادات Discord
# =========================================================

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(
    command_prefix=".",
    intents=intents
)

# =========================================================
# بيانات الألعاب
# =========================================================

games_data = {}
scores = {}

# =========================================================
# عند تشغيل البوت
# =========================================================

@bot.event
async def on_ready():
    print("=" * 50)
    print(f"✅ تم تسجيل الدخول بنجاح باسم: {bot.user}")
    print(f"🆔 ID: {bot.user.id}")
    print("🎮 بوت الألعاب يعمل بنجاح!")
    print("=" * 50)


# =========================================================
# إنشاء لعبة
# =========================================================

@bot.command(name="انشاء_لعبة")
async def create_game(ctx):

    guild_id = ctx.guild.id

    if guild_id not in games_data:
        games_data[guild_id] = []

    await ctx.send(
        "🎮 **إنشاء لعبة جديدة**\n\n"
        "أرسل الصورة الأولى ومعها الإجابة في نفس الرسالة.\n"
        "مثال:\n"
        "`Apple` + صورة Apple\n\n"
        "📌 أرسل الصور واحدة وراء الثانية.\n"
        "🛑 عندما تنتهي اكتب `تم`.\n"
        "⏱️ لديك دقيقة واحدة بين كل سؤال."
    )

    def check(message):
        return (
            message.author.id == ctx.author.id
            and message.channel.id == ctx.channel.id
        )

    while True:

        try:
            message = await bot.wait_for(
                "message",
                timeout=60,
                check=check
            )

        except asyncio.TimeoutError:
            await ctx.send(
                "⏰ انتهى الوقت.\n"
                "لم يتم إرسال رسالة خلال دقيقة."
            )
            break

        # إنهاء الإنشاء
        if message.content.strip().lower() == "تم":

            count = len(games_data[guild_id])

            await ctx.send(
                f"✅ **تم حفظ اللعبة بنجاح!**\n"
                f"📚 عدد الأسئلة: **{count}**"
            )

            break

        # التأكد من وجود صورة
        if not message.attachments:

            await ctx.send(
                "⚠️ يجب إرسال **صورة + الإجابة** في نفس الرسالة."
            )
            continue

        # التأكد من وجود إجابة
        answer = message.content.strip()

        if not answer:

            await ctx.send(
                "⚠️ نسيت كتابة الإجابة.\n"
                "أرسل الصورة ومعها الإجابة."
            )
            continue

        # حفظ الصورة والإجابة
        image_url = message.attachments[0].url

        games_data[guild_id].append(
            {
                "image": image_url,
                "answer": answer
            }
        )

        number = len(games_data[guild_id])

        await ctx.send(
            f"✅ تمت إضافة السؤال رقم **{number}**.\n"
            "📸 أرسل السؤال التالي أو اكتب `تم`."
        )


# =========================================================
# بدء اللعبة
# =========================================================

@bot.command(name="ابدا")
async def start_game(ctx):

    guild_id = ctx.guild.id

    # التأكد من وجود لعبة
    if guild_id not in games_data or not games_data[guild_id]:

        await ctx.send(
            "❌ لا توجد لعبة مسجلة.\n"
            "استخدم `.انشاء_لعبة` أولاً."
        )
        return

    # التأكد من عدم وجود لعبة تعمل
    if getattr(bot, "game_running", False):

        await ctx.send(
            "⚠️ توجد لعبة تعمل بالفعل."
        )
        return

    bot.game_running = True

    try:

        # عد تنازلي
        await ctx.send("🚨 **اللعبة تبدأ خلال:**")

        await ctx.send("3️⃣")
        await asyncio.sleep(1)

        await ctx.send("2️⃣")
        await asyncio.sleep(1)

        await ctx.send("1️⃣")
        await asyncio.sleep(1)

        await ctx.send(
            "🔥 **انطلاق اللعبة!**"
        )

        # إنشاء نظام النقاط
        if guild_id not in scores:
            scores[guild_id] = {}

        questions = games_data[guild_id]

        # الأسئلة
        for index, question in enumerate(
            questions,
            start=1
        ):

            await ctx.send(
                f"━━━━━━━━━━━━━━━━━━\n"
                f"🎯 **السؤال {index} من {len(questions)}**\n"
                f"━━━━━━━━━━━━━━━━━━"
            )

            # إرسال الصورة
            await ctx.send(
                question["image"]
            )

            # فحص الإجابات
            def check_answer(message):

                return (
                    message.channel.id == ctx.channel.id
                    and not message.author.bot
                )

            try:

                message = await bot.wait_for(
                    "message",
                    timeout=10,
                    check=check_answer
                )

                # الإجابة الصحيحة
                if (
                    message.content.strip().casefold()
                    == question["answer"].strip().casefold()
                ):

                    user_id = message.author.id

                    scores[guild_id][user_id] = (
                        scores[guild_id].get(user_id, 0) + 1
                    )

                    await ctx.send(
                        f"🎉 **أحسنت {message.author.mention}!**\n"
                        f"✅ إجابة صحيحة\n"
                        f"🏆 +1 نقطة"
                    )

                else:

                    await ctx.send(
                        "❌ الإجابة غير صحيحة."
                    )

            except asyncio.TimeoutError:

                await ctx.send(
                    "⏰ انتهى الوقت!\n"
                    "لم يجب أحد."
                )

            await asyncio.sleep(2)

        # =================================================
        # النتائج
        # =================================================

        await ctx.send(
            "🏆 **انتهت اللعبة!**\n"
            "📊 النتائج:"
        )

        if not scores.get(guild_id):

            await ctx.send(
                "لم يحصل أي لاعب على نقاط."
            )

        else:

            sorted_scores = sorted(
                scores[guild_id].items(),
                key=lambda item: item[1],
                reverse=True
            )

            result_lines = []

            for position, (user_id, points) in enumerate(
                sorted_scores,
                start=1
            ):

                member = ctx.guild.get_member(user_id)

                if member:
                    name = member.display_name
                else:
                    name = f"ID: {user_id}"

                result_lines.append(
                    f"**{position}.** {name} — 🏆 {points} نقطة"
                )

            await ctx.send(
                "\n".join(result_lines)
            )

    finally:

        bot.game_running = False


# =========================================================
# تصفير الألعاب
# =========================================================

@bot.command(name="تصفير_العاب")
async def reset_games(ctx):

    guild_id = ctx.guild.id

    games_data[guild_id] = []
    scores[guild_id] = {}

    await ctx.send(
        "🗑️ **تم التصفير بنجاح!**\n"
        "تم حذف جميع الأسئلة والنتائج."
    )


# =========================================================
# أمر اختبار
# =========================================================

@bot.command(name="اختبار")
async def test_command(ctx):

    await ctx.send(
        "✅ بوت الألعاب يعمل بشكل صحيح!"
    )


# =========================================================
# معالجة الأخطاء
# =========================================================

@bot.event
async def on_command_error(ctx, error):

    if isinstance(error, commands.CommandNotFound):
        return

    if isinstance(error, commands.MissingRequiredArgument):

        await ctx.send(
            "⚠️ هناك معلومات ناقصة في الأمر."
        )
        return

    print(
        f"❌ حدث خطأ في الأمر: {error}"
    )


# =========================================================
# تشغيل البوت
# =========================================================

bot.run(TOKEN)
