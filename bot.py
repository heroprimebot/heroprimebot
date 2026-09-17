import os
import json
import re

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

BOT_TOKEN = '8862557397:AAGlsz2UrF-1WXnMEmEI7KAVNJpdKTN2W1A'

IMAGE_FILE = "site_image.json"


# ============================================================
# ============================================================
# MENÜ
# ============================================================

# Buraya kullanacağın güvenli/genel bağlantıları ekleyebilirsin.
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
# KÜFÜR / HAKARET FİLTRESİ
# ============================================================

BAD_WORDS = {
    "ornek1",
    "ornek2",
    "ornek3",
}


def normalize_text(text):

    text = text.lower()

    replacements = {
        "ı": "i",
        "ş": "s",
        "ğ": "g",
        "ü": "u",
        "ö": "o",
        "ç": "c",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    # Boşluk, nokta, tire vb. karakterleri kaldırır.
    text = re.sub(
        r"[^a-z0-9]",
        "",
        text
    )

    return text


def contains_bad_word(text):

    normalized = normalize_text(text)

    for word in BAD_WORDS:

        if normalize_text(word) in normalized:
            return True

    return False


# ============================================================
# GÖRSEL KAYDET
# ============================================================

def save_image(file_id):

    with open(
        IMAGE_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            {
                "file_id": file_id
            },
            file,
            ensure_ascii=False,
            indent=2
        )


# ============================================================
# GÖRSEL OKU
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
# SİTE MENÜSÜ
# ============================================================

async def send_site_menu(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    text = (
        "🌐 <b>HEROPRIME</b>\n\n"
        "📌 Güvenilir Sponsor ve VIP Sitelerimize "
        "aşağıdaki butonlardan ulaşabilirsiniz.\n\n"
        "⚠️ <b>Dikkat!</b>\n"
        "Hiçbir yönetici sizden özel mesaj yoluyla "
        "para talep etmez veya hesabınıza giriş bilgisi istemez."
    )

    keyboard = site_keyboard()

    image_id = load_image()

    # --------------------------------------------------------
    # GÖRSEL VARSA
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
    # GÖRSEL YOKSA SADECE YAZI
    # --------------------------------------------------------

    await update.message.reply_text(
        text,
        parse_mode="HTML",
        reply_markup=keyboard
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

    if text in (
        ".site",
        "!site"
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

    # --------------------------------------------------------
    # Grup yöneticisi kontrolü
    # --------------------------------------------------------

    if update.effective_chat.type in (
        "group",
        "supergroup"
    ):

        member = await update.effective_chat.get_member(
            update.effective_user.id
        )

        if member.status not in (
            "administrator",
            "creator"
        ):

            await update.message.reply_text(
                "❌ Bu işlemi sadece grup yöneticileri kullanabilir."
            )

            return

    # --------------------------------------------------------
    # Görsel bekleme modu
    # --------------------------------------------------------

    context.user_data[
        "waiting_for_site_image"
    ] = True

    await update.message.reply_text(
        "🖼️ Site görselini fotoğraf olarak gönder."
    )


# ============================================================
# GÖRSEL AL
# ============================================================

async def receive_image(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not context.user_data.get(
        "waiting_for_site_image"
    ):

        return

    if not update.message:
        return

    if not update.message.photo:
        return

    # En yüksek çözünürlüklü fotoğrafı al.
    photo = update.message.photo[-1]

    save_image(
        photo.file_id
    )

    context.user_data[
        "waiting_for_site_image"
    ] = False

    await update.message.reply_text(
        "✅ Görsel kaydedildi.\n\n"
        "Artık .site veya !site yazıldığında "
        "bu görsel kullanılacak."
    )


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
            "❌ Henüz görsel ayarlanmadı.\n\n"
            "Önce /setimage kullan."
        )

        return

    await update.message.reply_photo(
        photo=image_id,
        caption="🖼️ Mevcut görsel"
    )


# ============================================================
# KÜFÜR / HAKARET MODERASYONU
# ============================================================

async def moderation_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not update.message:
        return

    # Sadece gruplarda çalış.
    if update.effective_chat.type not in (
        "group",
        "supergroup"
    ):

        return

    if not update.effective_user:
        return

    # Botların mesajlarını kontrol etme.
    if update.effective_user.is_bot:
        return

    message_text = (
        update.message.text
        or update.message.caption
        or ""
    )

    if not message_text:
        return

    # Küfür/hakaret yoksa hiçbir şey yapma.
    if not contains_bad_word(message_text):
        return

    user_id = update.effective_user.id

    # --------------------------------------------------------
    # YÖNETİCİLERE DOKUNMA
    # --------------------------------------------------------

    try:

        member = await update.effective_chat.get_member(
            user_id
        )

        if member.status in (
            "administrator",
            "creator"
        ):

            return

    except Exception:

        return

    # --------------------------------------------------------
    # MESAJI SİL
    # --------------------------------------------------------

    try:

        await update.message.delete()

    except Exception:

        return

    # --------------------------------------------------------
    # UYARI GÖNDER
    # --------------------------------------------------------

    try:

        warning = await update.effective_chat.send_message(
            "⚠️ Uygunsuz/küfürlü mesaj silindi."
        )

        # 10 saniye sonra uyarıyı sil.
        context.job_queue.run_once(
            delete_warning,
            10,
            data={
                "chat_id": update.effective_chat.id,
                "message_id": warning.message_id,
            }
        )

    except Exception:

        pass


# ============================================================
# UYARIYI SİL
# ============================================================

async def delete_warning(
    context: ContextTypes.DEFAULT_TYPE
):

    data = context.job.data

    try:

        await context.bot.delete_message(
            chat_id=data["chat_id"],
            message_id=data["message_id"]
        )

    except Exception:

        pass


# ============================================================
# BUTON CALLBACK
# ============================================================

async def button_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()

    if query.data != "sites":
        return

    text = (
        "🌐 <b>HEROPRIME</b>\n\n"
        "📌 Güvenilir Sponsor ve VIP Sitelerimize "
        "aşağıdaki butonlardan ulaşabilirsiniz.\n\n"
        "⚠️ <b>Dikkat!</b>\n"
        "Hiçbir yönetici sizden özel mesaj yoluyla "
        "para talep etmez veya hesabınıza giriş bilgisi istemez."
    )

    keyboard = site_keyboard()

    image_id = load_image()

    # --------------------------------------------------------
    # GÖRSEL VARSA
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # GÖRSEL YOKSA
    # --------------------------------------------------------

    await query.message.reply_text(
        text,
        parse_mode="HTML",
        reply_markup=keyboard
    )


# ============================================================
# BOT
# ============================================================

def main():

    # --------------------------------------------------------
    # TOKEN KONTROLÜ
    # --------------------------------------------------------

    if not BOT_TOKEN:

        raise RuntimeError(
            "BOT_TOKEN bulunamadı. "
            "Railway Variables kısmına BOT_TOKEN ekle."
        )

    # --------------------------------------------------------
    # APPLICATION
    # --------------------------------------------------------

    application = (
        Application
        .builder()
        .token(BOT_TOKEN)
        .build()
    )

    # --------------------------------------------------------
    # /site
    # --------------------------------------------------------

    application.add_handler(
        CommandHandler(
            "site",
            site_command
        )
    )

    # --------------------------------------------------------
    # /setimage
    # --------------------------------------------------------

    application.add_handler(
        CommandHandler(
            "setimage",
            setimage_command
        )
    )

    # --------------------------------------------------------
    # /siteimage
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # MODERASYON
    # --------------------------------------------------------

    application.add_handler(
        MessageHandler(
            filters.TEXT | filters.Caption(),
            moderation_handler
        ),
        group=1
    )

    # --------------------------------------------------------
    # BAŞLAT
    # --------------------------------------------------------

    print(
        "🤖 HEROPRIME moderasyon botu çalışıyor..."
    )

    application.run_polling()


# ============================================================
# BAŞLANGIÇ
# ============================================================

if __name__ == "__main__":
    main()
