import telebot
from telebot import types

from data import db_session
from data.quizes import Quiz
from data.questions import Question
from data.quiz2question import Quiz2Question


bot = telebot.TeleBot(API_KEY)
db_session.global_init(DB_NAME)
db_session = db_session.create_session()


@bot.message_handler(content_types=["text"], commands=["start"])
def start(message, invalid=False):
    person = message.from_user.id
    chat = message.chat.id
    if chat != person:
        Group.choose_quiz(message)
    else:
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
        keyboard.add("Начать случайную игру", "Ввести код игры", "Выбрать игру в каталоге", "Управление своими играми")
        if not invalid:
            bot.send_message(person, "Привет! Выбери раздел", reply_markup=keyboard)
        else:
            bot.send_message(person, "Давай ещё раз. Выбери раздел", reply_markup=keyboard)
        bot.register_next_step_handler(message, Single.choose_type)


class Single:
    @staticmethod
    def choose_type(message):
        text = message.text
        if text == 'Начать случайную игру':
            Single.new_game(message, quiz_id=None)
        elif text == "Ввести код игры":
            bot.send_message(message.chat.id, "Введи код игры", reply_markup=types.ReplyKeyboardRemove())
            bot.register_next_step_handler(message, Single.write_quiz_id)
        elif text == 'Выбрать игру в каталоге':
            Single.magazine(message)
        elif text == "Управление своими играми":
            ManageGames.start(message)
        else:
            start(message, invalid=True)

    @staticmethod
    def write_quiz_id(message):
        try:
            Single.new_game(message, quiz_id=message.text)
        except ValueError:
            bot.send_message(message.chat.id, "Код введен неверно")
            start(message, invalid=True)

    @staticmethod
    def new_game(message, quiz_id):
        if quiz_id is None:
            quiz_id = 0  # Позже реализуем для рандома
        questions = []
        quiz_info = db_session.query(Quiz).filter(Quiz.quiz_id == quiz_id).first()
        if quiz_info is None:
            raise ValueError
        for link in db_session.query(Quiz2Question).filter(Quiz2Question.quiz_id == quiz_id):
            questions.append(db_session.query(Question).filter(Question.question_id == link.question_id).first())
        text = f'''Игра: {quiz_info.name}\n
        Описание: {quiz_info.description}
        Количество вопросов: {quiz_info.question_count}
        Сложность: {quiz_info.level}'''
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
        keyboard.add("Играем!", "Вернуться в меню")
        bot.send_message(message.from_user.id, text, reply_markup=keyboard)
        bot.register_next_step_handler(message, Single.start_game, questions=questions)

    @staticmethod
    def start_game(message, questions):
        if message.text == 'Вернуться в меню':
            start(message)
        elif message.text == 'Играем!':
            bot.send_message(message.from_user.id, 'Поехали!', reply_markup=types.ReplyKeyboardRemove())
            stats = {'correct_anses': 0, 'curr_question': 0}
            Single.get_question(message, questions, stats)
        else:
            start(message, invalid=True)

    @staticmethod
    def get_question(message, questions, stats):
        question = questions[stats['curr_question']]
        text = f'Вопрос {stats["curr_question"] + 1} из {len(questions)}\n\n{question.text}'
        bot.send_photo(message.chat.id, open(question.pic_link, 'rb'), text)
        bot.register_next_step_handler(message, Single.check_answer, questions=questions, stats=stats)

    @staticmethod
    def check_answer(message, questions, stats):
        answer = message.text.lower().replace('ё', 'е')
        correct_anses = questions[stats['curr_question']].answer.split(';')
        if answer in correct_anses:
            stats['correct_anses'] += 1
            bot.send_message(message.chat.id, f'Правильно! Текущий счёт: {stats["correct_anses"]}')
        else:
            bot.send_message(message.chat.id, f'Неверно! Правильный ответ: {correct_anses[0].capitalize()}')
        if stats['curr_question'] + 1 < len(questions):
            stats['curr_question'] += 1
            bot.send_message(message.chat.id, f'Следующий вопрос!')
            Single.get_question(message, questions, stats)
        else:
            Single.get_results(message, questions, stats)

    @staticmethod
    def get_results(message, questions, stats):
        bot.send_message(message.chat.id,
                         f'Игра завершена! Твой результат: {stats["correct_anses"]} из {len(questions)}')
        bot.send_message(message.chat.id, 'Чтобы начать новую игру, отправь команду /start')

    @staticmethod
    def magazine(message, person=None):
        if person is None:
            person = message.from_user
        text = 'Список доступных игр:\n'
        for elem in db_session.query(Quiz).all():
            text += f'''\nИгра: {elem.name}\n
        Код игры: {elem.quiz_id}
        Описание: {elem.description}
        Количество вопросов: {elem.question_count}
        Сложность: {elem.level}'''
        bot.send_message(person.id, text, reply_markup=types.ReplyKeyboardRemove())
        bot.send_message(message.chat.id, 'Чтобы начать новую игру, отправь команду /start')


class Group:
    @staticmethod
    @bot.message_handler(content_types=["text"], commands=["game"])
    def choose_quiz(message):
        keyboard = types.InlineKeyboardMarkup()
        autogame = types.InlineKeyboardButton(text='Начать случайную игру', callback_data='autogame')
        keyboard.add(autogame)
        quiz_id = types.InlineKeyboardButton(text='Ввести код игры', callback_data='quiz_id')
        keyboard.add(quiz_id)
        magazine = types.InlineKeyboardButton(text='Выбрать игру в каталоге', callback_data='magazine')
        keyboard.add(magazine)
        bot.reply_to(message, "Выбери раздел", reply_markup=keyboard)

    @staticmethod
    @bot.callback_query_handler(func=lambda call: True)
    def group_start_game_callback_worker(call):
        message = call.message
        if call.data == "autogame":
            bot.delete_message(message.chat.id, message.message_id)
            Group.new_game(message, quiz_id=None)
        elif call.data == "magazine":
            bot.edit_message_text('Отправляю список игр в личные сообщения',
                                  chat_id=message.chat.id, message_id=message.message_id)
            Group.magazine(message, person=call.from_user)
        elif call.data == "quiz_id":
            bot.edit_message_text('Введи код игры', chat_id=message.chat.id, message_id=message.message_id)
            bot.register_next_step_handler(message, Group.write_quiz_id)
        else:
            print('what the hell')
            bot.send_message(message.chat.id, "Что-то пошло не так")

    @staticmethod
    def new_game(message, quiz_id):
        bot.send_message(message.chat.id, 'Пока я умею работать только в личных сообщениях!')

    @staticmethod
    def write_quiz_id(message):
        try:
            Group.new_game(message, quiz_id=message.text)
        except ValueError:
            bot.send_message(message.chat.id, "Код введен неверно")
            start(invalid=True)

    @staticmethod
    def magazine(message, person):
        try:
            Single.magazine(message, person)
        except telebot.apihelper.ApiTelegramException:
            bot.edit_message_text('Не удалось отправить сообщение. Запусти бота в личных сообщениях',
                                  chat_id=message.chat.id, message_id=message.message_id)


class ManageGames:
    @staticmethod
    def start(message):
        bot.send_message(message.from_user.id, "Раздел в разработке", reply_markup=types.ReplyKeyboardRemove())


bot.infinity_polling()
