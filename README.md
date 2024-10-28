# Discord Ticket For Minecraft Server Bot

Этот бот для Discord предназначен для управления заявками на сервер Minecraft. Он позволяет пользователям подавать заявки, а администраторам - рассматривать их и управлять вайтлистом сервера.

## Основные функции

- Создание меню для подачи заявок
- Подача заявок пользователями через модальное окно
- Рассмотрение заявок администраторами
- Автоматическое обновление вайтлиста Minecraft сервера
- Команды для добавления и удаления игроков из вайтлиста

## Установка

1. Клонируйте репозиторий:
  git clone https://github.com/kefisto/Kefisto-bot-for-minecrafts-servers.git

2. Перейдите в директорию проекта:
   cd Kefisto-bot-for-minecrafts-servers

3. Установите зависимости:z
   pip install -r requirements.txt

4. Укажите 
DISCORD_TOKEN=your_discord_bot_token

RCON_HOST=your_minecraft_server_ip

RCON_PORT=your_rcon_port

RCON_PASSWORD=your_rcon_password

В bot.py

channel = self.bot.get_channel(1300176870368612463)
    В ticket.py

5. Запустите бота:
    python bot.py

## Использование

- Используйте команду `/create_ticket_menu` для создания меню подачи заявок в указанном канале.
- Пользователи могут подавать заявки, нажав на кнопку "Подать заявку" и заполнив форму.
- Администраторы могут принимать или отклонять заявки в специальном канале.
- Используйте команды `/addtowhitelist` и `/removefromwhitelist` для ручного управления вайтлистом.

## Требования

См. файл `requirements.txt` для списка необходимых Python пакетов.

Требуется плагин easywhitelist на сервере для корректрой работы

## Лицензия

Этот проект распространяется под лицензией Apache. Подробности см. в файле LICENSE.
