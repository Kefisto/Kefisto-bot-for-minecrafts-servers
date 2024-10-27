import asyncio
import discord
from discord.ext import commands
from discord import app_commands
import mcrcon
import json

# Настройка бота
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.messages = True

class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix='!', intents=intents)

    async def setup_hook(self):
        await self.load_extension('ticket')
        await self.tree.sync()
        print("Команды синхронизированы")

    async def on_ready(self):
        print(f'Бот {self.user} готов к работе')
# Создание экземпляра бота
bot = MyBot()

# Настройки RCON
RCON_HOST = '89.208.14.107'
RCON_PORT = 24606
RCON_PASSWORD = 'awjfawkjgawt'

# Путь к JSON файлу
JSON_FILE = 'usernames.json'

# ID канала форума
FORUM_CHANNEL_ID = 1287163565521899621

async def update_whitelist():
    try:
        # Читаем ники из JSON файла
        with open(JSON_FILE, 'r', encoding='utf-8') as f:
            usernames = json.load(f)

        # Подключаемся к серверу через RCON
        with mcrcon.MCRcon(RCON_HOST, RCON_PASSWORD, RCON_PORT) as mcr:
            # Очищаем текущий вайтлист
            mcr.command("easywl clear")
            print("Вайтлист очищен")

            # Добавляем каждый ник в вайтлист
            for username in usernames:
                response = mcr.command(f"easywl add {username}")
                print(f"RCON: {response}")

        print("Вайтлист успешно обновлен")
    except Exception as e:
        print(f"Ошибка при обновлении вайтлиста: {e}")

def extract_username(message_content):
    lines = message_content.split('\n')
    for i, line in enumerate(lines):
        if line.strip().startswith('2'):
            if i + 2 < len(lines):  # Проверяем, есть ли третья строка
                username_line = lines[i + 2].strip()  # Берем третью строку
                # Удаляем символы типа '.' и ')'
                username = ''.join(char for char in username_line if char not in '.)')
                return username.strip()
    return None

async def process_thread(thread, usernames, accepted_tag_id):
    message_count = 0
    is_accepted = any(tag.id == accepted_tag_id for tag in thread.applied_tags)

    if not is_accepted:
        print(f"  Ветка не имеет тега 'принят', пропускаем")
        return

    async for message in thread.history(limit=None):
        message_count += 1
        username = extract_username(message.content)
        if username:
            usernames.add(username)
            print(f"  Найден принятый ник: {username}")
    print(f"  Обработано сообщений в ветке: {message_count}")

async def scan_forum_channel(bot):
    forum_channel = bot.get_channel(FORUM_CHANNEL_ID)
    if not forum_channel:
        print(f"Ошибка: канал с ID {FORUM_CHANNEL_ID} не найден")
        return

    accepted_tag = discord.utils.get(forum_channel.available_tags, name="принят")
    if not accepted_tag:
        print("Ошибка: тег 'принят' не найден")
        return

    usernames = set()
    threads = [thread async for thread in forum_channel.archived_threads(limit=None)]
    threads.extend([thread for thread in forum_channel.threads])

    for thread in threads:
        print(f"Обработка ветки: {thread.name}")
        await process_thread(thread, usernames, accepted_tag.id)

    print(f"Всего найдено уникальных ников: {len(usernames)}")

    with open(JSON_FILE, 'w', encoding='utf-8') as f:
        json.dump(list(usernames), f, ensure_ascii=False, indent=2)

    print(f"Ники сохранены в файл {JSON_FILE}")
    await update_whitelist()

@bot.tree.command(name="addtowhitelist", description="Добавить игрока в вайтлист")
@app_commands.describe(username="Никнейм игрока для добавления в вайтлист")
async def add_to_whitelist(interaction: discord.Interaction, username: str):
    await interaction.response.defer(ephemeral=True)
    try:
        with open(JSON_FILE, 'r', encoding='utf-8') as f:
            usernames = json.load(f)

        if username in usernames:
            await interaction.followup.send(f"Игрок {username} уже в вайтлисте.", ephemeral=True)
            return

        usernames.append(username)

        with open(JSON_FILE, 'w', encoding='utf-8') as f:
            json.dump(usernames, f, ensure_ascii=False, indent=2)
        with mcrcon.MCRcon(RCON_HOST, RCON_PASSWORD, RCON_PORT) as mcr:
            response = mcr.command(f"easywl add {username}")
            print(f"RCON: {response}")

        await interaction.followup.send(f"Игрок {username} успешно добавлен в вайтлист.", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"Произошла ошибка при добавлении игрока {username} в вайтлист: {str(e)}", ephemeral=True)

@bot.tree.command(name="rescan", description="Повторное сканирование форума")
async def rescan_command(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    await scan_forum_channel(bot)
    await interaction.followup.send("Сканирование завершено. Результаты сохранены и выведены в консоль. Вайтлист обновлен.", ephemeral=True)
@bot.tree.command(name="removefromwhitelist", description="Удалить игрока из вайтлиста")
@app_commands.describe(username="Никнейм игрока для удаления из вайтлиста")
async def remove_from_whitelist(interaction: discord.Interaction, username: str):
    await interaction.response.defer(ephemeral=True)
    try:
        with open(JSON_FILE, 'r', encoding='utf-8') as f:
            usernames = json.load(f)

        if username not in usernames:
            await interaction.followup.send(f"Игрок {username} не найден в вайтлисте.", ephemeral=True)
            return

        usernames.remove(username)

        with open(JSON_FILE, 'w', encoding='utf-8') as f:
            json.dump(usernames, f, ensure_ascii=False, indent=2)
        with mcrcon.MCRcon(RCON_HOST, RCON_PASSWORD, RCON_PORT) as mcr:
            response = mcr.command(f"easywl remove {username}")
            print(f"RCON: {response}")

        await interaction.followup.send(f"Игрок {username} успешно удален из вайтлиста.", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"Произошла ошибка при удалении игрока {username} из вайтлиста: {str(e)}", ephemeral=True)

@bot.command()
@commands.is_owner()
async def sync_commands(ctx):
    print("Начало синхронизации команд")
    synced = await bot.tree.sync()
    print(f"Синхронизировано {len(synced)} команд")
    await ctx.send(f"Синхронизировано {len(synced)} команд")

@bot.event
async def on_connect():
    print("Бот подключен к Discord")

async def main():
    async with bot:
        await bot.start('MTI5OTQ0MTI2NjY2ODMzOTI1MA.G37wU-.ssHGG8qxs96ArdQ5KhPM4bcdHCTuKY5CqXEpQc')

# Запуск бота
if __name__ == "__main__":
    asyncio.run(main())        

