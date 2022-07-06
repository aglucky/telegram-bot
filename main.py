import logging
from telegram import Update
from telegram.ext import filters, ApplicationBuilder, CallbackContext, CommandHandler, MessageHandler
from dotenv import load_dotenv
from datetime import datetime
import requests
import os
from github import Github
from wordle import final_action

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def start(update: Update, context: CallbackContext):
    await context.bot.send_message(
        chat_id=update.effective_chat.id, 
        text="Gluck Bot is online!"
        )

async def xkcd(update: Update, context: CallbackContext):
    # Make Sure the user has provided a number
    try:
        num = int(context.args[0])
        url = f"https://xkcd.com/{num}/info.0.json"
    except:
        url = "https://xkcd.com/info.0.json"
        
    # Get the comic
    comic = requests.get(url)
    text = "comic not found"
    if comic.status_code == 200:
        text = f"{comic.json()['title']}\n{comic.json()['img']}\n{comic.json()['alt']}"

    await context.bot.send_message(
        chat_id=update.effective_chat.id, 
        text=text
        )

async def getNote(update: Update, context: CallbackContext):
        g = Github(os.getenv('GITHUB_TOKEN'))
        repo = g.get_repo("aglucky/knowledge")
        note = repo.get_contents("notes/what-im-doing.telegram-notes.md")
        response = requests.get(note.download_url)

        await context.bot.send_message(
        chat_id=update.effective_chat.id, 
        text=response.text)

async def addBullet(update: Update, context: CallbackContext):
        # Setup Github
        g = Github(os.getenv('GITHUB_TOKEN'))
        repo = g.get_repo("aglucky/knowledge")

        # Get updated note content
        note = repo.get_contents("notes/what-im-doing.telegram-notes.md")
        note_text = requests.get(note.download_url).text
        note_text += f"\n- {datetime.now().date()}\n\t- " + " ".join(context.args)
        updated_note = repo.update_file("notes/what-im-doing.telegram-notes.md", "telegram update add", note_text, note.sha)
        
        result = "failed"
        if updated_note:
            result = "success"

        # Bot response
        await context.bot.send_message(
        chat_id=update.effective_chat.id, 
        text=result
        )


async def deleteBullet(update: Update, context: CallbackContext):
        # Setup Github
        g = Github(os.getenv('GITHUB_TOKEN'))
        repo = g.get_repo("aglucky/knowledge")

        # Get updated note content
        note = repo.get_contents("notes/what-im-doing.telegram-notes.md")
        note_text = requests.get(note.download_url).text
        new_text = "\n".join(note_text.split("\n")[:-2])
        updated_note = repo.update_file("notes/what-im-doing.telegram-notes.md", "telegram update delete", new_text, note.sha)
        
        result = "failed"
        if updated_note:
            result = "success"

        # Bot response
        await context.bot.send_message(
        chat_id=update.effective_chat.id, 
        text=result
        )

async def solveWordle(update: Update, context: CallbackContext):
    print('here')
    file = await context.bot.getFile(update.message.photo[-1].file_id)
    path = 'wordle.png'
    await file.download(path)
    result = final_action(path)
    os.remove(path)

    # Bot response
    await context.bot.send_message(
    chat_id=update.effective_chat.id, 
    text=result
    )




if __name__ == '__main__':
    load_dotenv('.env')
    TOKEN = os.getenv('BOT_TOKEN')
    application = ApplicationBuilder().token(TOKEN).build()
    PORT = int(os.environ.get('PORT', '8443'))
    job_queue = application.job_queue
    
    start_handler = CommandHandler('start', start)
    get_handler = CommandHandler('getNote', getNote)
    add_handler = CommandHandler('addBullet', addBullet, filters=filters.User(username='agluck1'))
    del_handler = CommandHandler('deleteBullet', deleteBullet, filters=filters.User(username='agluck1'))
    xkcd_handler = CommandHandler('xkcd', xkcd)
    wordle_handler = MessageHandler(filters.PHOTO, solveWordle)

    

    application.add_handler(start_handler)
    application.add_handler(get_handler)
    application.add_handler(add_handler)
    application.add_handler(del_handler)
    application.add_handler(xkcd_handler)
    application.add_handler(wordle_handler)

    application.run_webhook(
    listen="0.0.0.0",
    port=PORT,
    url_path=TOKEN,
    webhook_url="https://telegram-bot-adam.azurewebsites.net/" + TOKEN
    )

