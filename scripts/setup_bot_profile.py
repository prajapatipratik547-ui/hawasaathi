"""Set the bot's public profile: photo, descriptions and command menu, in English, Hindi and Marathi.

    python scripts/setup_bot_profile.py               # photo + texts + commands
    python scripts/setup_bot_profile.py --texts-only  # only texts and commands

Safe to run again. Telegram shows the hi/mr texts to users whose Telegram app is in that language,
and the English ones to everyone else. Needs TELEGRAM_BOT_TOKEN in .env. The token is never printed.
"""
import argparse
import json
import os
import sys

from dotenv import load_dotenv

# add project root to path so `from bot import ...` works when run from project folder
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

load_dotenv(os.path.join(ROOT, ".env"))

from bot.telegram import Telegram

AVATAR = os.path.join(ROOT, "assets", "avatar.jpg")

# shown in an empty chat, before the user presses Start (max 512 characters)
DESCRIPTION = {
    "en": (
        "🌬️ HawaSaathi tells you how clean the air is where you live, and what to do about it.\n\n"
        "• A morning air update at 7 AM, with advice for your age and health\n"
        "• A warning when pollution spikes\n"
        "• Ask anything: \"Can I go for a run now?\" or \"How is the air in Delhi?\"\n\n"
        "English · हिंदी · मराठी · Free · Not medical advice.\n\nTap Start to begin."
    ),
    "hi": (
        "🌬️ हवासाथी बताता है कि आपके इलाके की हवा कितनी साफ़ है, और आपको क्या करना चाहिए।\n\n"
        "• हर सुबह 7 बजे हवा का अपडेट, आपकी उम्र और सेहत के हिसाब से सलाह\n"
        "• प्रदूषण बढ़ने पर चेतावनी\n"
        "• कुछ भी पूछें: \"क्या अभी दौड़ने जा सकता हूँ?\" या \"दिल्ली में हवा कैसी है?\"\n\n"
        "English · हिंदी · मराठी · मुफ़्त · यह डॉक्टरी सलाह नहीं है।\n\nशुरू करने के लिए Start दबाएँ।"
    ),
    "mr": (
        "🌬️ हवासाथी सांगतो की तुमच्या भागातील हवा किती स्वच्छ आहे, आणि तुम्ही काय करावे.\n\n"
        "• दररोज सकाळी 7 वाजता हवेचा अपडेट, तुमच्या वयानुसार आणि आरोग्यानुसार सल्ला\n"
        "• प्रदूषण वाढल्यावर इशारा\n"
        "• काहीही विचारा: \"आत्ता धावायला जाऊ का?\" किंवा \"दिल्लीत हवा कशी आहे?\"\n\n"
        "English · हिंदी · मराठी · मोफत · हा वैद्यकीय सल्ला नाही.\n\nसुरू करण्यासाठी Start दाबा."
    ),
}

# shown on the bot's profile page and when someone shares the bot (max 120 characters)
SHORT_DESCRIPTION = {
    "en": "Free daily air-quality alerts and advice for your area, in English, हिंदी and मराठी. 🌬️",
    "hi": "आपके इलाके के लिए रोज़ हवा की गुणवत्ता का अलर्ट और सलाह, हिंदी, मराठी और English में। 🌬️",
    "mr": "तुमच्या भागासाठी रोजचा हवेच्या गुणवत्तेचा अलर्ट आणि सल्ला, मराठी, हिंदी आणि English मध्ये. 🌬️",
}

# the menu button next to the message box
COMMANDS = {
    "en": [
        ("start", "Start or restart"),
        ("settings", "Change language, location or profile"),
        ("invite", "Invite family and friends"),
        ("delete", "Delete all my data"),
    ],
    "hi": [
        ("start", "शुरू करें"),
        ("settings", "भाषा, लोकेशन या प्रोफ़ाइल बदलें"),
        ("invite", "परिवार और दोस्तों को बुलाएँ"),
        ("delete", "मेरा सारा डेटा मिटाएँ"),
    ],
    "mr": [
        ("start", "सुरू करा"),
        ("settings", "भाषा, लोकेशन किंवा प्रोफाइल बदला"),
        ("invite", "कुटुंब आणि मित्रांना बोलवा"),
        ("delete", "माझा सर्व डेटा हटवा"),
    ],
}


def main():
    parser = argparse.ArgumentParser(description="Set the bot's photo, descriptions and command menu.")
    parser.add_argument("--texts-only", action="store_true", help="skip the photo (each upload adds one to the bot's photo history)")
    args = parser.parse_args()
    telegram = Telegram()

    if not args.texts_only:
        with open(AVATAR, "rb") as f:
            photo = json.dumps({"type": "static", "photo": "attach://avatar"})
            telegram._post_sync("setMyProfilePhoto", {"photo": photo}, files={"avatar": ("avatar.jpg", f, "image/jpeg")})
        print("profile photo set")

    for lang in ("en", "hi", "mr"):
        # English is the default for every other app language too
        code = {} if lang == "en" else {"language_code": lang}
        telegram._post_sync("setMyDescription", {"description": DESCRIPTION[lang], **code})
        telegram._post_sync("setMyShortDescription", {"short_description": SHORT_DESCRIPTION[lang], **code})
        commands = [{"command": c, "description": d} for c, d in COMMANDS[lang]]
        telegram._post_sync("setMyCommands", {"commands": commands, **code})
        print(f"{lang}: description, short description and commands set")


if __name__ == "__main__":
    main()
