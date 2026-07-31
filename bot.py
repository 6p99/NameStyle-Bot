import os
import aiohttp
import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

RUNNER_TOKEN = os.environ.get("RUNNER_TOKEN")
CHANNEL_ID = os.environ.get("CHANNEL_ID")
PREFIX = os.environ.get("PREFIX", "!")

if not RUNNER_TOKEN or not CHANNEL_ID:
    raise SystemExit("❌ لازم تحط RUNNER_TOKEN و CHANNEL_ID جوا ملف .env")

CHANNEL_ID = int(CHANNEL_ID)

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix=PREFIX, intents=intents)

COLORS = [
    ("🔴 أحمر", 0xFF0000),
    ("🔵 أزرق", 0x0000FF),
    ("🟢 أخضر", 0x00FF00),
    ("🟡 أصفر", 0xFFFF00),
    ("🟣 بنفسجي", 0x9B30FF),
    ("🩷 وردي", 0xFF69B4),
    ("🟠 برتقالي", 0xFFA500),
    ("⚪ أبيض", 0xFFFFFF),
    ("⚫ أسود", 0x2B2D31),
    ("🩵 تركواز", 0x40E0D0),
    ("🥇 ذهبي", 0xFFD700),
    ("🥈 فضي", 0xC0C0C0),
    ("🔷 كحلي", 0x000080),
    ("🟤 بني", 0x8B4513),
    ("🫒 زيتي", 0x808000),
    ("🔮 نيلي", 0x4B0082),
    ("🪸 مرجاني", 0xFF7F50),
    ("🍋 ليموني", 0x32CD32),
    ("🌤️ سماوي", 0x87CEEB),
    ("🍷 عنابي", 0x800000),
    ("🔘 رمادي", 0x808080),
    ("🌿 نعناعي", 0x98FF98),
    ("🌊 بحري", 0x008080),
    ("🎆 فوشيا", 0xFF00FF),
]

FONTS = [str(n) for n in range(1, 11)]
EFFECTS = [str(n) for n in range(0, 8)]

FONT_EMOJIS = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
EFFECT_EMOJIS = ["✨", "🔥", "💧", "⚡", "🌈", "❄️", "🌟", "💫"]


def hex_to_int(color: str) -> int:
    return int(color.strip().lstrip("#"), 16)


async def apply_name_style(token: str, guild_id: str, font_id: int, effect_id: int, colors: list[int]):
    url = f"https://discord.com/api/v9/guilds/{guild_id}/members/@me"
    payload = {
        "display_name_font_id": font_id,
        "display_name_effect_id": effect_id,
        "display_name_colors": colors,
    }
    headers = {"Authorization": f"Bot {token}", "Content-Type": "application/json"}

    async with aiohttp.ClientSession() as session:
        async with session.patch(url, json=payload, headers=headers) as response:
            status = response.status
            try:
                data = await response.json()
            except Exception:
                data = await response.text()
            return status, data


class TokenModal(discord.ui.Modal, title="خطوة 1: التوكن والسيرفر"):
    token_input = discord.ui.TextInput(
        label="توكن البوت",
        placeholder="الصق توكن البوت هون",
        style=discord.TextStyle.short,
        required=True,
    )
    guild_id_input = discord.ui.TextInput(
        label="آيدي السيرفر",
        placeholder="آيدي السيرفر يلي البوت عضو فيه",
        style=discord.TextStyle.short,
        required=True,
    )

    async def on_submit(self, interaction: discord.Interaction):
        view = StyleConfigView(
            token=self.token_input.value.strip(),
            guild_id=self.guild_id_input.value.strip(),
        )
        await interaction.response.send_message(view=view, ephemeral=True)


class CustomColorModal(discord.ui.Modal, title="تحديد لون يدوي"):
    color_input = discord.ui.TextInput(
        label="كود اللون (هيكس)",
        placeholder="مثال: FF00AA",
        style=discord.TextStyle.short,
        required=True,
        max_length=7,
    )

    def __init__(self, style_view: "StyleConfigView"):
        super().__init__()
        self.style_view = style_view

    async def on_submit(self, interaction: discord.Interaction):
        raw = self.color_input.value.strip().lstrip("#")
        try:
            color = int(raw, 16)
            if not (0 <= color <= 0xFFFFFF):
                raise ValueError
        except ValueError:
            await interaction.response.send_message(
                "❌ كود اللون غلط. لازم يكون هيكس صحيح زي `FF00AA` أو `#FF00AA`.", ephemeral=True
            )
            return

        self.style_view.color = color
        for opt in self.style_view.color_select.options:
            if opt.value == "custom":
                opt.label = f"🎨 يدوي: #{raw.upper()}"
                opt.default = True
            else:
                opt.default = False

        await interaction.response.edit_message(view=self.style_view)


class ColorSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label=name, value=str(value), default=(i == 0))
            for i, (name, value) in enumerate(COLORS)
        ]
        options.append(discord.SelectOption(label="🎨 تحديد يدوي (كود اللون)", value="custom"))
        super().__init__(placeholder="اختار اللون", options=options, min_values=1, max_values=1)

    async def callback(self, interaction: discord.Interaction):
        if self.values[0] == "custom":
            await interaction.response.send_modal(CustomColorModal(self.view))
            return

        self.view.color = int(self.values[0])
        for opt in self.options:
            opt.default = opt.value == self.values[0]
        await interaction.response.edit_message(view=self.view)


class FontSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(
                label=f"شكل الخط رقم {n}", value=n, emoji=FONT_EMOJIS[i], default=(n == "1")
            )
            for i, n in enumerate(FONTS)
        ]
        super().__init__(placeholder="اختار شكل الخط (جرب أكثر من رقم)", options=options, min_values=1, max_values=1)

    async def callback(self, interaction: discord.Interaction):
        self.view.font_id = int(self.values[0])
        for opt in self.options:
            opt.default = opt.value == self.values[0]
        await interaction.response.edit_message(view=self.view)


class EffectSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(
                label=f"التأثير رقم {n}", value=n, emoji=EFFECT_EMOJIS[i], default=(n == "0")
            )
            for i, n in enumerate(EFFECTS)
        ]
        super().__init__(placeholder="اختار التأثير (جرب أكثر من رقم)", options=options, min_values=1, max_values=1)

    async def callback(self, interaction: discord.Interaction):
        self.view.effect_id = int(self.values[0])
        for opt in self.options:
            opt.default = opt.value == self.values[0]
        await interaction.response.edit_message(view=self.view)


class ApplyButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="✅ طبّق الستايل", style=discord.ButtonStyle.success)

    async def callback(self, interaction: discord.Interaction):
        view: StyleConfigView = self.view
        await interaction.response.defer(ephemeral=True, thinking=True)

        status, data = await apply_name_style(
            view.token, view.guild_id, view.font_id, view.effect_id, [view.color]
        )

        if status in (200, 204):
            await interaction.followup.send("✅ تم تغيير الستايل بنجاح! افتح البروفايل تبع البوت وشوف.", ephemeral=True)
        else:
            await interaction.followup.send(f"❌ فشل التعديل — status: `{status}`\n```{data}```", ephemeral=True)


class StyleConfigView(discord.ui.LayoutView):
    def __init__(self, token: str, guild_id: str):
        super().__init__(timeout=300)
        self.token = token
        self.guild_id = guild_id
        self.color = COLORS[0][1]
        self.font_id = 1
        self.effect_id = 0

        self.color_select = ColorSelect()

        self.add_item(
            discord.ui.Container(
                discord.ui.TextDisplay(
                    "## خطوة 2: شكل الستايل\n"
                    "اختار من القوائم تحت (فيه قيم جاهزة أصلاً)، وبعدين دوس **طبّق الستايل**."
                ),
                discord.ui.ActionRow(self.color_select),
                discord.ui.ActionRow(FontSelect()),
                discord.ui.ActionRow(EffectSelect()),
                discord.ui.ActionRow(ApplyButton()),
            )
        )


class OpenStyleButton(discord.ui.Button):
    def __init__(self):
        super().__init__(
            label="🎨 ابدأ",
            style=discord.ButtonStyle.primary,
            custom_id="open_style_modal",
        )

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(TokenModal())


class MainPanelView(discord.ui.LayoutView):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(
            discord.ui.Container(
                discord.ui.TextDisplay(
                    "## 🎨 ستايل اسم البوت\n"
                    "دوس **ابدأ**، حط التوكن وايدي السيرفر، بعدين اختار اللون والشكل من قوائم جاهزة. بس هيك."
                ),
                discord.ui.ActionRow(OpenStyleButton()),
            )
        )


