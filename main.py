# Python libs imports
from email.header import decode_header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

import email
import imaplib
import re
import smtplib
import sqlite3
import telebot
import threading
import time
import uuid
import os

# Custom imports
from config import TOKEN, SMTP_SRV, SMTP_PORT, SENDER, SENDER_PWD, RECIPIENT, IMAP
from custom_texts import START, INFO

bot = telebot.TeleBot(TOKEN)

# Directory for files
UPLOAD_DIR = 'uploads'
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Connection to database
conn = sqlite3.connect('tickets.db', check_same_thread=False)
cursor = conn.cursor()

# If table not exists
cursor.execute('''
CREATE TABLE IF NOT EXISTS tickets (
    id TEXT PRIMARY KEY,
    user_id INTEGER,
    problem TEXT,
    status TEXT
)
''')
conn.commit()


# Start command
@bot.message_handler(commands=['start'])
def start_message(message):
    bot.send_message(message.chat.id, START)


# Info command
@bot.message_handler(commands=['info'])
def info_message(message):
    bot.send_message(message.chat.id, INFO)


# Open new ticket
@bot.message_handler(commands=['ticket'])
def create_ticket(message):
    user_id = message.from_user.id
    problem = message.text[8:].strip()

    if not problem:
        bot.reply_to(message, "Пожалуйста, кратно опишите вашу проблему после команды /ticket.")
        return

    # Check if ticket already there
    cursor.execute("SELECT id FROM tickets WHERE user_id = ? AND status = 'open'", (user_id,))
    open_ticket = cursor.fetchone()
    if open_ticket:
        bot.reply_to(message,
                     f"У вас уже есть открытый тикет с ID: {open_ticket[0]}. Закройте его перед созданием нового.")
        return

    # If not - open a new one
    ticket_id = str(uuid.uuid4())[:8]
    cursor.execute("INSERT INTO tickets (id, user_id, problem, status) VALUES (?, ?, ?, ?, ?)",
                   (ticket_id, user_id, problem, 'open', problem))
    conn.commit()

    bot.reply_to(message, f"Тикет создан! Ваш ID: {ticket_id}")
    send_email(f"Ticket #{ticket_id} открыт", f"User ID: {user_id}\nProblem: {problem}")


# Close ticket
@bot.message_handler(commands=['closeticket'])
def close_ticket(message):
    user_id = message.from_user.id
    cursor.execute("SELECT id FROM tickets WHERE user_id = ? AND status = 'open'", (user_id,))
    ticket = cursor.fetchone()

    if ticket:
        ticket_id = ticket[0]
        cursor.execute("UPDATE tickets SET status = 'closed' WHERE id = ?", (ticket_id,))
        conn.commit()
        bot.reply_to(message, f"Тикет #{ticket_id} закрыт.")
        send_email(f"Ticket #{ticket_id} закрыт", f"User ID: {user_id}\nTicket ID: {ticket_id} has been closed.")
    else:
        bot.reply_to(message, "У вас нет открытых тикетов.")


# Text messages hadler
@bot.message_handler(content_types=['text'])
def handle_text(message):
    # Checking for open tickets
    user_id = message.from_user.id
    cursor.execute("SELECT id FROM tickets WHERE user_id = ? AND status = 'open'", (user_id,))
    ticket = cursor.fetchone()

    if not ticket:
        bot.reply_to(message, "У вас нет открытых тикетов. Откройте новый с помощью команды /ticket.")
        return

    text_content = message.text
    ticket_id = ticket[0]
    bot.reply_to(message, "Текстовое сообщение добавлено к тикету.")
    send_email(f"Update on Ticket #{ticket_id}", f"User ID: {user_id}\nMessage: {text_content}")


