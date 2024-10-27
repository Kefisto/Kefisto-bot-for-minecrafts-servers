import discord
from discord.ext import commands
from discord import app_commands
import datetime
import json
import mcrcon

# Импортируем необходимые константы и функции из основного файла бота
from bot import JSON_FILE, RCON_HOST, RCON_PORT, RCON_PASSWORD, update_whitelist

class ApplicationResponseView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Принять", style=discord.ButtonStyle.green, custom_id="accept_application")
    async def accept_application(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = interaction.message.embeds[0]
        nickname = next(field.value for field in embed.fields if field.name == "Никнейм")

        try:
            # Добавляем никнейм в JSON файл
            with open(JSON_FILE, 'r+', encoding='utf-8') as f:
                usernames = json.load(f)
                if nickname not in usernames:
                    usernames.append(nickname)
                    f.seek(0)
                    json.dump(usernames, f, ensure_ascii=False, indent=4)
                    f.truncate()

            # Обновляем вайтлист на сервере
            await update_whitelist()

            # Обновляем эмбед
            embed.color = discord.Color.green()
            embed.set_footer(text=f"Принята администратором {interaction.user.name}")
            await interaction.message.edit(embed=embed, view=None)

            await interaction.response.send_message(f"Заявка игрока {nickname} принята и добавлена в вайтлист.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"Произошла ошибка при принятии заявки: {str(e)}", ephemeral=True)

    @discord.ui.button(label="Отклонить", style=discord.ButtonStyle.red, custom_id="reject_application")
    async def reject_application(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = interaction.message.embeds[0]
        nickname = next(field.value for field in embed.fields if field.name == "Никнейм")

        # Обновляем эмбед
        embed.color = discord.Color.red()
        embed.set_footer(text=f"Отклонена администратором {interaction.user.name}")
        await interaction.message.edit(embed=embed, view=None)

        await interaction.response.send_message(f"Заявка игрока {nickname} отклонена.", ephemeral=True)
class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Подать заявку", style=discord.ButtonStyle.primary, custom_id="submit_application")
    async def submit_application(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Создаем модальное окно для ввода данных заявки
        modal = ApplicationModal()
        await interaction.response.send_modal(modal)

class ApplicationModal(discord.ui.Modal, title="Заявка на сервер"):
    nickname = discord.ui.TextInput(label="Ваш никнейм", placeholder="Введите ваш игровой никнейм", required=True)
    age = discord.ui.TextInput(label="Ваш возраст", placeholder="Введите ваш возраст", required=True)
    about = discord.ui.TextInput(label="О себе", style=discord.TextStyle.paragraph, placeholder="Расскажите немного о себе", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            embed = discord.Embed(
                title="Новая заявка на сервер",
                description=f"От пользователя {interaction.user.mention}",
                color=discord.Color.blue(),
                timestamp=datetime.datetime.utcnow()
            )
            embed.add_field(name="Никнейм", value=self.nickname.value, inline=False)
            embed.add_field(name="Возраст", value=self.age.value, inline=False)
            embed.add_field(name="О себе", value=self.about.value, inline=False)

            # Отправляем заявку в канал для рассмотрения (замените ID на нужный)
            channel = interaction.guild.get_channel(1299843186306580541)
            await channel.send(embed=embed, view=ApplicationResponseView())

            await interaction.response.send_message("Ваша заявка успешно отправлена на рассмотрение!", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message("Произошла ошибка при отправке заявки. Пожалуйста, обратитесь к администратору.", ephemeral=True)

class TicketCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="create_ticket_menu", description="Создать меню подачи заявок в текущем канале")
    @app_commands.default_permissions(administrator=True)
    async def create_ticket_menu(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="Подача заявки на сервер",
            description="Нажмите на кнопку ниже, чтобы подать заявку на сервер.",
            color=discord.Color.blue()
        )
        await interaction.channel.send(embed=embed, view=TicketView())
        await interaction.response.send_message("Меню для подачи заявок успешно создано!", ephemeral=True)

async def setup(bot):
    await bot.add_cog(TicketCog(bot))
