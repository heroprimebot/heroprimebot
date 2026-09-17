import os
import json

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)


# ============================================================
# AYARLAR
# ============================================================

BOT_TOKEN = "8862557397:AAE7SvuqE5ST4RiIcQz9g5G66o8uNzBV9Uw"

# Site görselinin Telegram file_id bilgisini burada saklıyoruz.
IMAGE_FILE = "site_image.json"


# ============================================================
# SİTELER
# ============================================================

SITES = [
    (
        "🎰 JASİNO",
        "https://jasino.to/4ZD8"
    ),
    (
        "🎰 BETWINNER",
        "https://bwref-l4ftkntp.com/1Px4?p=%2Fregistration%2F"
    ),
    (
        "💎 BİZBET",
        "https://refpa-0768.com/L?tag=d_2106249m_62079c_&site=2106249&ad=62079&r=registration/"
    ),
    (
        "🌐 HEROPRIME WEB",
        "https://heroprime68.com/"
    ),
]


# ============================================================
# SİTE BUTONLARI
# ============================================================

def site_keyboard():

    keyboard = [
        [
            InlineKeyboardButton(
                "🎰 JASİNO",
                url=SITES[0][1]
            )
        ],
        [
            InlineKeyboardButton(
                "🎰 BETWINNER",
                url=SITES[1][1]
            )
        ],
        [
            InlineKeyboardButton(
                "💎 BİZBET",
                url=SITES[2][1]
            )
        ],
        [
            InlineKeyboardButton(
                "🌐 HEROPRIME WEB",
                url=SITES[3][1]
            )
        ],
    ]

    return InlineKeyboardMarkup(keyboard)


# ============================================================
# GÖRSELİ KAYDET
# ============================================================

def save_image(file_id):

    data = {
        "file_id": file_id
    }

    with open(
        IMAGE_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            data,
            file,
            ensure_ascii=False,
            indent=2
        )


# ============================================================
# KAYITLI GÖRSELİ OKU
# ============================================================

