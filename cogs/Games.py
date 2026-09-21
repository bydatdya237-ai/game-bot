import asyncio
import discord
from discord.ext import commands
from discord import ui


# =========================================================
# الإعدادات
# =========================================================

GAME_NAME = "خمن الماركة من الصورة"

SETUP_ROOM_ID = 1548289588211097710
GAME_ROOM_ID = 1545143660469813250

ALLOWED_ROLE_IDS = {
    1544078469657530578,
    1545851911121666108,
    1544426415766896690,
}


# =========================================================
# جلسة اللعبة
# =========================================================

class GameSession:

    def __init__(self, creator_id):

        self.creator_id = creator_id

        self.questions = []

        self.scores = {}

        self.is_running = False

        self.starting = False

        self.current_question_index = 0

        self.game_name = GAME_NAME


# =========================================================
# Modal تعديل اسم اللعبة
# =========================================================

class EditGameNameModal(ui.Modal):

    def __init__(self, session):

        super().__init__(
            title="✏️ تعديل اسم اللعبة"
        )

        self.session = session

        self.name_input = ui.TextInput(
            label="اسم اللعبة الجديد",
            placeholder="اكتب اسم اللعبة الجديد هنا",
            default=session.game_name,
            min_length=1,
            max_length=100,
            required=True
        )

        self.add_item(self.name_input)

    async def on_submit(self, interaction: discord.Interaction):

        new_name = self.name_input.value.strip()

        if not new_name:

            await interaction.response.send_message(
                "❌ اسم اللعبة لا يمكن أن يكون فارغًا.",
                ephemeral=True
            )

            return

        self.session.game_name = new_name

        await interaction.response.send_message(
            f"✅ تم تعديل اسم اللعبة إلى:\n**{new_name}**",
            ephemeral=True
        )


# =========================================================
# Modal إضافة سؤال
# =========================================================

class QuestionAnswerModal(ui.Modal):

    def __init__(self, session):

        super().__init__(
            title="➕ إضافة سؤال"
        )

        self.session = session

        self.answer_input = ui.TextInput(
            label="الإجابة الصحيحة",
            placeholder="مثال: Apple",
            min_length=1,
            max_length=100,
            required=True
        )

        self.add_item(self.answer_input)

    async def on_submit(self, interaction: discord.Interaction):

        answer = self.answer_input.value.strip()

        if not answer:

            await interaction.response.send_message(
                "❌ يجب كتابة الإجابة.",
                ephemeral=True
            )

            return

        await interaction.response.send_message(
            "📸 الآن أرسل **الصورة مع رسالة عادية** في روم إعداد اللعبة.\n\n"
            "سيتم ربط الصورة بالإجابة التي كتبتها.",
            ephemeral=True
        )

        channel = interaction.channel

        def check(message):

            return (
                message.author.id == interaction.user.id
                and message.channel.id == SETUP_ROOM_ID
                and len(message.attachments) > 0
            )

        try:

            message = await interaction.client.wait_for(
                "message",
                timeout=300,
                check=check
            )

        except asyncio.TimeoutError:

            try:

                await interaction.followup.send(
                    "⏰ انتهى الوقت. أعد محاولة إضافة السؤال.",
                    ephemeral=True
                )

            except Exception:
                pass

            return

        attachment = message.attachments[0]

        if not attachment.content_type:

            await interaction.followup.send(
                "❌ الملف المرفق ليس صورة.",
                ephemeral=True
            )

            return

        if not attachment.content_type.startswith("image/"):

            await interaction.followup.send(
                "❌ يجب أن يكون المرفق صورة.",
                ephemeral=True
            )

            return

        self.session.questions.append(
            {
                "image": attachment.url,
                "answer": answer
            }
        )

        question_number = len(self.session.questions)

        await interaction.followup.send(
            f"✅ تمت إضافة السؤال رقم **{question_number}** بنجاح!\n"
            f"الإجابة: **{answer}**",
            ephemeral=True
        )


