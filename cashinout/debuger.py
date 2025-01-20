from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.utils.formatting import *

router = Router()

@router.message(Command("types"))
async def types_command(message: Message):
    content = [
        Text("As list: \n", as_list("word1", "word2", "word3", sep="\n")),
        Text("As marked list: \n", as_marked_list("word1", "word2", "word3", marker="MRK - ")),
        Text("As numbered list: \n", as_numbered_list("word1", "word2", "word3", start=10)),
        Text("As section: \n", as_section("title: \n", "word1, word2, word3")),
        Text("As marked section: \n", as_marked_section("title: ", "word1", "word2", "word3", marker="MRK - ")),
        Text("As numbered section: \n", as_numbered_section("title: ", "word1", "word2", "word3", start=10)),
        Text("As key value: \n", as_key_value("title", "word1, word2, word3")),
        as_list(
            Text("Also:"),
            HashTag("HashTag"), CashTag("CashTag"),
            BotCommand("/BotCommand"),
            Url("https://Url.Url/"), Email("Email@email.email"), PhoneNumber("+43790857843"),
            Bold("Bold"), Italic("Italic"), Underline("Underline"), Spoiler("Spoiler"), Code("Code"), Pre("Pre"),
            TextLink("TextLink", url="https://t.me/"), 
            TextMention("TextMention", user=message.from_user),
            BlockQuote("BlockQuote"), ExpandableBlockQuote("ExpandableBlockQuote\n\n\n\nBlock\n\n\nBlock"),
            sep="\n"
        )
    ]
    for contentpart in content:
        await message.answer(**contentpart.as_kwargs())