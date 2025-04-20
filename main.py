from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
import geopy.distance
from geopy.geocoders import Nominatim
import logging

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_TOKEN = '7767809773:AAHMELMnWt61ZtMRKQhl-_fPybZsrMDsfFg'

# Хранение данных пользователя
user_context = {}

# Вопросы и ответы
faq_questions = {
    "q1": {"ru": "🕒 Общий срок исковой давности", "kz": "🕒 Жалпы іс давность мерзімі"},
    "q2": {"ru": "📅 Сроки рассмотрения гражданских дел", "kz": "📅 Азаматтық істерді қарау мерзімі"},
    "q3": {"ru": "⏳ Специальные сроки исковой давности", "kz": "⏳ Іс давностьінің арнайы мерзімдері"},
    "q4": {"ru": "⚖️ Сроки рассмотрения особых категорий дел", "kz": "⚖️ Арнайы санаттағы істерді қарау мерзімдері"},
    "q5": {"ru": "📆 Исчисление процессуальных сроков", "kz": "📆 Процестік мерзімдерді есептеу"},
    "q6": {"ru": "📨 Сроки направления судебных актов", "kz": "📨 Сот актілерін жіберу мерзімдері"},
    "q7": {"ru": "📝 Сроки подачи апелляционной и кассационной жалобы", "kz": "📝 Апелляциялық және кассациялық шағымдарды беру мерзімдері"},
    "q8": {"ru": "🔄 Восстановление пропущенных сроков", "kz": "🔄 Өткізіп жіберілген мерзімдерді қалпына келтіру"},
    "q9": {"ru": "⚡ Сроки исполнения судебных актов", "kz": "⚡ Сот актілерін орындау мерзімдері"},
    "q10": {"ru": "🆕 Пересмотр по новым обстоятельствам", "kz": "🆕 Жаңа немесе қайта ашылан жағдайлар бойынша қайта қарау"},
    "q11": {"ru": "📋 Сроки рассмотрения ходатайств", "kz": "📋 Өтініштерді қарау мерзімдері"},
    "q12": {"ru": "📜 Срок на обращение за судебным приказом", "kz": "📜 Сот бұйрығына жүгіну мерзімі"}
}

faq_answers = {
    "q1": {
        "ru": "Общий срок исковой давности составляет 3 года с момента, когда лицо узнало или должно было узнать о нарушении своего права.",
        "kz": "Жалпы іс давностьі мерзімі адам өз құқығының бұзылғанын білген немесе білуі керек болған күннен бастап 3 жылды құрайды."
    },
    "q2": {
        "ru": "Гражданские дела рассматриваются судом в срок до двух месяцев со дня окончания подготовки дела к судебному разбирательству.",
        "kz": "Азаматтық істер сотта істі сот отырысына дайындауды аяқтаған күннен бастап екі айға дейін қаралады."
    },
    "q3": {
        "ru": "Для отдельных категорий дел законом могут быть установлены иные сроки исковой давности (например, 1 год по спорам о качестве работ).",
        "kz": "Істің жекелеген санаттары үшін заңмен іс давностьінің басқа мерзімдері белгіленуі мүмкін (мысалы, жұмыс сапасы туралы даулар бойынша 1 жыл)."
    },
    "q4": {
        "ru": "• Восстановление на работе, установление отцовства, взыскание алиментов - до 1 месяца\n• Признание забастовок незаконными - 10 рабочих дней\n• Иные категории - специальные сроки по закону",
        "kz": "• Жұмысқа қалпына келтіру, ата-аналықты анықтау, алимент алу - 1 айға дейін\n• Ереуілдерді заңсыз деп тану - 10 жұмыс күні\n• Басқа санаттар - заңда белгіленген арнайы мерзімдер"
    },
    "q5": {
        "ru": "• Начинается на следующий день после даты/события\n• Если последний день - выходной, срок переносится\n• Месячные/годовые сроки оканчиваются в соответствующее число",
        "kz": "• Күн/оқиғадан кейінгі күннен басталады\n• Соңғы күн демалыс күні болса, мерзім кейінге қалдырылады\n• Айлық/жылдық мерзімдер сәйкес күнде аяқталады"
    },
    "q6": {
        "ru": "Копии решений высылаются не позднее 5 дней со дня вынесения решения в окончательной форме.",
        "kz": "Шешімнің көшірмелері шешім қабылданған күннен бастап 5 күн ішінде жіберіледі."
    },
    "q7": {
        "ru": "• Апелляция - 1 месяц со дня вынесения решения\n• Кассация - 6 месяцев со дня вступления акта в силу",
        "kz": "• Апелляция - шешім шығарылған күннен бастап 1 ай\n• Кассация - акт күшіне енген күннен бастап 6 ай"
    },
    "q8": {
        "ru": "Суд может восстановить срок при уважительных причинах пропуска. Заявление рассматривается до истечения срока на обжалование.",
        "kz": "Сот мерзімді өткізіп жіберуге негізді себептер болған жағдайда қалпына келтіре алады. Өтініш шағым беру мерзімі аяқталғанға дейін қаралады."
    },
    "q9": {
        "ru": "• Немедленно - если подлежит немедленному исполнению\n• Обычно - после вступления в законную силу (после срока обжалования)",
        "kz": "• Бірден - егер дереу орындауға жатады\n• Әдетте - заңды күшіне енгеннен кейін (шағым беру мерзімі аяқталғаннан кейін)"
    },
    "q10": {
        "ru": "Заявление может быть подано в течение 3 месяцев со дня, когда лицо узнало о новых обстоятельствах.",
        "kz": "Өтініш жаңа жағдайлар туралы білген күннен бастап 3 ай ішінде берілуі мүмкін."
    },
    "q11": {
        "ru": "• Приостановление производства - незамедлительно\n• Обеспечение иска - в день поступления",
        "kz": "• Өндірісті тоқтату - дереу\n• Талапты қамтамасыз ету - түскен күні"
    },
    "q12": {
        "ru": "Срок на обращение за судебным приказом составляет 3 года с момента, когда взыскатель узнал о нарушении права.",
        "kz": "Сот бұйрығына жүгіну мерзімі талапкер құқық бұзылғанын білген күннен бастап 3 жылды құрайды."
    }
}

