import telebot
from telebot import types
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

API_TOKEN = 'YOUR BOT API TOKEN' # Replace with your bot's API token
GROUP_CHAT_ID = -100YOUR_GROUP_ID # Replace with your group chat ID

bot = telebot.TeleBot(API_TOKEN)

admins = [ADMIN_ID,]  # Replace with actual admin IDs
topics = {
    "TOPICS": TOPICS_Id,
}

topics = dict(sorted(topics.items()))
user_data = {}
reply_data = {}

@bot.message_handler(commands=['start'])
def send_welcome(message):
    if message.text.startswith("/start reply_"):
        handle_deep_link_reply(message)
    else:
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("Start", callback_data="start"))
        bot.send_message(
            message.chat.id,
            "Welcome to the Onto The Light Community.\n\nThis's a safe space to share your struggles, secrets, testimonies and more anonymously to a community of supportive individuals.\n\nClick on start to begin sharing... ",
            reply_markup=markup
        )

@bot.callback_query_handler(func=lambda call: call.data == "start")
def ask_for_message(call):
    bot.delete_message(call.message.chat.id, call.message.message_id)  # Delete the start button message
    msg = bot.send_message(call.message.chat.id, "Send your message.\nYou can send text, photo, video, or voice.")
    bot.register_next_step_handler(msg, receive_message)

def receive_message(message):
    user_data[message.chat.id] = {'message': message}
    markup = InlineKeyboardMarkup(row_width=2)
    buttons = [InlineKeyboardButton(topic, callback_data=topic) for topic in topics.keys()]

    for i in range(0, len(buttons), 2):
        markup.row(*buttons[i:i + 2])
    markup.add(InlineKeyboardButton("Go Back", callback_data="go_back"))

    topic_msg = bot.send_message(message.chat.id, "Please choose a topic for your message.", reply_markup=markup)
    user_data[message.chat.id]['topic_msg_id'] = topic_msg.message_id

@bot.callback_query_handler(func=lambda call: call.data in topics.keys() or call.data == "go_back")
def preview_message(call):
    if call.data == "go_back":
        ask_for_message(call)
        return

    bot.delete_message(call.message.chat.id, call.message.message_id)  # Delete the topic selection message
    user_data[call.message.chat.id]['topic'] = call.data
    chosen_topic = call.data
    msg = user_data[call.message.chat.id]['message']

    caption = f"#{chosen_topic.replace(' ', '_')}\n" + (msg.caption if msg.caption else "")

    # Preview the message with the correct content type
    if msg.content_type == "text":
        preview_text = caption + msg.text
        preview_msg = bot.send_message(call.message.chat.id, f"Preview:\n\n{preview_text}")
    elif msg.content_type == "photo":
        preview_msg = bot.send_photo(call.message.chat.id, msg.photo[-1].file_id, caption=caption)
    elif msg.content_type == "video":
        preview_msg = bot.send_video(call.message.chat.id, msg.video.file_id, caption=caption)
    elif msg.content_type == "voice":
        preview_msg = bot.send_voice(call.message.chat.id, msg.voice.file_id, caption=caption)
    elif msg.content_type == "audio":
        preview_msg = bot.send_audio(call.message.chat.id, msg.audio.file_id, caption=caption)
    else:
        bot.send_message(call.message.chat.id, "Unsupported message type./start")
        return

    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("Edit", callback_data="edit"))
    markup.add(InlineKeyboardButton("Send", callback_data="send"))
    markup.add(InlineKeyboardButton("Go Back", callback_data="go_back"))
    choice_msg = bot.send_message(call.message.chat.id, "Would you like to edit, send, or go back?", reply_markup=markup)

    user_data[call.message.chat.id]['preview_msg_id'] = preview_msg.message_id
    user_data[call.message.chat.id]['choice_msg_id'] = choice_msg.message_id

@bot.callback_query_handler(func=lambda call: call.data == "edit")
def edit_message(call):
    bot.delete_message(call.message.chat.id, user_data[call.message.chat.id]['preview_msg_id'])  # Delete the preview message
    bot.delete_message(call.message.chat.id, user_data[call.message.chat.id]['choice_msg_id'])  # Delete the edit/send choice message
    msg = bot.send_message(call.message.chat.id, "Please send the edited message. (text, photo, video, or voice).")
    bot.register_next_step_handler(msg, receive_message)

