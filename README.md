# IPDAppHelperBot

Простой Telegram-бот для поддержки пользователей приложения ИПД: создание тикетов, добавление сообщений и вложений в открытый тикет, закрытие тикетов и быстрый вывод справки.

> Лицензия: GPL-2.0

---

## 🚀 Возможности

- **`/info`** — показать справку по командам.  
- **`/ticket <краткое_описание>`** — создать новый тикет с заголовком.  
- Любое сообщение **без** `/` после создания тикета — добавляется в тикет (в т.ч. вложения: скриншоты, документы с логами).  
- **`/closeticket`** — закрыть текущий тикет.

Тексты подсказок и меню вынесены в **`custom_texts.py`**, что удобно для локализации и редактирования.

---

## 📂 Структура проекта

```aiignore
.
├─ main.py # точка входа бота
├─ custom_texts.py # тексты /info и стартового сообщения
├─ requirements.txt # зависимости Python
├─ Procfile # процесс worker: python main.py (для Heroku/Railway)
└─ LICENSE # GPL-2.0
```

---

## 📋 Требования

- Python **3.10+** (рекомендовано 3.11)  
- Аккаунт и токен **Telegram Bot API**  
- Переменная окружения `TELEGRAM_BOT_TOKEN`

Зависимости устанавливаются из `requirements.txt`.

---

## ⚡ Быстрый старт (локально)

1. Клонируй репозиторий:
   ```bash
   git clone https://github.com/Lesnoy40rt77/IPDAppHelperBot.git
   cd IPDAppHelperBot
   ```
2. Создай и активируй виртуальное окружение:
   ```bash
   python -m venv .venv
   source .venv/bin/activate      # Windows: .venv\Scripts\activate
   ```
3. Установи зависимости:
   ```bash
   pip install -r requirements.txt
   ```
4. Экспортируй токен бота:
   ```bash
   export TELEGRAM_BOT_TOKEN=123456:ABC...
   # Windows PowerShell:
   # $env:TELEGRAM_BOT_TOKEN="123456:ABC..."
   ```
5. Запусти:
   ```bash
   python main.py
   ```
---

## 🔑 Настройка окружения

Рекомендуется хранить секреты в файле `.env` (и добавить его в `.gitignore`):

  ```env
  TELEGRAM_BOT_TOKEN=123456:ABCDEF...
  ```
## ☁️ Деплой

### Heroku / Railway

Проект уже содержит `Procfile` с типом процесса `worker`.

1. Залей репозиторий в новый проект на Heroku или Railway.  
2. В переменных окружения задай `TELEGRAM_BOT_TOKEN`.  
3. Включи процесс `worker` (`python main.py`).  

---

### VPS / сервер

1. Установи Python и создай виртуальное окружение.  
2. Установи зависимости:
  ```bash
   pip install -r requirements.txt
  ```
3. Добавь переменную окружения `TELEGRAM_BOT_TOKEN` (в `.env` или systemd).
4. Настрой systemd-юнит или supervisor для автозапуска.

Пример systemd-юнита:
  ```ini
  [Unit]
  Description=IPDAppHelperBot
  After=network.target

  [Service]
  User=botuser
  WorkingDirectory=/home/botuser/IPDAppHelperBot
  Environment="TELEGRAM_BOT_TOKEN=123456:ABC..."
  ExecStart=/home/botuser/IPDAppHelperBot/.venv/bin/python main.py
  Restart=always

  [Install]
  WantedBy=multi-user.target
  ```

## 🛠️ Логи и диагностика

- Проверь, что переменная окружения **`TELEGRAM_BOT_TOKEN`** действительно подхватывается процессом.  
- Убедись, что бот в Telegram принимает вложения (по умолчанию они добавляются в тикет).  

---

## 📌 Доработки / планы

- Хранение тикетов в БД (SQLite/PostgreSQL).  
- Команда `/status` — список открытых тикетов.  
- Разграничение доступа (админы / операторы).  
- Локализация RU/EN через конфигурацию.  

---

## 🤝 Вклад

Pull requests и issues приветствуются.  
Перед отправкой PR проверь стиль и запусти линтеры/тесты (если будут добавлены).  

---

## 📜 Лицензия

Проект распространяется под лицензией **GPL-2.0**.  
См. файл [LICENSE](./LICENSE).

