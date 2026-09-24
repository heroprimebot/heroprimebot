import os
import json
import re
import html
import logging
from pathlib import Path

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    ConversationHandler,
    filters,
)

# ============================================================
# AYARLAR
# ============================================================

# Güvenlik nedeniyle token'ı Railway Variables > BOT_TOKEN'dan alır.
# BOT_TOKEN ortam değişkeni yoksa mevcut token ile çalıştırmaz.
BOT_TOKEN = '8862557397:AAGlsz2UrF-1WXnMEmEI7KAVNJpdKTN2W1A'

# Railway Variables içine:
# ADMIN_IDS=123456789,987654321
# şeklinde Telegram kullanıcı ID'lerini yaz.
ADMIN_IDS = {
    int(x.strip())
    for x in os.getenv("ADMIN_IDS", "").split(",")
    if x.strip().isdigit()
}

# İstersen tek bir yönetici kullanıcı adı da ekleyebilirsin.
# Örn: ADMIN_USERNAMES=HeroPrimeMarketing
ADMIN_USERNAMES = {
    x.strip().lstrip("@").lower()
    for x in os.getenv("ADMIN_USERNAMES", "").split(",")
    if x.strip()
}

DATA_FILE = Path(os.getenv("DATA_FILE", "bot_data.json"))

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ============================================================
# BAŞLANGIÇ VERİLERİ
# ============================================================

DEFAULT_SITES = [
    {"name": "JASİNO 2.000 TL", "url": "https://jasino.to/4ZD8"},
    {"name": "GALYABET 2.000 TL", "url": "https://t.ly/4HEqX"},
    {"name": "MİLANBAHİS 500 TL", "url": "https://kisal.site/heroprime"},
    {"name": "BETWINNER", "url": "https://bwref-l4ftkntp.com/1Px4?p=%2Fregistration%2F"},
    {"name": "BİZBET", "url": "https://refpa-0768.com/L?tag=d_2106249m_62079c_&site=2106249&ad=62079&r=registration/"},
    {"name": "HEROPRIME WEB", "url": "https://heroprime68.com/"},
]

DEFAULT_COMMANDS = {
    "kampanya": {
        "text": "🔥 <b>KAMPANYA</b>\n\nKampanya içeriğini yönetim panelinden düzenleyebilirsin.",
        "image_id": None,
    },
    "bonus": {
        "text": "🎁 <b>BONUS</b>\n\nBonus içeriğini yönetim panelinden düzenleyebilirsin.",
        "image_id": None,
    },
    "vip": {
        "text": "💎 <b>VIP</b>\n\nVIP içeriğini yönetim panelinden düzenleyebilirsin.",
        "image_id": None,
    },
    "telegram": {
        "text": "📱 <b>TELEGRAM</b>\n\nTelegram içeriğini yönetim panelinden düzenleyebilirsin.",
        "image_id": None,
    },
    "destek": {
        "text": "🆘 <b>DESTEK</b>\n\nDestek içeriğini yönetim panelinden düzenleyebilirsin.",
        "image_id": None,
    },
    "kurallar": {
        "text": "📜 <b>KURALLAR</b>\n\nKurallar içeriğini yönetim panelinden düzenleyebilirsin.",
        "image_id": None,
    },
}

DEFAULT_DATA = {
    "sites": DEFAULT_SITES,
    "commands": DEFAULT_COMMANDS,
    "site_image_id": None,
}

# ============================================================
# VERİTABANI / JSON
# ============================================================

def load_data():
    if not DATA_FILE.exists():
        save_data(DEFAULT_DATA)
        return json.loads(json.dumps(DEFAULT_DATA, ensure_ascii=False))

    try:
        with DATA_FILE.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        logger.exception("Veri dosyası okunamadı; varsayılan veri kullanılıyor.")
        data = json.loads(json.dumps(DEFAULT_DATA, ensure_ascii=False))

    data.setdefault("sites", [])
    data.setdefault("commands", {})
    data.setdefault("site_image_id", None)

    return data


def save_data(data):
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    temp = DATA_FILE.with_suffix(".tmp")
    with temp.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    temp.replace(DATA_FILE)


DATA = load_data()

# ============================================================
# YARDIMCI FONKSİYONLAR
# ============================================================

def normalize_text(text):
    text = (text or "").strip().lower()
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

    return re.sub(r"[^a-z0-9]", "", text)