@bot.callback_query_handler(func=lambda call: call.data == "send")
def send_to_admin(call):
    bot.delete_message(call.message.chat.id, user_data[call.message.chat.id]['preview_msg_id'])  # Delete the preview message
    bot.delete_message(call.message.chat.id, user_data[call.message.chat.id]['choice_msg_id'])  # Delete the edit/send choice message
    user_message = user_data[call.message.chat.id]['message']
    topic = user_data[call.message.chat.id]['topic']
    caption = f"#{topic.replace(' ', '_')}\n\n" + (user_message.caption if user_message.caption else "")

    for admin_id in admins:
        if user_message.content_type == "text":
            bot.send_message(admin_id, f"New message for approval:\n\n{caption + user_message.text}")
        elif user_message.content_type == "photo":
            bot.send_photo(admin_id, user_message.photo[-1].file_id, caption=caption)
        elif user_message.content_type == "video":
            bot.send_video(admin_id, user_message.video.file_id, caption=caption)
        elif user_message.content_type == "voice":
            bot.send_voice(admin_id, user_message.voice.file_id, caption=caption)
        elif user_message.content_type == "audio":
            bot.send_audio(admin_id, user_message.audio.file_id, caption=caption)

        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("Approve", callback_data=f"approve_{call.message.chat.id}"))
        markup.add(InlineKeyboardButton("Decline", callback_data=f"decline_{call.message.chat.id}"))
        bot.send_message(admin_id, "Approve or Decline?", reply_markup=markup)

    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("Go Back", callback_data="go_back"))
    bot.send_message(
    call.message.chat.id,
    "Your message has been sent for approval.\n\nOnce your story is posted to the community (@OntoTheLight) we'll send you a notification here so that you can read and listen to feedbacks from the community.\n\nThank you for your patience and for sharing with us. ",
    reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("approve_"))
def approve_message(call):
    bot.delete_message(call.message.chat.id, call.message.message_id)
    user_id = int(call.data.split("_")[1])
    user_message = user_data[user_id]['message']
    topic = user_data[user_id]['topic']
    message_thread_id = topics[topic]
    group_msg = None  # Initialize group_msg to ensure it's in scope

    try:
        if user_message.content_type == "text":
            group_msg = bot.send_message(
                GROUP_CHAT_ID,
                f"{user_message.text}",
                message_thread_id=message_thread_id
            )
        elif user_message.content_type == "photo":
            group_msg = bot.send_photo(
                GROUP_CHAT_ID,
                user_message.photo[-1].file_id,
                caption=(user_message.caption if user_message.caption else ""),
                message_thread_id=message_thread_id
            )
        elif user_message.content_type == "video":
            group_msg = bot.send_video(
                GROUP_CHAT_ID,
                user_message.video.file_id,
                caption= (user_message.caption if user_message.caption else ""),
                message_thread_id=message_thread_id
            )
        elif user_message.content_type == "voice":
            group_msg = bot.send_voice(
                GROUP_CHAT_ID,
                user_message.voice.file_id,
                caption= (user_message.caption if user_message.caption else ""),
                message_thread_id=message_thread_id
            )
        elif user_message.content_type == "audio":
            group_msg = bot.send_audio(
                GROUP_CHAT_ID,
                user_message.audio.file_id,
                caption= (user_message.caption if user_message.caption else ""),
                message_thread_id=message_thread_id
            )
        for admin_id in admins:
            if admin_id != call.from_user.id:
                bot.send_message(admin_id, "The message has been posted to the group by another admin.")


    except Exception as e:
        bot.send_message(call.message.chat.id, f"Failed to send message: {e}")

    if group_msg:
        reply_markup = InlineKeyboardMarkup()
        reply_markup.add(InlineKeyboardButton(
            "Answer Anonymously",
            url=f"https://t.me/ontothelightbot?start=reply_{group_msg.message_id}"
        ))


    bot.edit_message_reply_markup(GROUP_CHAT_ID, group_msg.message_id, reply_markup=reply_markup)
    message_link = f"https://t.me/c/2248181172/{group_msg.message_id}"
    # Send the confirmation message with the link to the user
    #bot.send_message(user_id, f"Your Message Has Been Approved and Posted.\n\n{message_link}")
    bot.send_message(
        user_id,f"Tour message has been approved. \n\nSee Message: <a href='https://t.me/c/2248181172/{group_msg.message_id}'>click here</a>",
        parse_mode='HTML')


# Handle start command with reply deep link
@bot.message_handler(commands=['start'])
def handle_start(message):
    if len(message.text.split()) > 1 and message.text.split()[1].startswith('reply_'):
        handle_deep_link_reply(message)
    else:
        bot.send_message(message.chat.id, "Welcome! Send any message, and others can reply to it anonymously.")

