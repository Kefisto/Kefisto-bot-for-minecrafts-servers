import discord
from discord.ext import commands
from discord import app_commands
import datetime
import json
import mcrcon
from functools import wraps

# Импортируем необходимые константы и функции из основного файла бота
from bot import JSON_FILE, RCON_HOST, RCON_PORT, RCON_PASSWORD, update_whitelist

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

        try:
            # Добавляем никнейм в JSON файл
            with open(JSON_FILE, 'r+', encoding='utf-8') as f:
                usernames = json.load(f)
                if nickname not in usernames:
                    usernames.append(nickname)
                    f.seek(0)
                    json.dump(usernames, f, ensure_ascii=False, indent=4)
                    f.truncate()

            # Добавляем только этот никнейм в вайтлист на сервере
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

            await interaction.response.send_message(f"Заявка игрока {nickname} принята и добавлена в вайтлист.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"Произошла ошибка при принятии заявки: {str(e)}", ephemeral=True)

    @discord.ui.button(label="Отклонить", style=discord.ButtonStyle.red, custom_id="reject_application")
    @has_required_role()
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
    birthdate = discord.ui.TextInput(label="Дата рождения", placeholder="Введите в формате дд.мм.гггг", required=True)

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
            embed.add_field(name="Дата рождения", value=self.birthdate.value, inline=False)

            # Отправляем заявку в канал для рассмотрения (замените ID на нужный)
            channel = interaction.guild.get_channel(1299843186306580541)
            await channel.send(embed=embed, view=ApplicationResponseView())

            await interaction.response.send_message("Ваша заявка успешно отправлена на рассмотрение!", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message("Произошла ошибка при отправке заявки. Пожалуйста, обратитесь к администратору.", ephemeral=True)

class TicketCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="create_ticket_menu", description="Создать меню подачи заявок в указанном канале")
    @app_commands.default_permissions(administrator=True)
    @has_required_role()
    async def create_ticket_menu(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        try:
            # Получаем канал по ID
            channel = self.bot.get_channel(1300176870368612463)

            if channel is None:
                await interaction.followup.send("Не удалось найти указанный канал. Пожалуйста, проверьте ID канала.", ephemeral=True)
                return

            # Проверяем права бота в канале
            if not channel.permissions_for(interaction.guild.me).send_messages:
                await interaction.followup.send("У бота нет прав для отправки сообщений в указанный канал.", ephemeral=True)
                return

            embed = discord.Embed(
                title="Подача заявки на сервер",
                description="Нажмите на кнопку ниже, чтобы подать заявку на сервер.",
                color=discord.Color.blue()
            )

            await channel.send(embed=embed, view=TicketView())
            await interaction.followup.send(f"Меню для подачи заявок успешно создано в канале {channel.mention}!", ephemeral=True)

        except discord.HTTPException as e:
            await interaction.followup.send(f"Произошла ошибка при отправке сообщения: {str(e)}", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"Произошла неизвестная ошибка: {str(e)}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(TicketCog(bot))