def clean_command_name(value):
    value = (value or "").strip().lower()
    if value.startswith("!"):
        value = value[1:]
    elif value.startswith("."):
        value = value[1:]

    value = value.split()[0] if value.split() else ""
    value = normalize_text(value)

    if not value:
        return None

    if not re.fullmatch(r"[a-z0-9_]+", value):
        return None

    return value[:50]


def clean_site_name(value):
    return re.sub(r"\s+", " ", (value or "").strip())[:100]


def is_admin(update):
    user = update.effective_user
    if not user:
        return False

    if user.id in ADMIN_IDS:
        return True

    username = (user.username or "").lower()
    return username in ADMIN_USERNAMES


async def require_admin(update):
    if is_admin(update):
        return True

    if update.message:
        await update.message.reply_text("❌ Bu panel sadece bot yöneticilerine açıktır.")
    elif update.callback_query:
        await update.callback_query.answer(
            "❌ Yönetici yetkin yok.",
            show_alert=True,
        )
    return False


def site_by_name(name):
    wanted = normalize_text(name)
    for site in DATA["sites"]:
        if normalize_text(site["name"]) == wanted:
            return site
    return None


def command_by_name(name):
    return DATA["commands"].get(clean_command_name(name) or "")


def admin_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("➕ Site Ekle", callback_data="admin:add_site"),
            InlineKeyboardButton("🗑️ Site Sil", callback_data="admin:delete_site"),
        ],
        [
            InlineKeyboardButton("✏️ Site Düzenle", callback_data="admin:edit_site"),
        ],
        [
            InlineKeyboardButton("➕ Komut Ekle", callback_data="admin:add_command"),
            InlineKeyboardButton("🗑️ Komut Sil", callback_data="admin:delete_command"),
        ],
        [
            InlineKeyboardButton("🖼️ Görsel Ekle", callback_data="admin:add_image"),
            InlineKeyboardButton("🗑️ Görsel Sil", callback_data="admin:delete_image"),
        ],
        [
            InlineKeyboardButton("📋 Mevcut Siteleri Gör", callback_data="admin:list_sites"),
        ],
        [
            InlineKeyboardButton("📋 Mevcut Komutları Gör", callback_data="admin:list_commands"),
        ],
    ])


def cancel_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("❌ İptal", callback_data="admin:cancel")]
    ])


# ============================================================
# SİTE MENÜSÜ
# ============================================================

def site_keyboard():
    buttons = []

    for site in DATA["sites"]:
        buttons.append([
            InlineKeyboardButton(
                f"💎 {site['name']}",
                url=site["url"],
            )
        ])

    return InlineKeyboardMarkup(buttons) if buttons else None


def site_menu_text():
    return (
        "🌐 <b>HEROPRIME SİTE MENÜSÜ</b>\n\n"
        "Aşağıdaki sitelerden istediğine ulaşabilirsin.\n\n"
        "⚠️ <b>Dikkat!</b>\n"
        "Hiçbir yönetici sizden özel mesaj yoluyla para talep etmez "
        "veya hesap giriş bilgisi istemez."
    )


async def send_site_menu_message(message):
    if not DATA["sites"]:
        await message.reply_text("📭 Henüz eklenmiş site bulunmuyor.")
        return

    keyboard = site_keyboard()
    image_id = DATA.get("site_image_id")

    if image_id:
        try:
            await message.reply_photo(
                photo=image_id,
                caption=site_menu_text(),
                parse_mode="HTML",
                reply_markup=keyboard,
            )
            return
        except Exception:
            logger.exception("Site görseli gönderilemedi.")

    await message.reply_text(
        site_menu_text(),
        parse_mode="HTML",
        reply_markup=keyboard,
    )


async def send_single_site(message, site):
    text = (
        f"🌐 <b>{html.escape(site['name'])}</b>\n\n"
        f"🔗 Siteye gitmek için aşağıdaki butona tıklayabilirsin."
    )

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"🚀 {site['name']}", url=site["url"])],
        [InlineKeyboardButton("🌐 Tüm Siteler", callback_data="public:sites")],
    ])

    await message.reply_text(
        text,
        parse_mode="HTML",
        reply_markup=keyboard,
    )


# ============================================================
# DİNAMİK KOMUTLAR
# ============================================================