# Полная база данных судов для 3 городов
courts_db = {
    "Астана": {
        "specialized": {
            "физ-физ": {
                "name": "Межрайонный специализированный гражданский суд №2",
                "address": "г. Астана, ул. Бейбитшилик, 25",
                "phone": "+7 (7172) 123-456",
                "type": "МСГД",
                "coords": (51.1282, 71.4307)
            },
            "юр-юр": {
                "name": "Специализированный межрайонный экономический суд г. Астаны",
                "address": "г. Астана, ул. Бокейхана, 4",
                "phone": "+7 (7172) 234-567",
                "type": "СМЭС",
                "coords": (51.1350, 71.4380)
            },
            "физ-юр": {
                "name": "Специализированный межрайонный экономический суд г. Астаны",
                "address": "г. Астана, ул. Бокейхана, 4",
                "phone": "+7 (7172) 234-567",
                "type": "СМЭС",
                "coords": (51.1350, 71.4380)
            },
            "юр-физ": {
                "name": "Специализированный межрайонный экономический суд г. Астаны",
                "address": "г. Астана, ул. Бокейхана, 4",
                "phone": "+7 (7172) 234-567",
                "type": "СМЭС",
                "coords": (51.1350, 71.4380)
            }
        }
    },
    "Алматы": {
        "specialized": {
            "физ-физ": {
                "name": "Межрайонный специализированный гражданский суд г. Алматы",
                "address": "г. Алматы, пр. Абая, 90",
                "phone": "+7 (727) 123-4567",
                "type": "МСГД",
                "coords": (43.2500, 76.9200)
            },
            "юр-юр": {
                "name": "Специализированный межрайонный экономический суд г. Алматы",
                "address": "г. Алматы, ул. Жарокова, 215",
                "phone": "+7 (727) 234-5678",
                "type": "СМЭС",
                "coords": (43.2450, 76.9150)
            },
            "физ-юр": {
                "name": "Специализированный межрайонный экономический суд г. Алматы",
                "address": "г. Алматы, ул. Жарокова, 215",
                "phone": "+7 (727) 234-5678",
                "type": "СМЭС",
                "coords": (43.2450, 76.9150)
            },
            "юр-физ": {
                "name": "Специализированный межрайонный экономический суд г. Алматы",
                "address": "г. Алматы, ул. Жарокова, 215",
                "phone": "+7 (727) 234-5678",
                "type": "СМЭС",
                "coords": (43.2450, 76.9150)
            }
        }
    },
    "Шымкент": {
        "specialized": {
            "физ-физ": {
                "name": "Межрайонный специализированный гражданский суд г. Шымкента",
                "address": "г. Шымкент, ул. Желтоксан, 28",
                "phone": "+7 (7252) 123-456",
                "type": "МСГД",
                "coords": (42.3180, 69.5900)
            },
            "юр-юр": {
                "name": "Специализированный межрайонный экономический суд г. Шымкента",
                "address": "г. Шымкент, пр. Тауке хана, 96",
                "phone": "+7 (7252) 234-567",
                "type": "СМЭС",
                "coords": (42.3150, 69.6000)
            },
            "физ-юр": {
                "name": "Специализированный межрайонный экономический суд г. Шымкента",
                "address": "г. Шымкент, пр. Тауке хана, 96",
                "phone": "+7 (7252) 234-567",
                "type": "СМЭС",
                "coords": (42.3150, 69.6000)
            },
            "юр-физ": {
                "name": "Специализированный межрайонный экономический суд г. Шымкента",
                "address": "г. Шымкент, пр. Тауке хана, 96",
                "phone": "+7 (7252) 234-567",
                "type": "СМЭС",
                "coords": (42.3150, 69.6000)
            }
        }
    }
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru")],
        [InlineKeyboardButton("🇰🇿 Қазақша", callback_data="lang_kz")]
    ]
    await update.message.reply_text(
        "👋 Привет! Сәлем!\nВыберите язык / Тілді таңдаңыз:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def handle_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = query.data.split("_")[1]
    user_id = query.from_user.id
    user_context[user_id] = {"lang": lang}

    keyboard = [
        [InlineKeyboardButton("Физ. лицо → Физ. лицо", callback_data="case_type_физ-физ")],
        [InlineKeyboardButton("Физ. лицо → Юр. лицо", callback_data="case_type_физ-юр")],
        [InlineKeyboardButton("Юр. лицо → Физ. лицо", callback_data="case_type_юр-физ")],
        [InlineKeyboardButton("Юр. лицо → Юр. лицо", callback_data="case_type_юр-юр")]
    ]

    text = {
        "ru": "👨‍⚖️ Выберите тип дела (истец → ответчик):",
        "kz": "👨‍⚖️ Істің түрін таңдаңыз (талапкер → жауапкер):"
    }[lang]

    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_case_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    case_type = query.data.split("_")[2]

    if user_id not in user_context:
        user_context[user_id] = {}
    user_context[user_id]["case_type"] = case_type

    lang = user_context[user_id].get("lang", "ru")

    request_text = {
        "ru": "📍 Отправьте ваше местоположение, чтобы найти ближайший суд:",
        "kz": "📍 Ең жақын сотты табу үшін орналасқан жеріңізді жіберіңіз:"
    }[lang]

    location_keyboard = ReplyKeyboardMarkup(
        [[KeyboardButton(text="📍 Отправить местоположение", request_location=True)]],
        resize_keyboard=True,
        one_time_keyboard=True
    )

    try:
        await query.edit_message_text(request_text)
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=request_text,
            reply_markup=location_keyboard
        )
    except Exception as e:
        logger.error(f"Error in handle_case_type: {e}")

