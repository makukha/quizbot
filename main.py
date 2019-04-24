"""
Simple Quiz Bot for Telegram
"""

from datetime import datetime
import logging
from logging import debug, info
from pathlib import Path
import random
import telegram
from telegram.ext import Updater, CommandHandler, MessageHandler, PicklePersistence
import yaml  # pyyaml


logging.basicConfig(
    filename='conversations.log',
    format='%(asctime)s %(levelname)-7s %(name)s %(message)s')
logging.getLogger().setLevel('DEBUG')

TOKEN_FILE = 'token.txt'
TOKEN = Path(TOKEN_FILE).read_text().strip()
AUTHORIZED_USERS = ['makukha']

DURATION = 5


class Question:

    def __init__(self, qid, question, answers):
        self.qid = qid
        self.text = question
        self.answers = {}
        self.correct = None
        for a in answers:
            aid = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'[len(self.answers)]
            if isinstance(a, str):
                self.answers[aid] = a
            elif isinstance(a, dict) and len(a) == 1 and \
                    'correct' in a and self.correct is None:
                self.answers[aid] = a['correct']
                self.correct = aid
            else:
                raise ValueError(
                    f'Incorrect answers in question {qid}: {answers}')

QUESTIONS = {q['id']: Question(q['id'], q['q'], q['a'])
    for q in yaml.load(Path('questions.yaml').read_text())}


def start(update, context):
    """Command handler for command /start"""

    msg = update.message
    user = msg.from_user
    debug(f'Quiz bot entered by user: {user.id} @{user.username} "{user.first_name} {user.last_name}"')

    if AUTHORIZED_USERS and user.username not in AUTHORIZED_USERS:
        return

    if 'username' not in context.user_data:
        context.user_data['username'] = user.username

    msg.bot.send_message(msg.chat_id,
        text=f'Давайте начнем тест. У вас будет {DURATION} минут на {len(QUESTIONS)} вопросов. Готовы?',
        reply_markup=telegram.ReplyKeyboardMarkup([['Начать тест']]))


def common_message(update, context):
    """General response handler"""

    msg = update.message
    user = msg.from_user
    debug(f'Message received from {user.id} @{user.username}: {msg.text}')

    if AUTHORIZED_USERS and user.username not in AUTHORIZED_USERS:
         return

    if 'quiz' not in context.user_data:

        info(f'Quiz started by {user.id} @{user.username}')

        context.user_data['quiz'] = {}
        context.user_data['quiz']['answers'] = {}
        starttime = datetime.now()
        context.user_data['quiz']['starttime'] = starttime

        msg.bot.send_message(msg.chat_id,
            text=f'Тест начат в {starttime}',
            reply_markup=telegram.ReplyKeyboardRemove())

    else:
        # save response
        context.user_data['quiz']['answers'][context.user_data['quiz']['current_qid']] = msg.text

    # ask the question

    questions_left = set(QUESTIONS) - set(context.user_data['quiz']['answers'])

    if len(questions_left) > 0:

        question = QUESTIONS[random.sample(questions_left, 1)[0]]

        msg.bot.send_message(msg.chat_id,
            text=f'{question.text}\n' + \
                '\n'.join(f'{aid}. {text}' for aid, text in sorted(question.answers.items())),
            reply_markup=telegram.ReplyKeyboardMarkup([[aid for aid in sorted(question.answers)]]))

        context.user_data['quiz']['current_qid'] = question.qid

    else:
        msg.bot.send_message(msg.chat_id,
            text=f'Тест пройден!',
            reply_markup=telegram.ReplyKeyboardRemove())
        context.user_data['quiz']['current_qid'] = None


def main():
    storage = PicklePersistence(filename='data.pickle')
    updater = Updater(token=TOKEN, persistence=storage, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(MessageHandler(None, common_message))
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