async def send_dynamic_command(message, command_name):
    command = command_by_name(command_name)

    if not command:
        return False

    text = command.get("text") or ""
    image_id = command.get("image_id")

    if image_id:
        try:
            await message.reply_photo(
                photo=image_id,
                caption=text,
                parse_mode="HTML",
            )
            return True
        except Exception:
            logger.exception("Komut görseli gönderilemedi.")

    await message.reply_text(
        text or "ℹ️ Bu komut için henüz içerik girilmedi.",
        parse_mode="HTML",
    )
    return True


# ============================================================
# MODERASYON
# ============================================================

BAD_WORDS = {
    "ornek1",
    "ornek2",
    "ornek3",
}


def contains_bad_word(text):
    normalized = normalize_text(text)
    return any(normalize_text(word) in normalized for word in BAD_WORDS)


async def delete_warning(context):
    data = context.job.data
    try:
        await context.bot.delete_message(
            chat_id=data["chat_id"],
            message_id=data["message_id"],
        )
    except Exception:
        pass


async def moderation_handler(update, context):
    if not update.message:
        return

    if update.effective_chat.type not in ("group", "supergroup"):
        return

    if not update.effective_user or update.effective_user.is_bot:
        return

    text = update.message.text or update.message.caption or ""
    if not text or not contains_bad_word(text):
        return

    try:
        member = await update.effective_chat.get_member(
            update.effective_user.id
        )
        if member.status in ("administrator", "creator"):
            return
    except Exception:
        return

    try:
        await update.message.delete()
    except Exception:
        return

    try:
        warning = await update.effective_chat.send_message(
            "⚠️ Uygunsuz/küfürlü mesaj silindi."
        )
        context.job_queue.run_once(
            delete_warning,
            10,
            data={
                "chat_id": update.effective_chat.id,
                "message_id": warning.message_id,
            },
        )
    except Exception:
        pass


# ============================================================
# /start - YÖNETİM PANELİ
# ============================================================

async def start_command(update, context):
    if update.effective_chat.type != "private":
        return

    if not await require_admin(update):
        return

    await update.message.reply_text(
        "🎛️ <b>HEROPRIME YÖNETİM PANELİ</b>\n\n"
        "Buradan siteleri, dinamik komutları ve görselleri yönetebilirsin.",
        parse_mode="HTML",
        reply_markup=admin_keyboard(),
    )


# ============================================================
# ADMIN PANEL CALLBACK
# ============================================================

