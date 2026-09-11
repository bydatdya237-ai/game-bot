import discord
from discord.ext import commands
import asyncio
import os

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='.', intents=intents)

games_data = {}
scores = {}

@bot.event
async def on_ready():
    print(f'تم تسجيل الدخول بنجاح باسم: {bot.user}')

@bot.command()
async def انشاء_لعبة(ctx):
    await ctx.send("🎮 أرسل الآن **الصورة الأولى** ومعها الإجابة بالشكل التالي في رسالة واحدة: \nمثال: `الإجابة` \n(عندك دقيقة لإرسال الصور، وإذا خلصت اكتب `تم`)")
    
    if ctx.guild.id not in games_data:
        games_data[ctx.guild.id] = []

    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel

    while True:
        try:
            msg = await bot.wait_for('message', timeout=60.0, check=check)
            if msg.content.lower() == 'تم':
                await ctx.send(f"✅ تم حفظ اللعبة بنجاح! عدد الأسئلة الحالية: {len(games_data[ctx.guild.id])}")
                break
            
            if msg.attachments:
                image_url = msg.attachments[0].url
                answer = msg.content.strip()
                if not answer:
                    await ctx.send("⚠️ نسيت تكتب الإجابة مع الصورة، عِد المحاولة أو اكتب 'تم' للإيقاف.")
                    continue
                
                games_data[ctx.guild.id].append({"image": image_url, "answer": answer})
                await ctx.send(f"📌 تمت إضافة السؤال رقم {len(games_data[ctx.guild.id])}. أرسل الصورة التالية أو اكتب `تم`.")
            else:
                await ctx.send("⚠️ يرجى إرسال صورة مرفقة مع الإجابة.")
        except asyncio.TimeoutError:
            await ctx.send("⏰ انتهى الوقت ولم تنهِ إنشاء اللعبة.")
            break

@bot.command()
async def ابدا(ctx):
    guild_id = ctx.guild.id
    if guild_id not in games_data or not games_data[guild_id]:
        await ctx.send("❌ مافي أي لعبة مسجلة! استخدم `.انشاء_لعبة` أولاً.")
        return

    await ctx.send("🚨 اللعبة تبدأ خلال: \n3️⃣")
    await asyncio.sleep(1)
    await ctx.send("2️⃣")
    await asyncio.sleep(1)
    await ctx.send("1️⃣\n🔥 انطلاق اللعبة!")

    if guild_id not in scores:
        scores[guild_id] = {}

    questions = games_data[guild_id]
    
    for index, q in enumerate(questions, start=1):
        await ctx.send(f"--- \n**السؤال {index} من {len(questions)}:**")
        await ctx.send(q["image"])

        def check_answer(m):
            return m.channel == ctx.channel and not m.author.bot

        try:
            msg = await bot.wait_for('message', timeout=10.0, check=check_answer)
            if msg.content.strip().lower() == q["answer"].lower():
                winner = msg.author
                scores[guild_id][winner.name] = scores[guild_id].get(winner.name, 0) + 1
                await ctx.send(f"🎉 كفو {winner.mention}! جاوب صح وأخذ نقطة. الإجابة الصحيحة كانت: **{q['answer']}**")
            else:
                await ctx.send(f"⏰ انتهى الوقت أو الإجابة خطأ! الإجابة الصحيحة كانت: **{q['answer']}**")
        except asyncio.TimeoutError:
            await ctx.send(f"⏰ انتهى الوقت! محد جاوب. الإجابة الصحيحة كانت: **{q['answer']}**")
        
        await asyncio.sleep(2)

    await ctx.send("🏆 **انتهت اللعبة! نتائج اللاعبين:**")
    if guild_id in scores and scores[guild_id]:
        sorted_scores = sorted(scores[guild_id].items(), key=lambda x: x[1], reverse=True)
        result_text = "\n".join([f"👤 {name}: {pts} نقاط" for name, pts in sorted_scores])
        await ctx.send(result_text)
    else:
        await ctx.send("مافي أحد جمع نقاط.")

@bot.command()
async def تصفير_العاب(ctx):
    guild_id = ctx.guild.id
    if guild_id in games_data:
        games_data[guild_id] = []
    if guild_id in scores:
        scores[guild_id] = {}
    await ctx.send("🗑️ تم تصفير وحذف جميع الألعاب والأسئلة والنتائج بنجاح!")

# تشغيل البوت بأمان من إعدادات الاستضافة
bot.run(os.getenv('DISCORD_TOKEN'))