def load_image():

    if not os.path.exists(IMAGE_FILE):
        return None

    try:

        with open(
            IMAGE_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            data = json.load(file)

        return data.get("file_id")

    except Exception:

        return None


# ============================================================
# SİTE MENÜSÜNÜ GÖNDER
# ============================================================

async def send_site_menu(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    text = (
        "🎰 <b>HEROPRIME</b>\n\n"
        "Aşağıdaki butonlardan seçim yapabilirsin."
    )

    keyboard = site_keyboard()

    image_id = load_image()

    # --------------------------------------------------------
    # GÖRSELLİ MENÜ
    # --------------------------------------------------------

    if image_id:

        try:

            await update.message.reply_photo(
                photo=image_id,
                caption=text,
                parse_mode="HTML",
                reply_markup=keyboard
            )

            return

        except Exception:

            pass

    # --------------------------------------------------------
    # GÖRSEL YOKSA SADECE BUTONLAR
    # --------------------------------------------------------

    await update.message.reply_text(
        text,
        parse_mode="HTML",
        reply_markup=keyboard
    )


# ============================================================
# /start
# ============================================================

async def start_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    keyboard = [
        [
            InlineKeyboardButton(
                "🎰 SİTELER",
                callback_data="sites"
            )
        ]
    ]

    await update.message.reply_text(
        "👋 <b>Hoş geldin!</b>\n\n"
        "Menüden işlem seçebilirsin.\n\n"
        "Site menüsünü açmak için:\n"
        "<code>.site</code>\n"
        "veya\n"
        "<code>!site</code>",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ============================================================
# /site
# ============================================================

async def site_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await send_site_menu(
        update,
        context
    )


# ============================================================
# /setimage
# ============================================================

async def setimage_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    context.user_data[
        "waiting_for_site_image"
    ] = True

    await update.message.reply_text(
        "🖼️ <b>Site görselini gönder.</b>\n\n"
        "Fotoğraf olarak gönderdiğinde "
        "otomatik olarak kaydedilecek.",
        parse_mode="HTML"
    )


# ============================================================
# GÖRSELİ AL
# ============================================================

async def receive_image(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not context.user_data.get(
        "waiting_for_site_image"
    ):

        return

    if not update.message.photo:

        return

    # Telegram'ın gönderdiği en büyük fotoğraf
    photo = update.message.photo[-1]

    file_id = photo.file_id

    save_image(file_id)

    context.user_data[
        "waiting_for_site_image"
    ] = False

    await update.message.reply_text(
        "✅ <b>Görsel kaydedildi.</b>\n\n"
        "Artık <code>.site</code> veya "
        "<code>!site</code> yazıldığında "
        "bu görsel kullanılacak.",
        parse_mode="HTML"
    )


# ============================================================
# .site / !site
# ============================================================

async def text_commands(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not update.message:
        return

    if not update.message.text:
        return

    text = update.message.text.strip().lower()

    # --------------------------------------------------------
    # .site
    # --------------------------------------------------------

    if text == ".site":

        await send_site_menu(
            update,
            context
        )

        return

    # --------------------------------------------------------
    # !site
    # --------------------------------------------------------

    if text == "!site":

        await send_site_menu(
            update,
            context
        )

        return


# ============================================================
# /siteimage
# ============================================================

async def siteimage_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    image_id = load_image()

    if not image_id:

        await update.message.reply_text(
            "❌ Henüz site görseli ayarlanmadı.\n\n"
            "Önce /setimage komutunu kullan."
        )

        return

    await update.message.reply_photo(
        photo=image_id,
        caption="🖼️ Mevcut site görseli"
    )


# ============================================================
# BUTONLAR
# ============================================================

async def button_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()

    # --------------------------------------------------------
    # SİTELER BUTONU
    # --------------------------------------------------------

    if query.data == "sites":

        text = (
            "🎰 <b>HEROPRIME</b>\n\n"
            "Aşağıdaki butonlardan seçim yapabilirsin."
        )

        keyboard = site_keyboard()

        image_id = load_image()

        # ----------------------------------------------------
        # Görsel varsa
        # ----------------------------------------------------

        if image_id:

            try:

                await query.message.reply_photo(
                    photo=image_id,
                    caption=text,
                    parse_mode="HTML",
                    reply_markup=keyboard
                )

                return

            except Exception:

                pass

        # ----------------------------------------------------
        # Görsel yoksa
        # ----------------------------------------------------

        await query.message.reply_text(
            text,
            parse_mode="HTML",
            reply_markup=keyboard
        )


# ============================================================
# BOTU BAŞLAT
# ============================================================

def main():

    if not BOT_TOKEN:

        raise RuntimeError(
            "BOT_TOKEN bulunamadı. "
            "Railway Variables kısmına BOT_TOKEN ekle."
        )

    application = (
        Application
        .builder()
        .token(BOT_TOKEN)
        .build()
    )

    # --------------------------------------------------------
    # KOMUTLAR
    # --------------------------------------------------------

    application.add_handler(
        CommandHandler(
            "start",
            start_command
        )
    )

    application.add_handler(
        CommandHandler(
            "site",
            site_command
        )
    )

    application.add_handler(
        CommandHandler(
            "setimage",
            setimage_command
        )
    )

    application.add_handler(
        CommandHandler(
            "siteimage",
            siteimage_command
        )
    )

    # --------------------------------------------------------
    # INLINE BUTONLAR
    # --------------------------------------------------------

    application.add_handler(
        CallbackQueryHandler(
            button_callback
        )
    )

    # --------------------------------------------------------
    # FOTOĞRAF
    # --------------------------------------------------------

    application.add_handler(
        MessageHandler(
            filters.PHOTO,
            receive_image
        )
    )

    # --------------------------------------------------------
    # .site / !site
    # --------------------------------------------------------

    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            text_commands
        )
    )

    print("🤖 HEROPRIME bot çalışıyor...")

    # --------------------------------------------------------
    # BOTU ÇALIŞTIR
    # --------------------------------------------------------

    application.run_polling()


# ============================================================
# PROGRAM BAŞLANGICI
# ============================================================

if __name__ == "__main__":
    main()
