# Python libs imports
import telebot, smtplib, uuid, sqlite3
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Custom imports
from config import TOKEN, SMTP_SRV, SMTP_PORT, SENDER, SENDER_PWD, RECIPIENT
bot = telebot.TeleBot(TOKEN)

# Connection to database
conn = sqlite3.connect('tickets.db', check_same_thread=False)
cursor = conn.cursor()

# If table not exists
cursor.execute('''
CREATE TABLE IF NOT EXISTS tickets (
    id TEXT PRIMARY KEY,
    user_id INTEGER,
    problem TEXT,
    status TEXT,
    history TEXT
)
''')
conn.commit()


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
    cursor.execute("INSERT INTO tickets (id, user_id, problem, status, history) VALUES (?, ?, ?, ?, ?)",
                   (ticket_id, user_id, problem, 'open', problem))
    conn.commit()

    bot.reply_to(message, f"Тикет создан! Ваш ID: {ticket_id}")
    send_email(f"Ticket #{ticket_id} открыт", f"User ID: {user_id}\nProblem: {problem}")


# New messages in open ticket
@bot.message_handler(func=lambda message: message.text and not message.text.startswith('/'))
def add_message_to_ticket(message):
    user_id = message.from_user.id
    cursor.execute("SELECT id, history FROM tickets WHERE user_id = ? AND status = 'open'", (user_id,))
    ticket = cursor.fetchone()

    if ticket:
        ticket_id, history = ticket
        new_history = history + f"\nUser:{message.text}"
        cursor.execute("UPDATE tickets SET history = ? WHERE id = ?", (new_history, ticket_id))
        conn.commit()
        bot.reply_to(message, "Сообщение добавлено к тикету.")
        send_email(f"Update on Ticket #{ticket_id}", f"User ID: {user_id}\nMessage: {message.text}")
    else:
        bot.reply_to(message, "У вас нет открытых тикетов. Откройте новый с помощью команды /ticket.")


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


bot.polling(none_stop=True)