# =========================================================
# لوحة التحكم
# =========================================================

class GameControlView(ui.View):

    def __init__(self, cog):

        super().__init__(timeout=None)

        self.cog = cog


    # =====================================================
    # إضافة سؤال
    # =====================================================

    @ui.button(
        label="➕ إضافة سؤال",
        style=discord.ButtonStyle.primary,
        custom_id="games:add_question"
    )
    async def add_question(
        self,
        interaction: discord.Interaction,
        button: ui.Button
    ):

        if interaction.channel.id != SETUP_ROOM_ID:

            await interaction.response.send_message(
                "❌ هذا الزر يعمل في روم إعداد اللعبة فقط.",
                ephemeral=True
            )

            return

        if not self.cog.has_allowed_role(interaction.user):

            await interaction.response.send_message(
                "❌ ما عندك صلاحية استخدام هذا الزر.",
                ephemeral=True
            )

            return

        session = self.cog.get_session(interaction.guild.id)

        if session is None:

            await interaction.response.send_message(
                "❌ لا توجد لعبة منشأة حاليًا.",
                ephemeral=True
            )

            return

        if session.is_running:

            await interaction.response.send_message(
                "❌ اللعبة بدأت بالفعل ولا يمكن إضافة أسئلة الآن.",
                ephemeral=True
            )

            return

        await interaction.response.send_modal(
            QuestionAnswerModal(session)
        )


    # =====================================================
    # تعديل اسم اللعبة
    # =====================================================

    @ui.button(
        label="✏️ تعديل الاسم",
        style=discord.ButtonStyle.secondary,
        custom_id="games:edit_name"
    )
    async def edit_name(
        self,
        interaction: discord.Interaction,
        button: ui.Button
    ):

        if interaction.channel.id != SETUP_ROOM_ID:

            await interaction.response.send_message(
                "❌ هذا الزر يعمل في روم إعداد اللعبة فقط.",
                ephemeral=True
            )

            return

        if not self.cog.has_allowed_role(interaction.user):

            await interaction.response.send_message(
                "❌ ما عندك صلاحية استخدام هذا الزر.",
                ephemeral=True
            )

            return

        session = self.cog.get_session(interaction.guild.id)

        if session is None:

            await interaction.response.send_message(
                "❌ لا توجد لعبة منشأة حاليًا.",
                ephemeral=True
            )

            return

        if session.is_running:

            await interaction.response.send_message(
                "❌ لا يمكن تعديل اسم اللعبة أثناء تشغيلها.",
                ephemeral=True
            )

            return

        await interaction.response.send_modal(
            EditGameNameModal(session)
        )


    # =====================================================
    # بدء اللعبة
    # =====================================================

    @ui.button(
        label="🚀 بدء اللعبة",
        style=discord.ButtonStyle.success,
        custom_id="games:start_game"
    )
    async def start_game(
        self,
        interaction: discord.Interaction,
        button: ui.Button
    ):

        if interaction.channel.id != GAME_ROOM_ID:

            await interaction.response.send_message(
                "❌ هذا الزر يعمل في روم الألعاب فقط.",
                ephemeral=True
            )

            return

        if not self.cog.has_allowed_role(interaction.user):

            await interaction.response.send_message(
                "❌ ما عندك صلاحية بدء اللعبة.",
                ephemeral=True
            )

            return

        session = self.cog.get_session(interaction.guild.id)

        if session is None:

            await interaction.response.send_message(
                "❌ لا توجد لعبة منشأة حاليًا.",
                ephemeral=True
            )

            return

        if session.is_running or session.starting:

            await interaction.response.send_message(
                "⚠️ يوجد لعبة جاريه بالفعل.",
                ephemeral=True
            )

            return

        if not session.questions:

            await interaction.response.send_message(
                "❌ لا توجد أسئلة في اللعبة.",
                ephemeral=True
            )

            return

        await interaction.response.send_message(
            "🚀 تم بدء اللعبة!",
            ephemeral=True
        )

        await self.cog.start_game(
            interaction.channel,
            session
        )


    # =====================================================
    # إنهاء اللعبة
    # =====================================================

    @ui.button(
        label="🛑 إنهاء اللعبة",
        style=discord.ButtonStyle.danger,
        custom_id="games:end_game"
    )
    async def end_game(
        self,
        interaction: discord.Interaction,
        button: ui.Button
    ):

        if interaction.channel.id != GAME_ROOM_ID:

            await interaction.response.send_message(
                "❌ هذا الزر يعمل في روم الألعاب فقط.",
                ephemeral=True
            )

            return

        if not self.cog.has_allowed_role(interaction.user):

            await interaction.response.send_message(
                "❌ ما عندك صلاحية إنهاء اللعبة.",
                ephemeral=True
            )

            return

        session = self.cog.get_session(interaction.guild.id)

        if session is None:

            await interaction.response.send_message(
                "❌ لا توجد لعبة حاليًا.",
                ephemeral=True
            )

            return

        session.is_running = False
        session.starting = False

        await interaction.response.send_message(
            "🛑 تم إنهاء اللعبة.",
            ephemeral=True
        )


