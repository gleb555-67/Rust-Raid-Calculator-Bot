import telebot
from telebot import types
from raid_data import RAID_TARGETS, EXPLOSIVE_RECIPES, calculate_raid, calculate_step_by_step

from telebot import apihelper
apihelper.proxy = {'https': 'socks5://127.0.0.1:9150'}

TOKEN = "...."
bot = telebot.TeleBot(TOKEN)


def get_main_menu():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("Рассчитать рейд", callback_data="menu:raid"),
        types.InlineKeyboardButton("Крафт взрывчатки", callback_data="menu:craft")
    )
    markup.add(types.InlineKeyboardButton("Цены взрывчатки", callback_data="menu:costs"))
    return markup

def get_raid_menu():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(types.InlineKeyboardButton("СТЕНЫ", callback_data="ignore"))
    markup.row(
        types.InlineKeyboardButton("Дерево", callback_data="raid:wood_wall"),
        types.InlineKeyboardButton("Камень", callback_data="raid:stone_wall")
    )
    markup.row(
        types.InlineKeyboardButton("Металл", callback_data="raid:sheet_wall"),
        types.InlineKeyboardButton("МВК", callback_data="raid:armored_wall")
    )
    markup.add(types.InlineKeyboardButton("ДВЕРИ", callback_data="ignore"))
    markup.row(
        types.InlineKeyboardButton("Дерево", callback_data="raid:wood_door"),
        types.InlineKeyboardButton("Металл", callback_data="raid:sheet_door")
    )
    markup.row(
        types.InlineKeyboardButton("Гараж", callback_data="raid:garage_door"),
        types.InlineKeyboardButton("МВК", callback_data="raid:armored_door")
    )
    markup.add(types.InlineKeyboardButton("В главное меню", callback_data="menu:main"))
    return markup

def get_craft_menu():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("C4", callback_data="craft:c4"),
        types.InlineKeyboardButton("Ракета", callback_data="craft:rocket"),
        types.InlineKeyboardButton("Сачель", callback_data="craft:satchel"),
        types.InlineKeyboardButton("Патрон 5.56", callback_data="craft:ammo")
    )
    markup.add(types.InlineKeyboardButton("В главное меню", callback_data="menu:main"))
    return markup

def get_back_to_menu_kb():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("В главное меню", callback_data="menu:main"))
    return markup

@bot.message_handler(commands=["start"])
def cmd_start(message):
    text = (
        "Rust Raid Calculator\n\n"
        "Бот рассчитает самый выгодный способ рейда и покажет, "
        "сколько и каких компонентов нужно нафармить.\n\n"
        "Выбери действие на кнопках ниже."
    )
    bot.send_message(message.chat.id, text, reply_markup=get_main_menu(), parse_mode="Markdown")

@bot.message_handler(commands=["raid"])
def cmd_raid(message):
    bot.send_message(message.chat.id, "Выбери цель для рейда:", reply_markup=get_raid_menu())