# Documents handler
@bot.message_handler(content_types=['document'])
def handle_document(message):
    # Checking for open tickets
    user_id = message.from_user.id
    cursor.execute("SELECT id FROM tickets WHERE user_id = ? AND status = 'open'", (user_id,))
    ticket = cursor.fetchone()

    if not ticket:
        bot.reply_to(message, "У вас нет открытых тикетов. Откройте новый с помощью команды /ticket.")
        return

    # List of files for attachments
    attachments = []
    text_content = message.caption if message.caption else "No additional information"

    # Saving document
    file_info = bot.get_file(message.document.file_id)
    download_file = bot.download_file(file_info.file_path)
    file_path = os.path.join(UPLOAD_DIR, message.document.file_name)

    # Save file and add path to list
    with open(file_path, 'wb') as f:
        f.write(download_file)
    attachments.append(file_path)

    # Send to E-Mail
    ticket_id = ticket[0]
    if send_email_with_attachments(f"Update on Ticket #{ticket_id}", f"User ID: {user_id}\nMessage: {text_content}",
                                   attachments):
        bot.reply_to(message, "Ваш документ прикреплён к тикету.")
    else:
        bot.reply_to(message, "Ошибка отправки. Попробуйте ещё раз или свяжитесь с администратором.")
        print(f"File sending failed: {file_path}, {user_id}")

    # Clean directory
    clean_upload_dir()


