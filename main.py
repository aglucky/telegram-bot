import logging
from telegram import Update, InlineQueryResultArticle, InputTextMessageContent
from telegram.ext import filters, ApplicationBuilder, CallbackContext, CommandHandler, MessageHandler, InlineQueryHandler
from dotenv import load_dotenv
from datetime import datetime
import requests
import os
from github import Github
import time



logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def start(update: Update, context: CallbackContext):
    await context.bot.send_message(
        chat_id=update.effective_chat.id, 
        text="Dendron Bot is online!"
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
        note_text += f"\n- {datetime.now().date()}\n\t- " + "".join(context.args)
        updated_note = repo.update_file("notes/what-im-doing.telegram-notes.md", "telegram update", note_text, note.sha)
        
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
        updated_note = repo.update_file("notes/what-im-doing.telegram-notes.md", "telegram update", new_text, note.sha)
        
        result = "failed"
        if updated_note:
            result = "success"

        # Bot response
        await context.bot.send_message(
        chat_id=update.effective_chat.id, 
        text=result
        )



if __name__ == '__main__':
    load_dotenv('.env')
    application = ApplicationBuilder().token(os.getenv('BOT_TOKEN')).build()
    
    get_handler = CommandHandler('getNote', getNote)
    add_handler = CommandHandler('addBullet', addBullet)
    del_handler = CommandHandler('deleteBullet', deleteBullet)

    

    application.add_handler(get_handler)
    application.add_handler(add_handler)
    application.add_handler(del_handler)

    
    application.run_polling()