@bot.message_handler(commands=["craft"])
def cmd_craft(message):
    bot.send_message(message.chat.id, "Что будем крафтить?", reply_markup=get_craft_menu())

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    if call.data == "ignore":
        bot.answer_callback_query(call.id)
        return

    if call.data == "menu:main":
        text = "Rust Raid Calculator\n\nВыбери действие на кнопках ниже."
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, 
                              reply_markup=get_main_menu(), parse_mode="Markdown")
        return

    if call.data == "menu:raid":
        bot.edit_message_text("Выбери цель для рейда:", call.message.chat.id, 
                              call.message.message_id, reply_markup=get_raid_menu())
        return

    if call.data == "menu:craft":
        bot.edit_message_text("Что будем крафтить?", call.message.chat.id, 
                              call.message.message_id, reply_markup=get_craft_menu())
        return

    if call.data == "menu:costs":
        text = (
            "Стоимость взрывчатки в чистой сере:\n"
            "C4: 2200\n"
            "Ракета: 1400\n"
            "Сачель: 480\n"
            "Разрывной 5.56: 25\n\n"
            "Остальные компоненты указаны в рецептах."
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, 
                              reply_markup=get_back_to_menu_kb(), parse_mode="Markdown")
        return

    if call.data.startswith("raid:"):
        key = call.data.split(":")[1]
        target = RAID_TARGETS[key]
        result = calculate_raid(target)
        best = result["best"]
        t = best["totals"]

        lines = [f"**{target['name']}**\n"]
        lines.append("**ЛУЧШИЙ СПОСОБ:**" if not best["is_combo"] else "**ЛУЧШИЙ СПОСОБ (комбинация):**")
        lines.append(f"{best['text']}\n")

        lines.append("**Пошаговый план:**")
        lines.append(f"Шаг 1. Нафармить {t['sulfur']:,} серы и {t['charcoal']:,} угля.".replace(",", " "))
        
        if t['gunpowder'] > 0:
            lines.append(f"Шаг 2. Скрафтить {t['gunpowder']:,} пороха (без стола смешивания):".replace(",", " "))
            lines.append(f"  - Потратить {t['gunpowder']*2:,} серы и {t['charcoal']:,} угля.".replace(",", " "))
            if t['extra_sulfur'] > 0:
                lines.append(f"  - Останется {t['extra_sulfur']:,} серы.".replace(",", " "))
            else:
                lines.append("  - Вся сера уйдет на порох.")
        else:
            lines.append("Шаг 2. Порох не требуется.")
            
        lines.append("Шаг 3. Скрафтить взрывчатку из компонентов:")
        if t['extra_sulfur'] > 0:
            lines.append(f"  - Сера: {t['extra_sulfur']:,}".replace(",", " "))
        if t['gunpowder'] > 0:
            lines.append(f"  - Порох: {t['gunpowder']:,}".replace(",", " "))
            
        comp_names = {"metal": "Металл", "cloth": "Ткань", "tech_trash": "Техмусор", "fuel": "Топливо", "metal_pipe": "Мет. трубы", "rope": "Веревка"}
        for k, name in comp_names.items():
            if t.get(k, 0) > 0:
                lines.append(f"  - {name}: {t[k]:,}".replace(",", " "))

        lines.append("\nДругие варианты (по количеству серы):")
        for opt in result["all"]:
            if opt is best: continue
            tag = " (комбо)" if opt["is_combo"] else ""
            lines.append(f"{opt['text']}{tag} — {opt['totals']['sulfur']:,} серы".replace(",", " "))

        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("К целям", callback_data="menu:raid"),
            types.InlineKeyboardButton("В меню", callback_data="menu:main")
        )
        bot.edit_message_text("\n".join(lines), call.message.chat.id, call.message.message_id, 
                              reply_markup=markup, parse_mode="Markdown")
        return

    if call.data.startswith("craft:"):
        key = call.data.split(":")[1]
        recipe = EXPLOSIVE_RECIPES[key]
        t = calculate_step_by_step({key: 1})

        lines = [f"**Рецепт крафта: 1 {recipe['name']}**\n"]
        lines.append(f"Шаг 1. Нафармить {t['sulfur']:,} серы и {t['charcoal']:,} угля.".replace(",", " "))
        
        if t['gunpowder'] > 0:
            lines.append(f"Шаг 2. Скрафтить {t['gunpowder']:,} пороха (без стола смешивания):".replace(",", " "))
            lines.append(f"  - Потратить {t['gunpowder']*2:,} серы и {t['charcoal']:,} угля.".replace(",", " "))
            if t['extra_sulfur'] > 0:
                lines.append(f"  - Останется {t['extra_sulfur']:,} серы.".replace(",", " "))
            else:
                lines.append("  - Вся сера уйдет на порох.")
        else:
            lines.append("Шаг 2. Порох не требуется.")
            
        lines.append("Шаг 3. Скрафтить сам предмет из:")
        if t['extra_sulfur'] > 0:
            lines.append(f"  - Сера: {t['extra_sulfur']:,}".replace(",", " "))
        if t['gunpowder'] > 0:
            lines.append(f"  - Порох: {t['gunpowder']:,}".replace(",", " "))
            
        comp_names = {"metal": "Металл", "cloth": "Ткань", "tech_trash": "Техмусор", "fuel": "Топливо", "metal_pipe": "Мет. трубы", "rope": "Веревка"}
        for k, name in comp_names.items():
            if t.get(k, 0) > 0:
                lines.append(f"  - {name}: {t[k]:,}".replace(",", " "))

        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("К крафту", callback_data="menu:craft"),
            types.InlineKeyboardButton("В меню", callback_data="menu:main")
        )
        bot.edit_message_text("\n".join(lines), call.message.chat.id, call.message.message_id, 
                              reply_markup=markup, parse_mode="Markdown")
        return

@bot.message_handler(content_types=["text"])
def handle_text(message):
    if message.text.startswith("/"):
        bot.reply_to(message, "Неизвестная команда. Нажми /start, чтобы открыть меню.")
        return
    
    bot.reply_to(
        message, 
        "Для удобства пользуйся кнопками. Вызови /start, чтобы открыть главное меню.",
        reply_markup=get_main_menu()
    )

if __name__ == "__main__":
    print("Бот запущен...")
    bot.infinity_polling()