# =========================================================
# Cog
# =========================================================

class GameCog(commands.Cog):

    def __init__(self, bot):

        self.bot = bot

        self.active_games = {}

        self.game_locks = {}


    # =====================================================
    # أدوات مساعدة
    # =====================================================

    def get_session(self, guild_id):

        return self.active_games.get(guild_id)


    def has_allowed_role(self, member):

        if not isinstance(member, discord.Member):
            return False

        return any(
            role.id in ALLOWED_ROLE_IDS
            for role in member.roles
        )


    def get_lock(self, guild_id):

        if guild_id not in self.game_locks:

            self.game_locks[guild_id] = asyncio.Lock()

        return self.game_locks[guild_id]


    # =====================================================
    # إنشاء لعبة
    # =====================================================

    @commands.command(name="انشاء-لعبة")
    async def create_game(self, ctx):

        if ctx.channel.id != SETUP_ROOM_ID:
            return

        if not self.has_allowed_role(ctx.author):

            await ctx.send(
                "❌ ما عندك صلاحية إنشاء الألعاب."
            )

            return

        guild_id = ctx.guild.id

        existing = self.get_session(guild_id)

        if existing is not None:

            if existing.is_running or existing.starting:

                await ctx.send(
                    "⚠️ يوجد لعبة جاريه بالفعل."
                )

                return

            await ctx.send(
                "⚠️ توجد لعبة منشأة بالفعل.\n"
                "استخدم `انهي` أولًا لإنهائها."
            )

            return

        session = GameSession(
            creator_id=ctx.author.id
        )

        self.active_games[guild_id] = session

        embed = discord.Embed(
            title=f"🎮 {session.game_name}",
            description=(
                "تم إنشاء لعبة جديدة.\n\n"
                "استخدم الأزرار الموجودة بالأسفل لإدارة اللعبة.\n\n"
                "➕ **إضافة سؤال:** إضافة صورة وإجابتها\n"
                "✏️ **تعديل الاسم:** تغيير اسم اللعبة\n"
                "🚀 **بدء اللعبة:** تشغيل اللعبة\n"
                "🛑 **إنهاء اللعبة:** حذف اللعبة الحالية"
            ),
            color=discord.Color.blurple()
        )

        embed.add_field(
            name="📊 عدد الأسئلة",
            value="0",
            inline=True
        )

        embed.add_field(
            name="📌 الحالة",
            value="جاهزة",
            inline=True
        )

        await ctx.send(
            embed=embed,
            view=GameControlView(self)
        )

        try:
            await ctx.message.delete()
        except Exception:
            pass


    # =====================================================
    # تعديل اسم اللعبة
    # =====================================================

    @commands.command(name="تعديل")
    async def edit_game(self, ctx):

        if ctx.channel.id != SETUP_ROOM_ID:
            return

        if not self.has_allowed_role(ctx.author):

            await ctx.send(
                "❌ ما عندك صلاحية تعديل اللعبة."
            )

            return

        session = self.get_session(ctx.guild.id)

        if session is None:

            await ctx.send(
                "❌ لا توجد لعبة منشأة حاليًا."
            )

            return

        if session.is_running:

            await ctx.send(
                "❌ لا يمكن تعديل اسم اللعبة أثناء تشغيلها."
            )

            return

        # نرسل زرًا لفتح الـ Modal لأن Discord لا يسمح
        # بفتح Modal مباشرة من رسالة عادية.

        view = EditNameCommandView(
            self,
            session
        )

        embed = discord.Embed(
            title="✏️ تعديل اسم اللعبة",
            description=(
                f"الاسم الحالي:\n"
                f"**{session.game_name}**\n\n"
                "اضغط الزر بالأسفل لفتح نافذة التعديل."
            ),
            color=discord.Color.orange()
        )

        await ctx.send(
            embed=embed,
            view=view
        )

        try:
            await ctx.message.delete()
        except Exception:
            pass


    # =====================================================
    # بدء اللعبة
    # =====================================================

    @commands.command(name="ابدا")
    async def start_command(self, ctx):

        if ctx.channel.id != GAME_ROOM_ID:
            return

        if not self.has_allowed_role(ctx.author):

            await ctx.send(
                "❌ ما عندك صلاحية بدء الألعاب."
            )

            return

        session = self.get_session(ctx.guild.id)

        if session is None:

            await ctx.send(
                "❌ لا توجد لعبة منشأة حاليًا."
            )

            return

        if session.is_running or session.starting:

            await ctx.send(
                "⚠️ يوجد لعبة جاريه بالفعل."
            )

            return

        if not session.questions:

            await ctx.send(
                "❌ لا توجد أسئلة في اللعبة.\n"
                "أضف أسئلة أولًا."
            )

            return

        await self.start_game(
            ctx.channel,
            session
        )


    # =====================================================
    # بدء اللعبة فعليًا
    # =====================================================

    async def start_game(self, channel, session):

        guild_id = channel.guild.id

        lock = self.get_lock(guild_id)

        if lock.locked():

            await channel.send(
                "⚠️ يوجد لعبة جاريه بالفعل."
            )

            return

        async with lock:

            if session.is_running:

                await channel.send(
                    "⚠️ يوجد لعبة جاريه بالفعل."
                )

                return

            session.starting = True

            await channel.send(
                embed=discord.Embed(
                    title="🎮 استعداد!",
                    description=(
                        f"**{session.game_name}**\n\n"
                        "اللعبة ستبدأ خلال:"
                    ),
                    color=discord.Color.blurple()
                )
            )

            await asyncio.sleep(1)

            await channel.send("3️⃣")

            await asyncio.sleep(1)

            await channel.send("2️⃣")

            await asyncio.sleep(1)

            await channel.send("1️⃣")

            await asyncio.sleep(1)

            session.starting = False
            session.is_running = True
            session.scores = {}
            session.current_question_index = 0

            await channel.send(
                embed=discord.Embed(
                    title="🔥 انطلاق اللعبة!",
                    description=(
                        f"**{session.game_name}**\n\n"
                        f"📊 عدد الأسئلة: **{len(session.questions)}**\n"
                        "⏱️ أمامكم **15 ثانية** لكل سؤال."
                    ),
                    color=discord.Color.green()
                )
            )

            await self.run_game_loop(
                channel,
                session
            )


    # =====================================================
    # تشغيل الأسئلة
    # =====================================================

    async def run_game_loop(self, channel, session):

        total_questions = len(session.questions)

        for index, question in enumerate(
            session.questions,
            start=1
        ):

            if not session.is_running:
                break

            session.current_question_index = index

            embed = discord.Embed(
                title=f"🎯 {session.game_name}",
                description=(
                    f"### السؤال {index} من {total_questions}\n\n"
                    "🧠 خمن الماركة من الصورة!\n\n"
                    "⏱️ الوقت: **15 ثانية**"
                ),
                color=discord.Color.blurple()
            )

            embed.set_image(
                url=question["image"]
            )

            embed.set_footer(
                text="أول إجابة صحيحة تحصل على النقطة 🏆"
            )

            await channel.send(
                embed=embed
            )

            answer = question["answer"].strip().lower()

            def check(message):

                if message.channel.id != channel.id:
                    return False

                if message.author.bot:
                    return False

                return (
                    message.content.strip().lower()
                    == answer
                )

            try:

                winner = await self.bot.wait_for(
                    "message",
                    timeout=15,
                    check=check
                )

                user_id = winner.author.id

                if user_id not in session.scores:

                    session.scores[user_id] = {
                        "name": winner.author.display_name,
                        "points": 0
                    }

                session.scores[user_id]["points"] += 1

                result_embed = discord.Embed(
                    title="🎉 إجابة صحيحة!",
                    description=(
                        f"🏆 الفائز: {winner.author.mention}\n"
                        f"➕ حصل على **1 نقطة**\n\n"
                        f"✅ الإجابة: **{question['answer']}**"
                    ),
                    color=discord.Color.green()
                )

                await channel.send(
                    embed=result_embed
                )

            except asyncio.TimeoutError:

                timeout_embed = discord.Embed(
                    title="⏰ انتهى الوقت!",
                    description=(
                        "لم يجب أحد بشكل صحيح.\n\n"
                        f"✅ الإجابة الصحيحة:\n"
                        f"**{question['answer']}**"
                    ),
                    color=discord.Color.red()
                )

                await channel.send(
                    embed=timeout_embed
                )

            await asyncio.sleep(2)

        if session.is_running:

            session.is_running = False

            await self.show_final_results(
                channel,
                session
            )


    # =====================================================
    # النتائج النهائية
    # =====================================================

    async def show_final_results(
        self,
        channel,
        session
    ):

        embed = discord.Embed(
            title="🏆 انتهت اللعبة!",
            description=(
                f"**{session.game_name}**\n\n"
                "🎉 النتائج النهائية:"
            ),
            color=discord.Color.gold()
        )

        if not session.scores:

            embed.add_field(
                name="📊 النتائج",
                value="لم يحصل أي لاعب على نقاط.",
                inline=False
            )

        else:

            sorted_scores = sorted(
                session.scores.items(),
                key=lambda item: item[1]["points"],
                reverse=True
            )

            medals = [
                "🥇",
                "🥈",
                "🥉"
            ]

            result_lines = []

            for position, (user_id, data) in enumerate(
                sorted_scores[:10],
                start=1
            ):

                medal = (
                    medals[position - 1]
                    if position <= 3
                    else f"**{position}.**"
                )

                result_lines.append(
                    f"{medal} <@{user_id}> — "
                    f"**{data['points']} نقطة**"
                )

            embed.add_field(
                name="🏆 المتصدرون",
                value="\n".join(result_lines),
                inline=False
            )

        await channel.send(
            embed=embed
        )


    # =====================================================
    # لوحة المتصدرين
    # =====================================================

    @commands.command(name="ط")
    async def leaderboard(self, ctx):

        if ctx.channel.id != GAME_ROOM_ID:
            return

        if not self.has_allowed_role(ctx.author):

            await ctx.send(
                "❌ ما عندك صلاحية استخدام هذا الأمر."
            )

            return

        session = self.get_session(ctx.guild.id)

        if session is None:

            await ctx.send(
                "❌ لا توجد لعبة حاليًا."
            )

            return

        embed = discord.Embed(
            title="🏆 لوحة المتصدرين",
            description=f"**{session.game_name}**",
            color=discord.Color.gold()
        )

        if not session.scores:

            embed.add_field(
                name="📊 النتائج",
                value="لا توجد نقاط حتى الآن.",
                inline=False
            )

        else:

            sorted_scores = sorted(
                session.scores.items(),
                key=lambda item: item[1]["points"],
                reverse=True
            )

            lines = []

            for position, (user_id, data) in enumerate(
                sorted_scores[:10],
                start=1
            ):

                lines.append(
                    f"**{position}.** <@{user_id}> — "
                    f"**{data['points']} نقطة**"
                )

            embed.add_field(
                name="النتائج",
                value="\n".join(lines),
                inline=False
            )

        await ctx.send(
            embed=embed
        )


    # =====================================================
    # تصفير النقاط
    # =====================================================

    @commands.command(name="دن")
    async def reset_scores(self, ctx):

        if ctx.channel.id != GAME_ROOM_ID:
            return

        if not self.has_allowed_role(ctx.author):

            await ctx.send(
                "❌ ما عندك صلاحية استخدام هذا الأمر."
            )

            return

        session = self.get_session(ctx.guild.id)

        if session is None:

            await ctx.send(
                "❌ لا توجد لعبة حاليًا."
            )

            return

        if session.is_running:

            await ctx.send(
                "❌ لا يمكن تصفير النقاط أثناء تشغيل اللعبة."
            )

            return

        session.scores = {}

        await ctx.send(
            "✅ تم تصفير نقاط اللاعبين بنجاح."
        )


    # =====================================================
    # إنهاء وحذف اللعبة
    # =====================================================

    @commands.command(name="انهي")
    async def end_game_command(self, ctx):

        if ctx.channel.id != GAME_ROOM_ID:
            return

        if not self.has_allowed_role(ctx.author):

            await ctx.send(
                "❌ ما عندك صلاحية إنهاء اللعبة."
            )

            return

        session = self.get_session(ctx.guild.id)

        if session is None:

            await ctx.send(
                "❌ لا توجد لعبة حاليًا."
            )

            return

        session.is_running = False
        session.starting = False

        del self.active_games[ctx.guild.id]

        await ctx.send(
            embed=discord.Embed(
                title="🛑 تم إنهاء اللعبة",
                description=(
                    "تم حذف اللعبة الحالية.\n"
                    "يمكنك إنشاء لعبة جديدة الآن."
                ),
                color=discord.Color.red()
            )
        )