async def handle_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = update.message.from_user.id
        lang = user_context.get(user_id, {}).get("lang", "ru")
        case_type = user_context.get(user_id, {}).get("case_type", "физ-физ")

        location = update.message.location
        user_coords = (location.latitude, location.longitude)

        geolocator = Nominatim(user_agent="court_bot")
        address = geolocator.reverse(user_coords, language='ru')

        city = None
        if address and 'address' in address.raw:
            address_data = address.raw['address']
            city = address_data.get('city') or address_data.get('town')

        # Уточнение названий городов
        if city:
            if "Астана" in city or "Нур-Султан" in city:
                city = "Астана"
            elif "Алматы" in city or "Алмата" in city:
                city = "Алматы"
            elif "Шымкент" in city:
                city = "Шымкент"

        if not city:
            error_text = {
                "ru": "❌ Не удалось определить город. Пожалуйста, попробуйте ещё раз.",
                "kz": "❌ Қаланы анықтау мүмкін болмады. Қайталап көріңіз."
            }[lang]
            await update.message.reply_text(error_text)
            return

        if city in courts_db and case_type in courts_db[city]["specialized"]:
            court = courts_db[city]["specialized"][case_type]
            distance = geopy.distance.distance(user_coords, court['coords']).km

            result_text = {
                "ru": f"👨‍⚖️ <b>{court['type']}: {court['name']}</b>\n\n"
                      f"📌 <b>Адрес:</b> {court['address']}\n"
                      f"📞 <b>Телефон:</b> {court['phone']}\n"
                      f"🗺 <b>Расстояние:</b> {distance:.1f} км\n\n"
                      f"<i>Тип дела: {case_type.replace('-', ' → ')}</i>",
                "kz": f"👨‍⚖️ <b>{court['type']}: {court['name']}</b>\n\n"
                      f"📌 <b>Мекен-жай:</b> {court['address']}\n"
                      f"📞 <b>Телефон:</b> {court['phone']}\n"
                      f"🗺 <b>Қашықтық:</b> {distance:.1f} км\n\n"
                      f"<i>Істің түрі: {case_type.replace('-', ' → ')}</i>"
            }[lang]

            await update.message.reply_text(result_text, parse_mode="HTML")
        else:
            error_text = {
                "ru": f"❌ Для типа дела '{case_type.replace('-', ' → ')}' не найден суд в городе {city}",
                "kz": f"❌ '{case_type.replace('-', ' → ')}' түріндегі іс үшін {city} қаласында сот табылмады"
            }[lang]
            await update.message.reply_text(error_text)

        await send_faq_menu(update.message, lang)

    except Exception as e:
        logger.error(f"Error in handle_location: {e}")
        error_text = {
            "ru": "❌ Произошла ошибка при обработке местоположения",
            "kz": "❌ Орналасқан жерді өңдеу кезінде қате пайда болды"
        }[user_context.get(user_id, {}).get("lang", "ru")]
        await update.message.reply_text(error_text)