async def admin_callback(update, context):
    query = update.callback_query
    await query.answer()

    if not is_admin(update):
        await query.answer("❌ Yetkin yok.", show_alert=True)
        return

    action = query.data

    if action == "admin:cancel":
        context.user_data.clear()
        await query.edit_message_text(
            "❌ İşlem iptal edildi.",
            reply_markup=admin_keyboard(),
        )
        return

    if action == "admin:add_site":
        context.user_data.clear()
        context.user_data["admin_action"] = "add_site_name"
        await query.edit_message_text(
            "➕ <b>Site Ekle</b>\n\n"
            "Site adını gönder.\n"
            "Örnek: <code>JASİNO</code>",
            parse_mode="HTML",
            reply_markup=cancel_keyboard(),
        )
        return

    if action == "admin:delete_site":
        if not DATA["sites"]:
            await query.edit_message_text(
                "📭 Silinecek site yok.",
                reply_markup=admin_keyboard(),
            )
            return

        context.user_data.clear()
        context.user_data["admin_action"] = "delete_site"
        await query.edit_message_text(
            "🗑️ <b>Site Sil</b>\n\n"
            "Silmek istediğin sitenin adını gönder.\n"
            "Örnek: <code>JASİNO</code>",
            parse_mode="HTML",
            reply_markup=cancel_keyboard(),
        )
        return

    if action == "admin:edit_site":
        context.user_data.clear()
        context.user_data["admin_action"] = "edit_site_name"
        await query.edit_message_text(
            "✏️ <b>Site Düzenle</b>\n\n"
            "Düzenlemek istediğin sitenin mevcut adını gönder.",
            parse_mode="HTML",
            reply_markup=cancel_keyboard(),
        )
        return

    if action == "admin:add_command":
        context.user_data.clear()
        context.user_data["admin_action"] = "add_command_name"
        await query.edit_message_text(
            "➕ <b>Komut Ekle</b>\n\n"
            "Komut adını gönder.\n"
            "Örnek: <code>kampanya</code>\n\n"
            "Grupta kullanım: <code>!kampanya</code>",
            parse_mode="HTML",
            reply_markup=cancel_keyboard(),
        )
        return

    if action == "admin:delete_command":
        if not DATA["commands"]:
            await query.edit_message_text(
                "📭 Silinecek komut yok.",
                reply_markup=admin_keyboard(),
            )
            return

        context.user_data.clear()
        context.user_data["admin_action"] = "delete_command"
        await query.edit_message_text(
            "🗑️ <b>Komut Sil</b>\n\n"
            "Silmek istediğin komutu gönder.\n"
            "Örnek: <code>kampanya</code> veya <code>!kampanya</code>",
            parse_mode="HTML",
            reply_markup=cancel_keyboard(),
        )
        return

    if action == "admin:add_image":
        context.user_data.clear()
        context.user_data["admin_action"] = "choose_image_target"
        await query.edit_message_text(
            "🖼️ <b>Görsel Ekle</b>\n\n"
            "Görseli nereye eklemek istiyorsun?\n\n"
            "1️⃣ <b>site</b> yazarsan site menüsünün görseli olur.\n"
            "2️⃣ Bir komut adı yazarsan o komutun görseli olur.\n\n"
            "Örnek: <code>kampanya</code>",
            parse_mode="HTML",
            reply_markup=cancel_keyboard(),
        )
        return

    if action == "admin:delete_image":
        context.user_data.clear()
        context.user_data["admin_action"] = "delete_image_target"
        await query.edit_message_text(
            "🗑️ <b>Görsel Sil</b>\n\n"
            "<code>site</code> yazarak site menüsü görselini,\n"
            "veya komut adı yazarak o komutun görselini silebilirsin.",
            parse_mode="HTML",
            reply_markup=cancel_keyboard(),
        )
        return

    if action == "admin:list_sites":
        if not DATA["sites"]:
            text = "📭 Henüz site eklenmemiş."
        else:
            lines = ["📋 <b>MEVCUT SİTELER</b>\n"]
            for i, site in enumerate(DATA["sites"], 1):
                lines.append(
                    f"{i}. <b>{html.escape(site['name'])}</b>\n"
                    f"🔗 {html.escape(site['url'])}"
                )
            text = "\n\n".join(lines)

        await query.edit_message_text(
            text,
            parse_mode="HTML",
            reply_markup=admin_keyboard(),
        )
        return

    if action == "admin:list_commands":
        if not DATA["commands"]:
            text = "📭 Henüz dinamik komut eklenmemiş."
        else:
            lines = ["📋 <b>MEVCUT KOMUTLAR</b>\n"]
            for name, item in DATA["commands"].items():
                has_image = "🖼️" if item.get("image_id") else "📝"
                lines.append(
                    f"{has_image} <code>!{html.escape(name)}</code>\n"
                    f"{html.escape((item.get('text') or '')[:120])}"
                )
            text = "\n\n".join(lines)

        await query.edit_message_text(
            text,
            parse_mode="HTML",
            reply_markup=admin_keyboard(),
        )
        return


# ============================================================
# ADMIN'DEN GELEN METİN
# ============================================================