@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    # Checking for open tickets
    user_id = message.from_user.id
    cursor.execute("SELECT id FROM tickets WHERE user_id = ? AND status = 'open'", (user_id,))
    ticket = cursor.fetchone()

    if not ticket:
        bot.reply_to(message, "У вас нет открытых тикетов. Откройте новый с помощью команды /ticket.")
        return

    # List of files for attachments
    attachments = []
    text_content = message.caption if message.caption else "No additional information"

    # Get photo
    file_info = bot.get_file(message.photo[-1].file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    file_path = os.path.join(UPLOAD_DIR, f"{message.photo[-1].file_id}.jpg")

    # Save photo and add path to list
    with open(file_path, 'wb') as f:
        f.write(downloaded_file)
    attachments.append(file_path)

    # Send to E-Mail
    ticket_id = ticket[0]
    if send_email_with_attachments(f"Update on Ticket #{ticket_id}", f"User ID: {user_id}\nMessage: {text_content}",
                                   attachments):
        bot.reply_to(message, "Ваш документ прикреплён к тикету.")
    else:
        bot.reply_to(message, "Ошибка отправки. Попробуйте ещё раз или свяжитесь с администратором.")
        print(f"File sending failed: {file_path}, {user_id}")

    # Clean directory
    clean_upload_dir()


# Unknown command
@bot.message_handler(func=lambda message: message.text.startswith('/'))
def unknown_command(message):
    bot.reply_to(message, "Неизвестная команда. Список команд: /info")


@bot.message_handler(content_types=['audio', 'video', 'voice', 'sticker', 'location', 'contact'])
def unsupported_file_type(message):
    bot.reply_to(message, "Неверный формат файла. Доступные форматы: фото, документ")


# E-Mail sender
def send_email(subject, body):
    try:
        msg = MIMEMultipart()
        msg['From'] = SENDER
        msg['To'] = RECIPIENT
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        with smtplib.SMTP(SMTP_SRV, SMTP_PORT) as server:
            server.starttls()
            server.login(SENDER, SENDER_PWD)
            server.sendmail(SENDER, RECIPIENT, msg.as_string())
            server.quit()
        return True
    except Exception as e:
        print(f"Exception while sending message: {e}")
        return False


# E-Mail with attachments sender
def send_email_with_attachments(subject, body, attachments):
    try:
        msg = MIMEMultipart()
        msg['From'] = SENDER
        msg['To'] = RECIPIENT
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        # Add all files as attachments
        for file_path in attachments:
            with open(file_path, 'rb') as f:
                part = MIMEApplication(f.read(), Name=os.path.basename(file_path))
                part['Content-Disposition'] = f'attachment; filename="{os.path.basename(file_path)}"'
                msg.attach(part)

        # Send the mail
        with smtplib.SMTP(SMTP_SRV, SMTP_PORT) as server:
            server.starttls()
            server.login(SENDER, SENDER_PWD)
            server.sendmail(SENDER, RECIPIENT, msg.as_string())

        return True
    except Exception as e:
        print(f"Error in sending mail with attachment: {e}")
        return False


# Checking the mail for replies on open tickets
def check_mail():
    try:
        # connecting to IMAP
        mail = imaplib.IMAP4_SSL(IMAP)
        mail.login(SENDER, SENDER_PWD)
        mail.select("inbox")

        # searching for unread
        status, messages = mail.search(None, 'UNSEEN')
        mail_ids = messages[0].split()

        for mail_id in mail_ids:
            # Receiving and parsing the letter
            status, data = mail.fetch(mail_id, '(RFC822)')
            msg = email.message_from_bytes(data[0][1])

            # Recieving the subject of letter
            subject, encoding = decode_header(msg["Subject"])[0]
            if isinstance(subject, bytes):
                subject = subject.decode(encoding or 'utf-8')
            body = ""

            # Checking if the ticket was closed from the support side
            if "CLOSE_TICKET" in subject:
                # Getting UUID from the subject
                ticket_id_match = re.search(r'#([a-f0-9]{8})', subject)
                if ticket_id_match:
                    ticket_id = ticket_id_match.group(1)
                    # closing the ticket in DB
                    cursor.execute("UPDATE tickets SET status = 'closed' WHERE id = ?", (ticket_id,))
                    conn.commit()
                    print(f"Ticket #{ticket_id} closed from support side")

                    # Notifying the user about his ticket being closed
                    cursor.execute("SELECT user_id FROM tickets WHERE id = ?", (ticket_id,))
                    result = cursor.fetchone()
                    if result:
                        user_id = result[0]
                        bot.send_message(user_id, f"Ваш тикет #{ticket_id} был закрыт поддержкой.")
                    continue

            # Pulling out the body
            if msg.is_multipart():
                for part in msg.walk():
                    content_type = part.get_content_type()
                    content_disposition = str(part.get("Content-Disposition"))

                    if content_type == "text/plain" and "attachment" not in content_disposition:
                        body = part.get_payload(decode=True).decode()
            else:
                body = msg.get_payload(decode=True).decode()

            # Getting UUID of the ticket from the subject (supposedly UUID is an 8-symbol code)
            ticket_id_match = re.search(r'#([a-f0-9]{8})', subject)
            if not ticket_id_match:
                print("UUID of the ticket is not found in the subject")
                continue

            ticket_id = ticket_id_match.group(1)  # Pulling UUID without "#"
            print(f"UUID found: {ticket_id}")

            # Searching for user_id in DB based on UUID of ticket
            cursor.execute("SELECT user_id FROM tickets WHERE id = ? AND status = 'open'", (ticket_id,))
            result = cursor.fetchone()

            if result:
                user_id = result[0]
                # re-sending the message to user_id in Telegram
                bot.send_message(user_id, f"Новое сообщение по Вашему тикету {ticket_id}\nТема: {subject}\n\n{body}")
                print(f"Message sent to {user_id}")
            else:
                print(f"Ticket with UUID {ticket_id} is not found or is closed")

            # Marking the E-Mail as "Read"
            mail.store(mail_id, '+FLAGS', '\\Seen')

        # closing connection with IMAP
        mail.close()
        mail.logout()
    except Exception as e:
        print(f"Error while checking mail: {e}")


# Cycling through mail every 60 seconds
def mail_check_loop():
    while True:
        check_mail()
        time.sleep(60)


# Directory cleaning func
def clean_upload_dir():
    for filename in os.listdir(UPLOAD_DIR):
        file_path = os.path.join(UPLOAD_DIR, filename)
        try:
            if os.path.isfile(file_path):
                os.remove(file_path)
        except Exception as e:
            print(f"Cannot delete file {file_path}: {e}")


mail_check_thread = threading.Thread(target=mail_check_loop)
mail_check_thread.start()

# Starting the bot
bot.polling(none_stop=True)