def handle_deep_link_reply(message):
    try:
        # Extract the message ID from the deep link
        sent_message_id = int(message.text.split("_")[-1])

        # Copy the touched message to the user's chat to show them what they are replying to
        bot.copy_message(message.chat.id, GROUP_CHAT_ID, sent_message_id)

        bot.send_message(
            message.chat.id,
            "This is the message you are replying to anonymously. Please send your reply."
        )

        # Register the next step to handle the user's reply
        bot.register_next_step_handler(message, get_reply_content, sent_message_id)

    except Exception as e:
        bot.send_message(message.chat.id, f"Could not retrieve the message: {e}")

def get_reply_content(message, sent_message_id):
    if message.text and message.text.startswith("/start reply_"):
        bot.send_message(message.chat.id, "Please send a /start to send a message.")
        return

    try:
        # Handle the user's reply and forward it to the group chat
        send_reply(message, sent_message_id)

    except Exception as e:
        bot.send_message(message.chat.id, f"Failed to process the reply: {e}")

def send_reply(message, touched_message_id):
    try:
        # Send the reply to the touched message in the group chat
        if message.content_type == "text":
            sent_message = bot.send_message(GROUP_CHAT_ID, message.text, reply_to_message_id=touched_message_id)
        elif message.content_type == "photo":
            sent_message = bot.send_photo(GROUP_CHAT_ID, message.photo[-1].file_id, caption=message.caption, reply_to_message_id=touched_message_id)
        elif message.content_type == "video":
            sent_message = bot.send_video(GROUP_CHAT_ID, message.video.file_id, caption=message.caption, reply_to_message_id=touched_message_id)
        elif message.content_type == "voice":
            sent_message = bot.send_voice(GROUP_CHAT_ID, message.voice.file_id, caption=message.caption, reply_to_message_id=touched_message_id)
        elif message.content_type == "audio":
            sent_message = bot.send_audio(GROUP_CHAT_ID, message.audio.file_id, caption=message.caption, reply_to_message_id=touched_message_id)
        else:
            bot.send_message(message.chat.id, "Unsupported message type. Please try again.")
            return

        # Create an inline keyboard for "Reply Anonymously" button using sent_message_id
        markup = InlineKeyboardMarkup()
        reply_url = f"https://t.me/{bot.get_me().username}?start=reply_{sent_message.message_id}"
        markup.add(InlineKeyboardButton("Reply Anonymously", url=reply_url))

        # Edit the sent message to include the reply button
        bot.edit_message_reply_markup(GROUP_CHAT_ID, sent_message.message_id, reply_markup=markup)

        # Notify the user that their reply was sent
        bot.send_message(
            message.chat.id,
            f'Your reply has been posted anonymously. <a href="https://t.me/c/2248181172/{sent_message.message_id}">See here</a>',
            parse_mode='HTML'
        )

    except Exception as e:
        bot.send_message(message.chat.id, f"Failed to send reply: {e}")



@bot.callback_query_handler(func=lambda call: call.data.startswith("decline_"))
def decline_message(call):
    bot.delete_message(call.message.chat.id, call.message.message_id)
    user_id = int(call.data.split("_")[1])
    bot.send_message(user_id, "Your Message Has Been Declined.")


# Function to dynamically add admins
def add_admin(admin_id):
    if admin_id not in admins:
        admins.append(admin_id)
        return f"Admin with ID {admin_id} added."
    return "Admin Already Exists."


# Function to dynamically add topics
def add_topic(name, thread_id):
    topics[name] = thread_id
    return f"Topic '{name}' added with thread ID {thread_id}."


@bot.message_handler(commands=['add_admin'])
# Command handlers for adding admins and topics dynamically
@bot.message_handler(commands=['add_admin'])
def handle_add_admin(message):
    if message.from_user.id in admins:  # Ensure only existing admins can add new ones
        try:
            new_admin_id = int(message.text.split()[1])
            response = add_admin(new_admin_id)
        except (IndexError, ValueError):
            response = "Usage: /add_admin <admin_id>"
    else:
        response = "You Are Not an Admin!!!."
    bot.reply_to(message, response)

@bot.message_handler(commands=['add_topic'])
def handle_add_topic(message):
    if message.from_user.id in admins:  # Ensure only existing admins can add topics
        try:
            args = message.text.split()
            name = args[1]
            thread_id = int(args[2])
            response = add_topic(name, thread_id)
        except (IndexError, ValueError):
            response = "Usage: /add_topic <topic_name> <thread_id>"
    else:
        response = "You Are Not an Admin !!!"
    bot.reply_to(message, response)

bot.infinity_polling()