async def admin_private_text(update, context):
    if update.effective_chat.type != "private":
        return

    if not is_admin(update):
        return

    action = context.user_data.get("admin_action")
    if not action:
        return

    value = (update.message.text or "").strip()

    if action == "add_site_name":
        name = clean_site_name(value)
        if not name:
            await update.message.reply_text("❌ Geçerli bir site adı gönder.")
            return

        if site_by_name(name):
            await update.message.reply_text(
                "❌ Bu isimde bir site zaten var. Farklı bir isim gönder."
            )
            return

        context.user_data["new_site_name"] = name
        context.user_data["admin_action"] = "add_site_url"

        await update.message.reply_text(
            f"✅ Site adı: <b>{html.escape(name)}</b>\n\n"
            "Şimdi site URL'sini gönder.\n"
            "Örnek: <code>https://ornek.com</code>",
            parse_mode="HTML",
            reply_markup=cancel_keyboard(),
        )
        return

    if action == "add_site_url":
        url = value
        if not re.match(r"^https?://", url, re.I):
            await update.message.reply_text(
                "❌ URL http:// veya https:// ile başlamalı."
            )
            return

        name = context.user_data.get("new_site_name")
        DATA["sites"].append({"name": name, "url": url})
        save_data(DATA)
        context.user_data.clear()

        await update.message.reply_text(
            f"✅ <b>{html.escape(name)}</b> başarıyla eklendi.\n\n"
            "Grupta <code>!site</code> ile menüde görünür.",
            parse_mode="HTML",
            reply_markup=admin_keyboard(),
        )
        return

    if action == "delete_site":
        site = site_by_name(value)
        if not site:
            await update.message.reply_text("❌ Bu isimde site bulunamadı.")
            return

        DATA["sites"].remove(site)
        save_data(DATA)
        context.user_data.clear()

        await update.message.reply_text(
            f"🗑️ <b>{html.escape(site['name'])}</b> silindi.",
            parse_mode="HTML",
            reply_markup=admin_keyboard(),
        )
        return

    if action == "edit_site_name":
        site = site_by_name(value)
        if not site:
            await update.message.reply_text("❌ Bu isimde site bulunamadı.")
            return

        context.user_data["edit_site_old_name"] = site["name"]
        context.user_data["admin_action"] = "edit_site_new_name"

        await update.message.reply_text(
            f"✏️ Mevcut site: <b>{html.escape(site['name'])}</b>\n\n"
            "Yeni site adını gönder.",
            parse_mode="HTML",
            reply_markup=cancel_keyboard(),
        )
        return

    if action == "edit_site_new_name":
        old_name = context.user_data.get("edit_site_old_name")
        site = site_by_name(old_name)
        new_name = clean_site_name(value)

        if not site:
            context.user_data.clear()
            await update.message.reply_text("❌ Site bulunamadı.")
            return

        if not new_name:
            await update.message.reply_text("❌ Geçerli bir isim gönder.")
            return

        context.user_data["edit_site_new_name"] = new_name
        context.user_data["admin_action"] = "edit_site_url"

        await update.message.reply_text(
            "🔗 Şimdi yeni URL'yi gönder.\n\n"
            "Mevcut URL'yi korumak istiyorsan mevcut URL'yi tekrar gönderebilirsin.",
            reply_markup=cancel_keyboard(),
        )
        return

    if action == "edit_site_url":
        old_name = context.user_data.get("edit_site_old_name")
        new_name = context.user_data.get("edit_site_new_name")
        site = site_by_name(old_name)

        if not site:
            context.user_data.clear()
            await update.message.reply_text("❌ Site bulunamadı.")
            return

        if not re.match(r"^https?://", value, re.I):
            await update.message.reply_text(
                "❌ URL http:// veya https:// ile başlamalı."
            )
            return

        site["name"] = new_name
        site["url"] = value
        save_data(DATA)
        context.user_data.clear()

        await update.message.reply_text(
            f"✅ Site güncellendi: <b>{html.escape(new_name)}</b>",
            parse_mode="HTML",
            reply_markup=admin_keyboard(),
        )
        return

    if action == "add_command_name":
        name = clean_command_name(value)
        if not name:
            await update.message.reply_text(
                "❌ Geçerli bir komut adı gönder. Örnek: kampanya"
            )
            return

        if name in DATA["commands"]:
            await update.message.reply_text(
                "❌ Bu komut zaten var. Mevcut komutu düzenlemek için tekrar ekleme; "
                "komut içeriğini aşağıdaki panelden güncelleyebilirsin."
            )
            return

        DATA["commands"][name] = {"text": "", "image_id": None}
        context.user_data["editing_command"] = name
        context.user_data["admin_action"] = "command_text"

        await update.message.reply_text(
            f"✅ <code>!{name}</code> oluşturuldu.\n\n"
            "Şimdi komutun vereceği metni gönder.\n"
            "HTML kullanabilirsin: <code>&lt;b&gt;kalın&lt;/b&gt;</code>\n\n"
            "Grupta bu komut yazıldığında sadece bu içerik çıkacak.",
            parse_mode="HTML",
            reply_markup=cancel_keyboard(),
        )
        return

    if action == "command_text":
        name = context.user_data.get("editing_command")
        if not name or name not in DATA["commands"]:
            context.user_data.clear()
            await update.message.reply_text("❌ Komut bulunamadı.")
            return

        DATA["commands"][name]["text"] = value
        save_data(DATA)

        context.user_data.clear()

        await update.message.reply_text(
            f"✅ <code>!{name}</code> içeriği kaydedildi.\n\n"
            "İstersen yönetim panelinden bu komuta görsel ekleyebilirsin.",
            parse_mode="HTML",
            reply_markup=admin_keyboard(),
        )
        return

    if action == "delete_command":
        name = clean_command_name(value)
        if not name or name not in DATA["commands"]:
            await update.message.reply_text("❌ Bu komut bulunamadı.")
            return

        del DATA["commands"][name]
        save_data(DATA)
        context.user_data.clear()

        await update.message.reply_text(
            f"🗑️ <code>!{name}</code> silindi.",
            parse_mode="HTML",
            reply_markup=admin_keyboard(),
        )
        return

    if action == "choose_image_target":
        if normalize_text(value) == "site":
            context.user_data["image_target"] = "site"
            context.user_data["admin_action"] = "receive_image"
            await update.message.reply_text(
                "🖼️ Site menüsü için görsel seçildi.\n\n"
                "Şimdi fotoğrafı gönder.",
                reply_markup=cancel_keyboard(),
            )
            return

        name = clean_command_name(value)
        if not name or name not in DATA["commands"]:
            await update.message.reply_text(
                "❌ Böyle bir komut yok. Örneğin <code>kampanya</code> yaz.",
                parse_mode="HTML",
            )
            return

        context.user_data["image_target"] = name
        context.user_data["admin_action"] = "receive_image"

        await update.message.reply_text(
            f"🖼️ <code>!{name}</code> için görsel seçildi.\n\n"
            "Şimdi fotoğrafı gönder.",
            parse_mode="HTML",
            reply_markup=cancel_keyboard(),
        )
        return

    if action == "delete_image_target":
        if normalize_text(value) == "site":
            DATA["site_image_id"] = None
            save_data(DATA)
            context.user_data.clear()
            await update.message.reply_text(
                "🗑️ Site menüsü görseli silindi.",
                reply_markup=admin_keyboard(),
            )
            return

        name = clean_command_name(value)
        if not name or name not in DATA["commands"]:
            await update.message.reply_text("❌ Böyle bir komut bulunamadı.")
            return

        DATA["commands"][name]["image_id"] = None
        save_data(DATA)
        context.user_data.clear()

        await update.message.reply_text(
            f"🗑️ <code>!{name}</code> görseli silindi.",
            parse_mode="HTML",
            reply_markup=admin_keyboard(),
        )
        return