async def send_faq_menu(message, lang):
    try:
        keyboard = [
            [InlineKeyboardButton(faq_questions["q1"][lang], callback_data="faq_q1"),
             InlineKeyboardButton(faq_questions["q2"][lang], callback_data="faq_q2")],
            [InlineKeyboardButton(faq_questions["q3"][lang], callback_data="faq_q3"),
             InlineKeyboardButton(faq_questions["q4"][lang], callback_data="faq_q4")],
            [InlineKeyboardButton(faq_questions["q5"][lang], callback_data="faq_q5"),
             InlineKeyboardButton(faq_questions["q6"][lang], callback_data="faq_q6")],
            [InlineKeyboardButton(faq_questions["q7"][lang], callback_data="faq_q7"),
             InlineKeyboardButton(faq_questions["q8"][lang], callback_data="faq_q8")],
            [InlineKeyboardButton(faq_questions["q9"][lang], callback_data="faq_q9"),
             InlineKeyboardButton(faq_questions["q10"][lang], callback_data="faq_q10")],
            [InlineKeyboardButton(faq_questions["q11"][lang], callback_data="faq_q11"),
             InlineKeyboardButton(faq_questions["q12"][lang], callback_data="faq_q12")],
            [InlineKeyboardButton("🌐 Сменить язык" if lang == "ru" else "🌐 Тілді өзгерту", callback_data="change_lang")]
        ]
        await message.reply_text(
            "❓ Выберите вопрос:" if lang == "ru" else "❓ Сұрақты таңдаңыз:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except Exception as e:
        logger.error(f"Error in send_faq_menu: {e}")

async def handle_faq_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.callback_query
        await query.answer()
        user_id = query.from_user.id
        lang = user_context.get(user_id, {}).get("lang", "ru")
        question_key = query.data.split("_")[1]

        answer = faq_answers.get(question_key, {}).get(lang, "Ответ не найден")
        await query.edit_message_text(
            f"{faq_questions[question_key][lang]}\n\n{answer}"
        )
    except Exception as e:
        logger.error(f"Error in handle_faq_answer: {e}")

async def handle_change_lang(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.callback_query
        await query.answer()
        await start(update, context)
    except Exception as e:
        logger.error(f"Error in handle_change_lang: {e}")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = update.message.from_user.id
        lang = user_context.get(user_id, {}).get("lang", "ru")

        if update.message.text in ["📍 Отправить местоположение", "📍 Орналасқан жерді жіберу"]:
            prompt_text = {
                "ru": "Пожалуйста, нажмите на кнопку отправки местоположения",
                "kz": "Орналасқан жерді жіберу түймесін басыңыз"
            }[lang]
            await update.message.reply_text(prompt_text)
        else:
            await start(update, context)
    except Exception as e:
        logger.error(f"Error in handle_text: {e}")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_language, pattern="^lang_"))
    app.add_handler(CallbackQueryHandler(handle_case_type, pattern="^case_type_"))
    app.add_handler(CallbackQueryHandler(handle_faq_answer, pattern="^faq_q"))
    app.add_handler(CallbackQueryHandler(handle_change_lang, pattern="^change_lang"))
    app.add_handler(MessageHandler(filters.LOCATION, handle_location))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    logger.info("Бот запущен...")
    app.run_polling()

if __name__ == '__main__':
    main()