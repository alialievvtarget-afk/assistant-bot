"""
Бот-база знаний: кнопка -> задача -> присылает все файлы инструкции.

Структура:
  tasks/<task_id>/meta.json   -> {"title": "...", "description": "..."}
  tasks/<task_id>/...         -> любые файлы (.md, .json, .js и т.д.) — все отправляются как документы

Чтобы добавить новую задачу: создать новую папку в tasks/ с meta.json + файлами.
Никаких изменений в коде бота не требуется — список кнопок строится автоматически.
"""

import json
import logging
import os
from pathlib import Path

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent
TASKS_DIR = BASE_DIR / "tasks"

# Токен берём из переменной окружения BOT_TOKEN (задаётся в хостинге),
# либо (для локального теста) из config/assistant_bot_token.txt
TOKEN = os.environ.get("BOT_TOKEN")
if not TOKEN:
    token_file = BASE_DIR.parent / "config" / "assistant_bot_token.txt"
    if token_file.exists():
        TOKEN = token_file.read_text(encoding="utf-8").strip()

if not TOKEN:
    raise RuntimeError("Не найден токен бота: задайте BOT_TOKEN или config/assistant_bot_token.txt")


def list_tasks():
    """Возвращает список задач: [(task_id, title, description, folder_path), ...]"""
    tasks = []
    if not TASKS_DIR.exists():
        return tasks
    for folder in sorted(TASKS_DIR.iterdir()):
        if not folder.is_dir():
            continue
        meta_file = folder / "meta.json"
        if not meta_file.exists():
            continue
        try:
            meta = json.loads(meta_file.read_text(encoding="utf-8"))
        except Exception as e:
            logger.warning("Пропускаю %s: не смог прочитать meta.json (%s)", folder, e)
            continue
        tasks.append((folder.name, meta.get("title", folder.name), meta.get("description", ""), folder))
    return tasks


def task_files(folder: Path):
    """Все файлы задачи, кроме meta.json, рекурсивно."""
    files = []
    for p in sorted(folder.rglob("*")):
        if p.is_file() and p.name != "meta.json":
            files.append(p)
    return files


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tasks = list_tasks()
    if not tasks:
        await update.message.reply_text("Пока нет ни одной задачи. Попроси Али добавить.")
        return

    buttons = [
        [InlineKeyboardButton(title, callback_data=f"task:{task_id}")]
        for task_id, title, _desc, _folder in tasks
    ]
    await update.message.reply_text(
        "Привет! Выбери задачу — пришлю инструкцию и все файлы:",
        reply_markup=InlineKeyboardMarkup(buttons),
    )


async def on_task_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    task_id = query.data.split(":", 1)[1]
    folder = TASKS_DIR / task_id
    meta_file = folder / "meta.json"
    if not folder.exists() or not meta_file.exists():
        await query.message.reply_text("Задача не найдена (возможно, её переименовали).")
        return

    meta = json.loads(meta_file.read_text(encoding="utf-8"))
    title = meta.get("title", task_id)
    description = meta.get("description", "")

    await query.message.reply_text(f"📦 {title}\n{description}\n\nОтправляю файлы...")

    files = task_files(folder)
    if not files:
        await query.message.reply_text("В этой задаче пока нет файлов.")
        return

    for f in files:
        with open(f, "rb") as fh:
            await query.message.reply_document(document=fh, filename=f.name)


async def list_tasks_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start(update, context)


def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("tasks", list_tasks_command))
    app.add_handler(CallbackQueryHandler(on_task_click, pattern=r"^task:"))

    logger.info("Бот запущен, задач найдено: %d", len(list_tasks()))
    app.run_polling()


if __name__ == "__main__":
    main()