# ============================================================
# ADMIN FOTOĞRAF AL
# ============================================================

async def admin_receive_photo(update, context):
    if update.effective_chat.type != "private":
        return

    if not is_admin(update):
        return

    if context.user_data.get("admin_action") != "receive_image":
        return

    if not update.message or not update.message.photo:
        return

    photo = update.message.photo[-1]
    target = context.user_data.get("image_target")

    if target == "site":
        DATA["site_image_id"] = photo.file_id
        result = "site menüsü"
    elif target in DATA["commands"]:
        DATA["commands"][target]["image_id"] = photo.file_id
        result = f"!{target} komutu"
    else:
        context.user_data.clear()
        await update.message.reply_text("❌ Görsel hedefi bulunamadı.")
        return

    save_data(DATA)
    context.user_data.clear()

    await update.message.reply_text(
        f"✅ Görsel {result} için kaydedildi.",
        reply_markup=admin_keyboard(),
    )


# ============================================================
# PUBLIC TEXT KOMUTLARI
# ============================================================

async def public_text_commands(update, context):
    if not update.message or not update.message.text:
        return

    if update.effective_chat.type not in ("group", "supergroup"):
        return

    raw = update.message.text.strip()

    # !site / .site / !site JASİNO
    match = re.fullmatch(r"[!.]site(?:\s+(.+))?", raw, re.I)
    if match:
        site_name = (match.group(1) or "").strip()

        if site_name:
            site = site_by_name(site_name)
            if site:
                await send_single_site(update.message, site)
            else:
                await update.message.reply_text(
                    "❌ Bu isimde bir site bulunamadı."
                )
        else:
            await send_site_menu_message(update.message)
        return

    # Dinamik !komut / .komut
    match = re.fullmatch(r"[!.]([A-Za-z0-9_]+)", raw)
    if not match:
        return

    command_name = clean_command_name(match.group(1))
    if not command_name:
        return

    await send_dynamic_command(update.message, command_name)