@bot.event
async def on_ready():
    print(f"✅ سجل الدخول: {bot.user} ({bot.user.id})")
    bot.add_view(MainPanelView())

    channel = bot.get_channel(CHANNEL_ID)
    if channel is None:
        print("⚠️ ما لقيت الروم، تأكد من CHANNEL_ID والصلاحيات.")
        return

    await channel.send(view=MainPanelView())


@bot.command(name="panel")
async def panel(ctx: commands.Context):
    await ctx.send(view=MainPanelView())


bot.run(RUNNER_TOKEN)
        for opt in self.options:
            opt.default = opt.value == self.values[0]
        await interaction.response.edit_message(view=self.view)


class FontSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(
                label=f"شكل الخط رقم {n}", value=n, emoji=FONT_EMOJIS[i], default=(n == "1")
            )
            for i, n in enumerate(FONTS)
        ]
        super().__init__(placeholder="اختار شكل الخط (جرب أكثر من رقم)", options=options, min_values=1, max_values=1)

    async def callback(self, interaction: discord.Interaction):
        self.view.font_id = int(self.values[0])
        for opt in self.options:
            opt.default = opt.value == self.values[0]
        await interaction.response.edit_message(view=self.view)


class EffectSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(
                label=f"التأثير رقم {n}", value=n, emoji=EFFECT_EMOJIS[i], default=(n == "0")
            )
            for i, n in enumerate(EFFECTS)
        ]
        super().__init__(placeholder="اختار التأثير (جرب أكثر من رقم)", options=options, min_values=1, max_values=1)

    async def callback(self, interaction: discord.Interaction):
        self.view.effect_id = int(self.values[0])
        for opt in self.options:
            opt.default = opt.value == self.values[0]
        await interaction.response.edit_message(view=self.view)


class ApplyButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="✅ طبّق الستايل", style=discord.ButtonStyle.success)

    async def callback(self, interaction: discord.Interaction):
        view: StyleConfigView = self.view
        await interaction.response.defer(ephemeral=True, thinking=True)

        status, data = await apply_name_style(
            view.token, view.guild_id, view.font_id, view.effect_id, [view.color]
        )

        if status in (200, 204):
            await interaction.followup.send("✅ تم تغيير الستايل بنجاح! افتح البروفايل تبع البوت وشوف.", ephemeral=True)
        else:
            await interaction.followup.send(f"❌ فشل التعديل — status: `{status}`\n```{data}```", ephemeral=True)


class StyleConfigView(discord.ui.LayoutView):
    def __init__(self, token: str, guild_id: str):
        super().__init__(timeout=300)
        self.token = token
        self.guild_id = guild_id
        self.color = COLORS[0][1]
        self.font_id = 1
        self.effect_id = 0

        self.add_item(
            discord.ui.Container(
                discord.ui.TextDisplay(
                    "## خطوة 2: شكل الستايل\n"
                    "اختار من القوائم تحت (فيه قيم جاهزة أصلاً)، وبعدين دوس **طبّق الستايل**."
                ),
                discord.ui.ActionRow(ColorSelect()),
                discord.ui.ActionRow(FontSelect()),
                discord.ui.ActionRow(EffectSelect()),
                discord.ui.ActionRow(ApplyButton()),
            )
        )


class OpenStyleButton(discord.ui.Button):
    def __init__(self):
        super().__init__(
            label="🎨 ابدأ",
            style=discord.ButtonStyle.primary,
            custom_id="open_style_modal",
        )

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(TokenModal())


class MainPanelView(discord.ui.LayoutView):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(
            discord.ui.Container(
                discord.ui.TextDisplay(
                    "## 🎨 ستايل اسم البوت\n"
                    "دوس **ابدأ**، حط التوكن وايدي السيرفر، بعدين اختار اللون والشكل من قوائم جاهزة. بس هيك."
                ),
                discord.ui.ActionRow(OpenStyleButton()),
            )
        )


@bot.event
async def on_ready():
    print(f"✅ سجل الدخول: {bot.user} ({bot.user.id})")
    bot.add_view(MainPanelView())

    channel = bot.get_channel(CHANNEL_ID)
    if channel is None:
        print("⚠️ ما لقيت الروم، تأكد من CHANNEL_ID والصلاحيات.")
        return

    await channel.send(view=MainPanelView())


@bot.command(name="panel")
async def panel(ctx: commands.Context):
    await ctx.send(view=MainPanelView())


bot.run(RUNNER_TOKEN)
