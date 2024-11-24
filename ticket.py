import discord
from discord.ext import commands
from discord import app_commands
import datetime
import json
import mcrcon

# Импортируем необходимые константы и функции из основного файла бота
from bot import RCON_HOST, RCON_PORT, RCON_PASSWORD, update_whitelist
from ticket_db import init_db, user_has_ticket, add_ticket, remove_ticket

# Инициализируем базу данных при запуске
init_db()

REQUIRED_ROLE_ID = 1300175482196590683

def has_required_role():
    def predicate(interaction: discord.Interaction):
        return any(role.id == REQUIRED_ROLE_ID for role in interaction.user.roles)
    return app_commands.check(predicate)

class ApplicationResponseView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Принять", style=discord.ButtonStyle.green, custom_id="accept_application")
    @has_required_role()
    async def accept_application(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = interaction.message.embeds[0]
        nickname = next(field.value for field in embed.fields if field.name == "Никнейм")
        user_id = int(embed.description.split()[-1][2:-1])  # Извлекаем ID пользователя из описания

        try:
            # Добавляем никнейм в вайтлист на сервере
            try:
                with mcrcon.MCRcon(RCON_HOST, RCON_PASSWORD, RCON_PORT) as mcr:
                    response = mcr.command(f"easywl add {nickname}")
                    print(f"RCON: {response}")
            except Exception as rcon_error:
                print(f"Ошибка при добавлении в вайтлист через RCON: {rcon_error}")
                raise

            # Обновляем эмбед
            embed.color = discord.Color.green()
            embed.set_footer(text=f"Принята администратором {interaction.user.name}")
            await interaction.message.edit(embed=embed, view=None)

            # Удаляем запись о тикете из базы данных
            remove_ticket(user_id)
            await interaction.response.send_message(f"Заявка игрока {nickname} принята и добавлена в вайтлист.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"Произошла ошибка при принятии заявки: {str(e)}", ephemeral=True)

    @discord.ui.button(label="Отклонить", style=discord.ButtonStyle.red, custom_id="reject_application")
    @has_required_role()
    async def reject_application(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = interaction.message.embeds[0]
        nickname = next(field.value for field in embed.fields if field.name == "Никнейм")
        user_id = int(embed.description.split()[-1][2:-1])  # Извлекаем ID пользователя из описания

        # Обновляем эмбед
        embed.color = discord.Color.red()
        embed.set_footer(text=f"Отклонена администратором {interaction.user.name}")
        await interaction.message.edit(embed=embed, view=None)

        # Удаляем запись о тикете из базы данных
        remove_ticket(user_id)
        await interaction.response.send_message(f"Заявка игрока {nickname} отклонена.", ephemeral=True)

class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Подать заявку", style=discord.ButtonStyle.primary, custom_id="submit_application")
    async def submit_application(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Проверяем, есть ли уже открытый тикет у пользователя
        if user_has_ticket(interaction.user.id):
            await interaction.response.send_message("У вас уже есть открытая заявка. Пожалуйста, дождитесь её рассмотрения.", ephemeral=True)
            return
        # Создаем модальное окно для ввода данных заявки
        modal = ApplicationModal()
        await interaction.response.send_modal(modal)

class ApplicationModal(discord.ui.Modal, title="Заявка на сервер"):
    nickname = discord.ui.TextInput(label="Ваш никнейм", placeholder="Введите ваш игровой никнейм", required=True)
    age = discord.ui.TextInput(label="Ваш возраст", placeholder="Введите ваш возраст", required=True)
    reason = discord.ui.TextInput(label="Почему вы хотите играть на нашем сервере?", style=discord.TextStyle.paragraph, required=True)

    async def on_submit(self, interaction: discord.Interaction):
        # Создаем эмбед с информацией о заявке
        embed = discord.Embed(title="Новая заявка на сервер", description=f"От пользователя {interaction.user.mention}", color=discord.Color.blue())
        embed.add_field(name="Никнейм", value=self.nickname.value, inline=False)
        embed.add_field(name="Возраст", value=self.age.value, inline=False)
        embed.add_field(name="Причина", value=self.reason.value, inline=False)
        embed.set_footer(text="Ожидает рассмотрения")

        # Отправляем заявку в канал для рассмотрения
        channel = interaction.client.get_channel(1299843186306580541)  # Обновленный ID канала для заявок
        await channel.send(embed=embed, view=ApplicationResponseView())

        # Добавляем запись о тикете в базу данных
        add_ticket(interaction.user.id, datetime.datetime.now())

        await interaction.response.send_message("Ваша заявка успешно отправлена на рассмотрение.", ephemeral=True)
class TicketCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="create_ticket_menu", description="Создать меню подачи заявок в указанном канале")
    @app_commands.default_permissions(administrator=True)
    @has_required_role()
    async def create_ticket_menu(self, interaction: discord.Interaction):
        embed = discord.Embed(title="Подача заявки на сервер", description="Нажмите на кнопку ниже, чтобы подать заявку на вступление на сервер.", color=discord.Color.blue())
        await interaction.channel.send(embed=embed, view=TicketView())
        await interaction.response.send_message("Меню подачи заявок создано.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(TicketCog(bot))