# ============================================================
# /site
# ============================================================

async def site_command(update, context):
    if not update.message:
        return

    await send_site_menu_message(update.message)


# ============================================================
# BUTONLAR
# ============================================================

async def public_callback(update, context):
    query = update.callback_query
    await query.answer()

    if query.data == "public:sites":
        if not DATA["sites"]:
            await query.message.reply_text("📭 Henüz site bulunmuyor.")
            return

        keyboard = site_keyboard()
        image_id = DATA.get("site_image_id")

        if image_id:
            try:
                await query.message.reply_photo(
                    photo=image_id,
                    caption=site_menu_text(),
                    parse_mode="HTML",
                    reply_markup=keyboard,
                )
                return
            except Exception:
                pass

        await query.message.reply_text(
            site_menu_text(),
            parse_mode="HTML",
            reply_markup=keyboard,
        )


# ============================================================
# /setimage ve /siteimage - GERİYE DÖNÜK UYUMLULUK
# ============================================================

async def setimage_command(update, context):
    if not await require_admin(update):
        return

    if update.effective_chat.type != "private":
        await update.message.reply_text(
            "ℹ️ Görsel yönetimini özelden /start panelinden yap."
        )
        return

    context.user_data.clear()
    context.user_data["admin_action"] = "choose_image_target"

    await update.message.reply_text(
        "🖼️ Görsel eklemek için hedefi gönder:\n\n"
        "<code>site</code> veya bir komut adı (örn. <code>kampanya</code>)",
        parse_mode="HTML",
        reply_markup=cancel_keyboard(),
    )


async def siteimage_command(update, context):
    image_id = DATA.get("site_image_id")

    if not image_id:
        await update.message.reply_text("❌ Site görseli ayarlanmamış.")
        return

    await update.message.reply_photo(
        photo=image_id,
        caption="🖼️ Mevcut site menüsü görseli",
    )


# ============================================================
# HATA YAKALAMA
# ============================================================

async def error_handler(update, context):
    logger.exception("Bot hatası:", exc_info=context.error)


# ============================================================
# MAIN
# ============================================================

def main():
    if not BOT_TOKEN:
        raise RuntimeError(
            "BOT_TOKEN bulunamadı. Railway Variables içine BOT_TOKEN ekle."
        )

    if not ADMIN_IDS and not ADMIN_USERNAMES:
        logger.warning(
            "ADMIN_IDS / ADMIN_USERNAMES ayarlanmadı. "
            "Özel yönetim paneline kimse erişemez."
        )

    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .build()
    )

    # Özelden /start -> yönetim paneli
    application.add_handler(
        CommandHandler("start", start_command)
    )

    # /site
    application.add_handler(
        CommandHandler("site", site_command)
    )

    # Eski görsel komutları
    application.add_handler(
        CommandHandler("setimage", setimage_command)
    )
    application.add_handler(
        CommandHandler("siteimage", siteimage_command)
    )

    # Admin panel butonları
    application.add_handler(
        CallbackQueryHandler(
            admin_callback,
            pattern=r"^admin:"
        )
    )

    # Public site menüsü butonları
    application.add_handler(
        CallbackQueryHandler(
            public_callback,
            pattern=r"^public:"
        )
    )

    # Admin özel mesaj fotoğrafı
    application.add_handler(
        MessageHandler(
            filters.ChatType.PRIVATE & filters.PHOTO,
            admin_receive_photo,
        )
    )

    # Admin özel mesaj metinleri
    application.add_handler(
        MessageHandler(
            filters.ChatType.PRIVATE
            & filters.TEXT
            & ~filters.COMMAND,
            admin_private_text,
        )
    )

    # Gruptaki !site, !site JASİNO ve dinamik !komutlar
    application.add_handler(
        MessageHandler(
            filters.ChatType.GROUPS
            & filters.TEXT
            & ~filters.COMMAND,
            public_text_commands,
        )
    )

    # Küfür/hakaret moderasyonu en sonda çalışır.
    application.add_handler(
        MessageHandler(
            filters.ChatType.GROUPS
            & (filters.TEXT | filters.Caption()),
            moderation_handler,
        ),
        group=1,
    )

    application.add_error_handler(error_handler)

    print("🤖 HEROPRIME yönetim + site + dinamik komut + moderasyon botu çalışıyor...")
    application.run_polling()


if __name__ == "__main__":
    main()