# =========================================================
# View خاصة بأمر "تعديل"
# =========================================================

class EditNameCommandView(ui.View):

    def __init__(self, cog, session):

        super().__init__(timeout=120)

        self.cog = cog
        self.session = session


    @ui.button(
        label="✏️ تعديل الاسم",
        style=discord.ButtonStyle.primary
    )
    async def edit_name(
        self,
        interaction: discord.Interaction,
        button: ui.Button
    ):

        if interaction.channel.id != SETUP_ROOM_ID:

            await interaction.response.send_message(
                "❌ هذا الزر يعمل في روم إعداد اللعبة فقط.",
                ephemeral=True
            )

            return

        if not self.cog.has_allowed_role(interaction.user):

            await interaction.response.send_message(
                "❌ ما عندك صلاحية استخدام هذا الزر.",
                ephemeral=True
            )

            return

        current_session = self.cog.get_session(
            interaction.guild.id
        )

        if current_session is None:

            await interaction.response.send_message(
                "❌ اللعبة لم تعد موجودة.",
                ephemeral=True
            )

            return

        if current_session.is_running:

            await interaction.response.send_message(
                "❌ لا يمكن تعديل اسم اللعبة أثناء تشغيلها.",
                ephemeral=True
            )

            return

        await interaction.response.send_modal(
            EditGameNameModal(
                current_session
            )
        )


# =========================================================
# setup
# =========================================================

async def setup(bot):

    await bot.add_cog(
        GameCog(bot)
    )
