import os
import time
import threading
import datetime
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request, session, redirect, url_for, send_from_directory
import requests
from functools import wraps
from datetime import timedelta
import mysql.connector
from flask_cors import CORS  # To allow cross-origin requests from your HTML file
import pathlib
import json
from concurrent.futures import ThreadPoolExecutor, as_completed

# Load environment variables from .env file
# Load environment variables from .env file
current_dir = pathlib.Path(__file__).parent
dotenv_path = current_dir / 'flask.env'
dotenv_path = dotenv_path.resolve()

if dotenv_path.exists():
    load_dotenv(dotenv_path)
    print(f"OK Loaded environment variables from: {dotenv_path}")
else:
    print(f"FAIL Warning: flask.env not found at {dotenv_path}")

flaskuser = os.getenv("flaskuser")
flaskpassword = os.getenv("flaskpassword")

# Discord OAuth Config
DISCORD_CLIENT_ID = os.getenv("DISCORD_CLIENT_ID")
DISCORD_CLIENT_SECRET = os.getenv("DISCORD_CLIENT_SECRET")
DISCORD_REDIRECT_URI = os.getenv("DISCORD_REDIRECT_URI")
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
DISCORD_GUILD_ID = os.getenv("DISCORD_GUILD_ID")
COUNCIL_ROLE_IDS = os.getenv("COUNCIL_ROLE_IDS", "").split(",")

print(f"DISCORD_CLIENT_ID loaded: {DISCORD_CLIENT_ID is not None}")


# Flask app with custom template folder
parent_dir = current_dir.parent  # www/
template_folder = parent_dir / 'html'
app = Flask(__name__, template_folder=str(template_folder))

app.secret_key = os.getenv("SECRET_KEY", "change-this-secret-key")
app.config['SESSION_COOKIE_SECURE'] = False  # Set to True in production with HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)

CORS(app, supports_credentials=True)

# Discord API endpoint
DISCORD_API_ENDPOINT = "https://discord.com/api/v10"

# MySQL Database Configuration for sanity2
DB_CONFIG = {
    'host': 'localhost',
    'user': f'{flaskuser}',
    'password': f'{flaskpassword}',
    'database': 'sanity2'
}

# MySQL Database Configuration for the new bingo schema
BINGO_DB_CONFIG = {
    'host': 'localhost',
    'user': f'{flaskuser}',
    'password': f'{flaskpassword}',
    'database': 'sanitybingo'
}

# MySQL Database Configuration for the money grab schema
MONEYGRAB_DB_CONFIG = {
    'host': 'localhost',
    'user': f'{flaskuser}',
    'password': f'{flaskpassword}',
    'database': 'sanitymoneygrab'
}


# --- TEAM LOGO UPLOADS ---
TEAM_IMAGE_DIR = os.path.join(current_dir, 'uploads', 'team_images')
ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
MAX_UPLOAD_SIZE = 5 * 1024 * 1024  # 5 MB


# --- WISEOLDMAN KC SYNC ---

WOM_API_BASE = "https://api.wiseoldman.net/v2"
WOM_SYNC_LOCK_NAME = "sanity_bingo_wom_sync"
WOM_SYNC_INTERVAL_SECONDS = 60 * 60

# Full list of WiseOldMan boss metrics. New bosses can be added here; any boss
# already present in bingobosskc / bingo_boss_mapping is included automatically.
WOM_BOSS_METRICS = [
    'abyssal_sire', 'alchemical_hydra', 'amoxliatl', 'araxxor', 'artio', 'barrows_chests',
    'brutus', 'bryophyta', 'callisto', 'calvarion', 'cerberus', 'chambers_of_xeric',
    'chambers_of_xeric_challenge_mode', 'chaos_elemental', 'chaos_fanatic', 'commander_zilyana',
    'corporeal_beast', 'crazy_archaeologist', 'dagannoth_prime', 'dagannoth_rex',
    'dagannoth_supreme', 'deranged_archaeologist', 'doom_of_mokhaiotl', 'duke_sucellus',
    'general_graardor', 'giant_mole', 'grotesque_guardians', 'hespori', 'kalphite_queen',
    'king_black_dragon', 'kraken', 'kreearra', 'kril_tsutsaroth', 'lunar_chests', 'mad_angel',
    'maggot_king', 'mimic', 'nex', 'nightmare', 'phosanis_nightmare', 'obor', 'phantom_muspah',
    'sarachnis', 'scorpia', 'scurrius', 'shellbane_gryphon', 'skotizo', 'sol_heredit', 'spindel',
    'tempoross', 'the_gauntlet', 'the_corrupted_gauntlet', 'the_hueycoatl', 'the_leviathan',
    'the_royal_titans', 'the_whisperer', 'theatre_of_blood', 'theatre_of_blood_hard_mode',
    'thermonuclear_smoke_devil', 'tombs_of_amascut', 'tombs_of_amascut_expert', 'tzkal_zuk',
    'tztok_jad', 'vardorvis', 'venenatis', 'vetion', 'vorkath', 'wintertodt', 'yama', 'zalcano',
    'zulrah',
]


def _title_case(metric):
    return metric.replace('_', ' ').title()


def _norm_name(s):
    """Lowercase and treat space/underscore interchangeably for name matching."""
    return ' '.join((s or '').lower().replace('_', ' ').split())


def _wom_get(url, timeout=30):
    wom_api_key = os.getenv('WOM_API_KEY', 'prjobo42nwlfnnjiy4sebqlb')
    headers = {'Content-Type': 'application/json', 'x-api-key': wom_api_key}
    return requests.get(url, headers=headers, timeout=timeout)


def _fetch_competition(wom_id):
    """Resolve a competition ID to its full competition payload (incl. groupId)."""
    resp = _wom_get(f"{WOM_API_BASE}/competitions/{wom_id}")
    if resp.status_code != 200:
        return None
    try:
        return resp.json()
    except ValueError:
        return None


def _get_boss_list():
    """Static WOM boss list plus any boss already tracked in the DB or mapping."""
    bosses = list(WOM_BOSS_METRICS)
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute("SHOW COLUMNS FROM sanity2.bingobosskc")
        for row in cur.fetchall():
            if row[0] != 'RSN' and row[0] not in bosses:
                bosses.append(row[0])
        cur.close()
        conn.close()
    except mysql.connector.Error:
        pass
    try:
        conn = mysql.connector.connect(**BINGO_DB_CONFIG)
        cur = conn.cursor()
        cur.execute("SELECT wom_metric FROM bingo_boss_mapping")
        for row in cur.fetchall():
            if row[0] not in bosses:
                bosses.append(row[0])
        cur.close()
        conn.close()
    except mysql.connector.Error:
        pass
    return bosses


def _fetch_competition_csv(session, wom_id, metric):
    """Fetch the participants CSV for a single boss metric. Returns text or None."""
    url = f"{WOM_API_BASE}/competitions/{wom_id}/csv?table=participants&metric={metric}"
    for attempt in range(3):
        try:
            resp = session.get(url, timeout=20)
            if resp.status_code == 200:
                return resp.text
            # 404 means this metric simply has no competition data; don't retry.
            if resp.status_code == 404:
                return None
        except requests.RequestException:
            pass
        time.sleep(0.5 * (attempt + 1))
    return None


def _parse_boss_csv(text):
    """Parse (Rank,Username,Team,Start,End,Gained,Last Updated) -> [(rsn, gained)]."""
    rows = []
    for line in text.split('\n')[1:]:
        line = line.strip()
        if not line:
            continue
        parts = line.split(',')
        if len(parts) < 6:
            continue
        rsn = parts[1].strip()
        try:
            gained = int(float(parts[5].strip()))
        except (ValueError, IndexError):
            continue
        if gained > 0:
            rows.append((rsn, gained))
    return rows


def _ensure_boss_columns(boss_metrics):
    """Add any missing boss columns to sanity2.bingobosskc. Returns count added."""
    conn = mysql.connector.connect(**DB_CONFIG)
    added = 0
    try:
        cur = conn.cursor()
        cur.execute("SHOW COLUMNS FROM sanity2.bingobosskc")
        existing = {row[0] for row in cur.fetchall()}
        for metric in boss_metrics:
            if metric not in existing:
                cur.execute(f"ALTER TABLE sanity2.bingobosskc ADD COLUMN `{metric}` INT DEFAULT 0")
                added += 1
        conn.commit()
    finally:
        conn.close()
    return added


def _ensure_boss_mapping(boss_metrics):
    """Add missing WiseOldMan -> boss name mapping entries with a title-cased default."""
    conn = mysql.connector.connect(**BINGO_DB_CONFIG)
    try:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS bingo_boss_mapping (
                wom_metric VARCHAR(64) PRIMARY KEY,
                boss_name VARCHAR(100) NOT NULL
            )
        """)
        cur.execute("SELECT wom_metric FROM bingo_boss_mapping")
        existing = {row[0] for row in cur.fetchall()}
        for metric in boss_metrics:
            if metric not in existing:
                cur.execute(
                    "INSERT INTO bingo_boss_mapping (wom_metric, boss_name) VALUES (%s, %s)",
                    (metric, _title_case(metric))
                )
        conn.commit()
    finally:
        conn.close()


def _write_kc(gains_by_rsn, fetched_bosses=None):
    """
    Zero the re-fetched boss columns then write the latest gains into
    sanity2.bingobosskc. Only zero bosses that were actually re-fetched, so a
    partial sync (e.g. a rate-limited CSV request) doesn't wipe untouched bosses.
    Returns (players, cells).
    """
    conn = mysql.connector.connect(**DB_CONFIG)
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute("SHOW COLUMNS FROM sanity2.bingobosskc")
        boss_columns = [row['Field'] for row in cur.fetchall() if row['Field'] != 'RSN']

        # Zero only the bosses that were re-fetched (or all if unspecified).
        zero_targets = fetched_bosses if fetched_bosses is not None else boss_columns
        zero_targets = [c for c in zero_targets if c in boss_columns]
        if zero_targets:
            zero_sql = ', '.join(f"`{c}` = 0" for c in zero_targets)
            cur.execute(f"UPDATE sanity2.bingobosskc SET {zero_sql}")

        players = 0
        cells = 0
        for rsn, gains in gains_by_rsn.items():
            cur.execute("SELECT RSN FROM sanity2.bingobosskc WHERE RSN = %s", (rsn,))
            if not cur.fetchone():
                cur.execute("INSERT INTO sanity2.bingobosskc (RSN) VALUES (%s)", (rsn,))

            for boss, g in gains.items():
                if boss in boss_columns:
                    cur.execute(f"UPDATE sanity2.bingobosskc SET `{boss}` = %s WHERE RSN = %s", (g, rsn))
                    cells += 1
            players += 1

        conn.commit()
        return players, cells
    finally:
        conn.close()


def _snapshot_kc(event_id):
    """
    Capture the current sanity2.bingobosskc gains into bingo_kc_snapshots so
    EHB-over-time can be charted later. Skips the insert when the data is
    unchanged since the last snapshot. Returns True when a row was written.
    """
    conn = mysql.connector.connect(**DB_CONFIG)
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute("SHOW COLUMNS FROM sanity2.bingobosskc")
        boss_columns = [row['Field'] for row in cur.fetchall() if row['Field'] != 'RSN']
        cur.execute("SELECT * FROM sanity2.bingobosskc")
        data = {}
        for row in cur.fetchall():
            rsn = row.get('RSN')
            if not rsn:
                continue
            gains = {}
            for col in boss_columns:
                val = int(row.get(col) or 0)
                if val > 0:
                    gains[col] = val
            if gains:
                data[rsn] = gains
    finally:
        conn.close()

    serialized = json.dumps(data, sort_keys=True)

    bingo_conn = mysql.connector.connect(**BINGO_DB_CONFIG)
    try:
        cur = bingo_conn.cursor(dictionary=True)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS bingo_kc_snapshots (
                id INT AUTO_INCREMENT PRIMARY KEY,
                event_id INT NOT NULL,
                snapshot_time DATETIME NOT NULL,
                data LONGTEXT NOT NULL,
                INDEX idx_event_time (event_id, snapshot_time)
            )
        """)
        cur.execute(
            "SELECT data FROM bingo_kc_snapshots WHERE event_id = %s ORDER BY id DESC LIMIT 1",
            (event_id,)
        )
        last = cur.fetchone()
        if last and last.get('data') == serialized:
            return False
        cur.execute(
            "INSERT INTO bingo_kc_snapshots (event_id, snapshot_time, data) VALUES (%s, %s, %s)",
            (event_id, datetime.datetime.now(), serialized)
        )
        bingo_conn.commit()
        return True
    finally:
        bingo_conn.close()


def _log_sync(event_id, status, message, players=0, cells=0, added_bosses=0):
    conn = mysql.connector.connect(**BINGO_DB_CONFIG)
    try:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS bingo_wom_sync_log (
                id INT AUTO_INCREMENT PRIMARY KEY,
                event_id INT,
                finished_at DATETIME,
                status VARCHAR(20),
                message TEXT,
                players INT DEFAULT 0,
                cells INT DEFAULT 0,
                added_bosses INT DEFAULT 0
            )
        """)
        cur.execute(
            "INSERT INTO bingo_wom_sync_log (event_id, finished_at, status, message, players, cells, added_bosses) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s)",
            (event_id, datetime.datetime.now(), status, message, players, cells, added_bosses)
        )
        conn.commit()
    finally:
        conn.close()


def _get_last_sync(event_id):
    conn = mysql.connector.connect(**BINGO_DB_CONFIG)
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS bingo_wom_sync_log (
                id INT AUTO_INCREMENT PRIMARY KEY,
                event_id INT,
                finished_at DATETIME,
                status VARCHAR(20),
                message TEXT,
                players INT DEFAULT 0,
                cells INT DEFAULT 0,
                added_bosses INT DEFAULT 0
            )
        """)
        cur.execute(
            "SELECT * FROM bingo_wom_sync_log WHERE event_id = %s ORDER BY id DESC LIMIT 1",
            (event_id,)
        )
        return cur.fetchone()
    finally:
        conn.close()


def sync_wom_kc(event_id=None):
    """
    Fetch boss KC gains for an event's WiseOldMan competition and update
    sanity2.bingobosskc. Fetches boss metrics in parallel via the competition
    CSV endpoint, and auto-adds any new boss columns + mapping entries.

    Returns a dict with keys: ok, message, players, cells, added_bosses.
    """
    result = {"ok": False, "message": "", "players": 0, "cells": 0, "added_bosses": 0}

    # Resolve the event (and its wom_id).
    bingo_conn = mysql.connector.connect(**BINGO_DB_CONFIG)
    try:
        cur = bingo_conn.cursor(dictionary=True)
        if event_id:
            cur.execute("SELECT id, name, wom_id, start_date, end_date, is_active FROM bingo_events WHERE id = %s", (event_id,))
        else:
            cur.execute("SELECT id, name, wom_id, start_date, end_date, is_active FROM bingo_events WHERE is_active = 1 ORDER BY id DESC LIMIT 1")
        event = cur.fetchone()
        cur.close()
    finally:
        bingo_conn.close()

    if not event or not event.get('wom_id'):
        result["message"] = "No event with a WiseOldMan competition ID found. Set it in Edit Event first."
        return result

    wom_id = event['wom_id']
    boss_list = _get_boss_list()

    # Fetch boss KC in parallel. A serial fetch of ~70 bosses exceeds the
    # gunicorn 30s worker timeout and 500s the request. requests.Session is not
    # thread-safe, so each worker thread gets its own session.
    gains_by_rsn = {}
    fetched_bosses_list = []
    thread_local = threading.local()

    def _session():
        s = getattr(thread_local, 'session', None)
        if s is None:
            s = requests.Session()
            s.headers.update({
                'Content-Type': 'application/json',
                'x-api-key': os.getenv('WOM_API_KEY', 'prjobo42nwlfnnjiy4sebqlb'),
                'User-Agent': 'Mozilla/5.0 (compatible; SanityBingo/1.0)',
            })
            thread_local.session = s
        return s

    def _fetch_one(boss):
        text = _fetch_competition_csv(_session(), wom_id, boss)
        if text is None:
            return boss, None
        return boss, _parse_boss_csv(text)

    with ThreadPoolExecutor(max_workers=6) as ex:
        futures = [ex.submit(_fetch_one, boss) for boss in boss_list]
        for fut in as_completed(futures):
            try:
                boss, rows = fut.result()
            except Exception:
                continue
            if rows is None:
                continue
            fetched_bosses_list.append(boss)
            for rsn, gained in rows:
                gains_by_rsn.setdefault(rsn, {})[boss] = gained

    fetched_bosses = len(fetched_bosses_list)

    if fetched_bosses == 0:
        result["message"] = f"Could not fetch any boss data for competition {wom_id}. Is the ID correct?"
        return result

    added = _ensure_boss_columns(boss_list)
    _ensure_boss_mapping(boss_list)
    result["added_bosses"] = added

    players, cells = _write_kc(gains_by_rsn, fetched_bosses_list)
    _snapshot_kc(event['id'])
    result.update({
        "ok": True,
        "players": players,
        "cells": cells,
        "message": f"Synced {players} players, {cells} boss KC updates from {fetched_bosses} bosses" + (f", added {added} new boss(es)" if added else ""),
    })
    return result


def _get_events_due_for_sync():
    """Return events that should be auto-synced: active flag OR now within window."""
    conn = mysql.connector.connect(**BINGO_DB_CONFIG)
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT id, name, wom_id, start_date, end_date, is_active FROM bingo_events WHERE wom_id IS NOT NULL AND wom_id > 0")
        events = cur.fetchall()
    finally:
        conn.close()

    now = datetime.datetime.now()
    due = []
    for e in events:
        in_window = False
        try:
            if e['start_date'] and e['end_date']:
                in_window = e['start_date'] <= now <= e['end_date']
        except TypeError:
            pass
        if e['is_active'] == 1 or in_window:
            due.append(e)
    return due


def _run_sync_with_lock(event_id):
    """
    Acquire a MySQL advisory lock so only one gunicorn worker syncs at a time.
    Returns the sync result dict.
    """
    lock_conn = mysql.connector.connect(**BINGO_DB_CONFIG)
    try:
        cur = lock_conn.cursor()
        cur.execute("SELECT GET_LOCK(%s, 1)", (WOM_SYNC_LOCK_NAME,))
        acquired = cur.fetchone()[0]
        cur.close()
        if not acquired:
            return {"ok": False, "skipped": True, "message": "Another worker is syncing right now."}
        try:
            return sync_wom_kc(event_id)
        finally:
            release_cur = lock_conn.cursor()
            release_cur.execute("SELECT RELEASE_LOCK(%s)", (WOM_SYNC_LOCK_NAME,))
            release_cur.close()
    finally:
        lock_conn.close()


def _wom_scheduler_loop():
    """Background thread: sync KC hourly for every active event."""
    while True:
        time.sleep(60)
        try:
            for event in _get_events_due_for_sync():
                event_id = event['id']
                last = _get_last_sync(event_id)
                if last and last.get('finished_at'):
                    delta = (datetime.datetime.now() - last['finished_at']).total_seconds()
                    if delta < WOM_SYNC_INTERVAL_SECONDS:
                        continue
                result = _run_sync_with_lock(event_id)
                if result.get('skipped'):
                    continue
                _log_sync(
                    event_id,
                    'ok' if result.get('ok') else 'error',
                    result.get('message', ''),
                    result.get('players', 0),
                    result.get('cells', 0),
                    result.get('added_bosses', 0),
                )
                print(f"[WOM sync] event {event_id}: {result.get('message')}")
        except Exception as err:
            import traceback
            traceback.print_exc()
            print(f"[WOM sync] scheduler error: {err}")


_scheduler_thread = threading.Thread(target=_wom_scheduler_loop, daemon=True)
_scheduler_thread.start()


# --- AUTHENTICATION DECORATORS AND HELPER FUNCTIONS ---

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'discord_user' not in session:
            return jsonify({"error": "Authentication required"}), 401
        return f(*args, **kwargs)

    return decorated_function


def council_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'discord_user' not in session:
            return jsonify({"error": "Authentication required"}), 401
        if not session.get('is_council', False):
            return jsonify({"error": "Council permissions required"}), 403
        return f(*args, **kwargs)

    return decorated_function


def exchange_code(code):
    data = {
        'client_id': DISCORD_CLIENT_ID,
        'client_secret': DISCORD_CLIENT_SECRET,
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': DISCORD_REDIRECT_URI
    }
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    response = requests.post(f'{DISCORD_API_ENDPOINT}/oauth2/token', data=data, headers=headers)
    response.raise_for_status()
    return response.json()


def get_user_info(access_token):
    headers = {'Authorization': f'Bearer {access_token}'}
    response = requests.get(f'{DISCORD_API_ENDPOINT}/users/@me', headers=headers)
    response.raise_for_status()
    return response.json()


def get_user_guild_member(user_id):
    headers = {'Authorization': f'Bot {DISCORD_BOT_TOKEN}'}
    response = requests.get(
        f'{DISCORD_API_ENDPOINT}/guilds/{DISCORD_GUILD_ID}/members/{user_id}',
        headers=headers
    )
    response.raise_for_status()
    return response.json()


def check_council_role(member_data):
    user_roles = member_data.get('roles', [])
    return any(role_id in COUNCIL_ROLE_IDS for role_id in user_roles)


# --- DISCORD OAUTH ROUTES ---

@app.route('/auth/login')
def discord_login():
    discord_login_url = (
        f"{DISCORD_API_ENDPOINT}/oauth2/authorize?"
        f"client_id={DISCORD_CLIENT_ID}&"
        f"redirect_uri={DISCORD_REDIRECT_URI}&"
        f"response_type=code&"
        f"scope=identify"
    )
    return redirect(discord_login_url)


@app.route('/auth/callback')
def discord_callback():
    code = request.args.get('code')
    if not code:
        return jsonify({"error": "No code provided"}), 400

    try:
        token_data = exchange_code(code)
        access_token = token_data['access_token']
        user_info = get_user_info(access_token)
        user_id = user_info['id']
        member_data = get_user_guild_member(user_id)
        is_council = check_council_role(member_data)

        session.permanent = True
        session['discord_user'] = {
            'id': user_id,
            'username': user_info['username'],
            'discriminator': user_info.get('discriminator', '0'),
            'avatar': user_info.get('avatar'),
            'global_name': user_info.get('global_name')
        }
        session['is_council'] = is_council
        session['access_token'] = access_token

        if is_council:
            return redirect('/admin.html')
        else:
            return redirect('/?error=not_council')

    except Exception as e:
        print(f"OAuth error: {e}")
        return jsonify({"error": "Authentication failed"}), 500


@app.route('/auth/logout')
def logout():
    session.clear()
    return redirect('/')


@app.route('/auth/status')
def auth_status():
    if 'discord_user' not in session:
        return jsonify({"authenticated": False})

    return jsonify({
        "authenticated": True,
        "user": session['discord_user'],
        "is_council": session.get('is_council', False)
    })


# --- ADMIN PANEL ROUTE ---

@app.route('/api/admin/drops', methods=['GET'])
@council_required
def get_drops():
    """
    Get drops with optional filtering and pagination
    Query params:
    - search: search by name
    - has_value: 'true' to show items with values, 'false' for NULL values
    - page: page number (default 1)
    - per_page: items per page (default 50, max 500)
    - sort: 'name', 'value', 'id' (default 'value')
    - order: 'asc' or 'desc' (default 'asc')
    """
    connection = None
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor(dictionary=True)

        # Get query parameters
        search = request.args.get('search', '').strip()
        has_value = request.args.get('has_value', '')
        page = max(1, int(request.args.get('page', 1)))
        per_page = min(500, max(10, int(request.args.get('per_page', 50))))
        sort_by = request.args.get('sort', 'value')
        order = request.args.get('order', 'asc')

        # Validate sort column
        valid_sorts = ['name', 'value', 'id']
        if sort_by not in valid_sorts:
            sort_by = 'value'

        # Validate order
        if order not in ['asc', 'desc']:
            order = 'asc'

        # Build WHERE clause
        where_conditions = []
        params = []

        if search:
            where_conditions.append("name LIKE %s")
            params.append(f"%{search}%")

        if has_value == 'true':
            where_conditions.append("value IS NOT NULL AND value > 0")
        elif has_value == 'false':
            where_conditions.append("(value IS NULL OR value = 0)")

        where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"

        # Get total count
        count_query = f"SELECT COUNT(*) as total FROM sanity2.drops WHERE {where_clause}"
        cursor.execute(count_query, params)
        total = cursor.fetchone()['total']

        # Get paginated results
        offset = (page - 1) * per_page

        # Special sorting: NULL values and 0 values should come last when sorting by value DESC
        if sort_by == 'value':
            if order == 'desc':
                sort_clause = "CASE WHEN value IS NULL THEN 1 WHEN value = 0 THEN 1 ELSE 0 END, value DESC"
            else:
                # For ascending, prioritize items with values, then NULL/0 values
                sort_clause = "CASE WHEN value IS NULL OR value = 0 THEN 1 ELSE 0 END, value ASC"
        else:
            sort_clause = f"{sort_by} {order.upper()}"

        query = f"""
            SELECT id, name, value
            FROM sanity2.drops
            WHERE {where_clause}
            ORDER BY {sort_clause}
            LIMIT %s OFFSET %s
        """

        params.extend([per_page, offset])
        cursor.execute(query, params)
        drops = cursor.fetchall()

        return jsonify({
            'data': drops,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'total_pages': (total + per_page - 1) // per_page
            }
        })

    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return jsonify({"error": str(err)}), 500
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()


@app.route('/api/admin/drops/<int:drop_id>', methods=['PUT'])
@council_required
def update_drop(drop_id):
    """Update a drop value"""
    data = request.get_json()
    connection = None
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor(dictionary=True)

        # Debug: Print what we're looking for
        print(f"Looking for drop_id: {drop_id}")

        # Validate value
        value = data.get('value')
        if value is not None:
            try:
                value = int(value)
            except (ValueError, TypeError):
                return jsonify({"error": "Value must be an integer or null"}), 400

        # Get the drop info FIRST - use correct query
        query = "SELECT name, value FROM sanity2.drops WHERE id = %s"
        cursor.execute(query, (drop_id,))
        drop_result = cursor.fetchone()

        # Debug: Check what we got
        print(f"Drop result: {drop_result}")

        if not drop_result:
            return jsonify({"error": "Drop not found"}), 404

        drop_name = drop_result['name']
        old_value = drop_result['value']

        # Update the drop
        update_query = "UPDATE sanity2.drops SET value = %s WHERE id = %s"
        cursor.execute(update_query, (value, drop_id))
        connection.commit()

        print(f"Updated {drop_name} from {old_value} to {value}")

        # Get Discord user ID from session
        discord_user = session.get('discord_user', {})
        discord_user_id = discord_user.get('id')

        # Try to create audit log (but don't fail if it doesn't work)
        if discord_user_id:
            try:
                # Format: ItemName:oldValue->newValue
                action_note = f"{drop_name}:{old_value if old_value is not None else 'NULL'}->{value if value is not None else 'NULL'}"

                audit_query = """
                    INSERT INTO sanity2.auditlogs (userId, affectedUsers, actionType, actionNote, actionDate) 
                    VALUES (%s, %s, %s, %s, NOW())
                """

                cursor.execute(audit_query, (discord_user_id, drop_name, 10, action_note))
                connection.commit()
                print(f"Audit log created for user {discord_user_id}")
            except mysql.connector.Error as audit_err:
                # Don't fail the update if audit logging fails
                print(f"Warning: Audit log failed: {audit_err}")
                # Still return success since the drop was updated

        return jsonify({"message": "Drop updated successfully", "name": drop_name})

    except mysql.connector.Error as err:
        if connection:
            connection.rollback()
        print(f"Database error: {err}")
        return jsonify({"error": str(err)}), 500
    except Exception as e:
        if connection:
            connection.rollback()
        print(f"Unexpected error: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()


# ============================================
# Updated bulk_update_drops endpoint
# ============================================

@app.route('/api/admin/drops/bulk-update', methods=['POST'])
@council_required
def bulk_update_drops():
    """Bulk update multiple drop values at once"""
    data = request.get_json()
    updates = data.get('updates', [])

    if not updates or not isinstance(updates, list):
        return jsonify({"error": "Invalid updates format"}), 400

    connection = None
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor(dictionary=True)

        updated_count = 0
        updated_items = []

        for update in updates:
            drop_id = update.get('id')
            value = update.get('value')

            if drop_id is None:
                continue

            # Validate value
            if value is not None:
                try:
                    value = int(value)
                except (ValueError, TypeError):
                    continue

            # Get item name before updating
            cursor.execute("SELECT name FROM sanity2.drops WHERE id = %s", (drop_id,))
            result = cursor.fetchone()
            if not result:
                continue

            item_name = result['name']

            # Update the drop
            query = "UPDATE sanity2.drops SET value = %s WHERE id = %s"
            cursor.execute(query, (value, drop_id))

            if cursor.rowcount > 0:
                updated_count += 1
                updated_items.append(f"{item_name}:{value}")

        connection.commit()

        # Create audit log for bulk update
        discord_user = session.get('discord_user', {})
        discord_user_id = discord_user.get('id')

        if discord_user_id and updated_count > 0:
            # affectedUsers = comma-separated list of first few items
            affected_text = ', '.join([item.split(':')[0] for item in updated_items[:5]])
            if len(updated_items) > 5:
                affected_text += f' +{len(updated_items) - 5} more'

            # Truncate if needed (affectedUsers is varchar(1000))
            if len(affected_text) > 950:
                affected_text = affected_text[:950] + '...'

            # actionNote = summary of changes
            action_note = f"Bulk update: {updated_count} items"

            audit_query = """
                INSERT INTO sanity2.auditlogs (userId, affectedUsers, actionType, actionNote, actionDate) 
                VALUES (%s, %s, %s, %s, NOW())
            """

            try:
                cursor.execute(audit_query, (discord_user_id, affected_text, 10, action_note))
                connection.commit()
            except mysql.connector.Error as audit_err:
                print(f"Audit log error: {audit_err}")

        return jsonify({
            "message": f"Successfully updated {updated_count} drops",
            "updated_count": updated_count
        })

    except mysql.connector.Error as err:
        if connection:
            connection.rollback()
        print(f"Error: {err}")
        return jsonify({"error": str(err)}), 500
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()


@app.route('/api/admin/drops/stats', methods=['GET'])
@council_required
def get_drops_stats():
    """Get statistics about drops"""
    connection = None
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor(dictionary=True)

        query = """
            SELECT 
                COUNT(*) as total_drops,
                COUNT(CASE WHEN value IS NOT NULL AND value > 0 THEN 1 END) as drops_with_value,
                COUNT(CASE WHEN value IS NULL OR value = 0 THEN 1 END) as drops_without_value,
                AVG(CASE WHEN value > 0 THEN value END) as avg_value,
                MAX(value) as max_value,
                MIN(CASE WHEN value > 0 THEN value END) as min_value
            FROM sanity2.drops
        """

        cursor.execute(query)
        stats = cursor.fetchone()

        return jsonify(stats)

    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return jsonify({"error": str(err)}), 500
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()

@app.route('/admin')
def admin_panel():
    if 'discord_user' not in session:
        return redirect('/auth/login')
    if not session.get('is_council', False):
        return "Access Denied: Council permissions required", 403
    return render_template('admin.html')


# --- ADMIN API ENDPOINTS ---

@app.route('/api/admin/dairies', methods=['GET'])
@council_required
def get_admin_dairies():
    connection = None
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor(dictionary=True)
        query = "SELECT * FROM sanity2.dairies ORDER BY id"
        cursor.execute(query)
        dairies = cursor.fetchall()
        return jsonify(dairies)
    except mysql.connector.Error as err:
        return jsonify({"error": str(err)}), 500
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()


@app.route('/api/admin/dairies', methods=['POST'])
@council_required
def create_admin_dairy():
    data = request.get_json()
    connection = None
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor()
        query = "INSERT INTO sanity2.dairies (name, value, description) VALUES (%s, %s, %s)"
        cursor.execute(query, (data['name'], data['value'], data.get('description', '')))
        connection.commit()
        return jsonify({"message": "Dairy created", "id": cursor.lastrowid}), 201
    except mysql.connector.Error as err:
        if connection:
            connection.rollback()
        return jsonify({"error": str(err)}), 500
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()


@app.route('/api/admin/dairies/<int:dairy_id>', methods=['PUT'])
@council_required
def update_admin_dairy(dairy_id):
    data = request.get_json()
    connection = None
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor()
        query = "UPDATE sanity2.dairies SET name = %s, value = %s, description = %s WHERE id = %s"
        cursor.execute(query, (data['name'], data['value'], data.get('description', ''), dairy_id))
        connection.commit()
        if cursor.rowcount == 0:
            return jsonify({"error": "Not found"}), 404
        return jsonify({"message": "Updated successfully"})
    except mysql.connector.Error as err:
        if connection:
            connection.rollback()
        return jsonify({"error": str(err)}), 500
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()


@app.route('/api/admin/dairies/<int:dairy_id>', methods=['DELETE'])
@council_required
def delete_admin_dairy(dairy_id):
    connection = None
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor()
        query = "DELETE FROM sanity2.dairies WHERE id = %s"
        cursor.execute(query, (dairy_id,))
        connection.commit()
        if cursor.rowcount == 0:
            return jsonify({"error": "Not found"}), 404
        return jsonify({"message": "Deleted successfully"})
    except mysql.connector.Error as err:
        if connection:
            connection.rollback()
        return jsonify({"error": str(err)}), 500
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()


@app.route('/api/admin/drop-values', methods=['GET'])
@council_required
def get_admin_drop_values():
    connection = None
    try:
        connection = mysql.connector.connect(**BINGO_DB_CONFIG)
        cursor = connection.cursor(dictionary=True)
        query = "SELECT id, bossName, item, itemPoints, droprate, hoursToGetDrop FROM bingo_boss_items ORDER BY bossName, item"
        cursor.execute(query)
        items = cursor.fetchall()
        return jsonify(items)
    except mysql.connector.Error as err:
        return jsonify({"error": str(err)}), 500
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()


@app.route('/api/admin/drop-values/<int:item_id>', methods=['PUT'])
@council_required
def update_admin_drop_value(item_id):
    data = request.get_json()
    connection = None
    try:
        connection = mysql.connector.connect(**BINGO_DB_CONFIG)
        cursor = connection.cursor()
        query = "UPDATE bingo_boss_items SET bossName=%s, item=%s, itemPoints=%s, droprate=%s, hoursToGetDrop=%s WHERE id=%s"
        cursor.execute(query, (
        data['bossName'], data['item'], data['itemPoints'], data['droprate'], data.get('hoursToGetDrop'), item_id))
        connection.commit()
        if cursor.rowcount == 0:
            return jsonify({"error": "Not found"}), 404
        return jsonify({"message": "Updated successfully"})
    except mysql.connector.Error as err:
        if connection:
            connection.rollback()
        return jsonify({"error": str(err)}), 500
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()


@app.route('/api/admin/bingowinners', methods=['GET'])
@council_required
def get_bingo_winners():
    """
    Get bingo winners with optional filtering and pagination
    Query params:
    - search: search by bingoName, teamName, or participants
    - page: page number (default 1)
    - per_page: items per page (default 50, max 500)
    - sort: 'bingoId', 'bingoName', 'teamName' (default 'bingoId')
    - order: 'asc' or 'desc' (default 'desc')
    """
    connection = None
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor(dictionary=True)

        search = request.args.get('search', '').strip()
        page = max(1, int(request.args.get('page', 1)))
        per_page = min(500, max(10, int(request.args.get('per_page', 50))))
        sort_by = request.args.get('sort', 'bingoId')
        order = request.args.get('order', 'desc')

        valid_sorts = ['bingoId', 'bingoName', 'teamName']
        if sort_by not in valid_sorts:
            sort_by = 'bingoId'

        if order not in ['asc', 'desc']:
            order = 'desc'

        where_conditions = []
        params = []

        if search:
            where_conditions.append("(bingoName LIKE %s OR teamName LIKE %s OR participants LIKE %s)")
            like_term = f"%{search}%"
            params.extend([like_term, like_term, like_term])

        where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"

        count_query = f"SELECT COUNT(*) as total FROM sanity2.bingoWinners WHERE {where_clause}"
        cursor.execute(count_query, params)
        total = cursor.fetchone()['total']

        offset = (page - 1) * per_page

        query = f"""
            SELECT bingoId, bingoName, teamName, participants
            FROM sanity2.bingoWinners
            WHERE {where_clause}
            ORDER BY {sort_by} {order.upper()}
            LIMIT %s OFFSET %s
        """

        params.extend([per_page, offset])
        cursor.execute(query, params)
        winners = cursor.fetchall()

        return jsonify({
            'data': winners,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'total_pages': (total + per_page - 1) // per_page
            }
        })

    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return jsonify({"error": str(err)}), 500
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()


@app.route('/api/admin/bingowinners', methods=['POST'])
@council_required
def create_bingo_winner():
    """Create a new bingo winner entry"""
    data = request.get_json()

    bingo_name = (data.get('bingoName') or '').strip()
    team_name = (data.get('teamName') or '').strip()
    participants = (data.get('participants') or '').strip()

    if not bingo_name or not team_name:
        return jsonify({"error": "bingoName and teamName are required"}), 400

    connection = None
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor()

        query = """INSERT INTO sanity2.bingoWinners (bingoName, teamName, participants)
                   VALUES (%s, %s, %s)"""
        cursor.execute(query, (bingo_name, team_name, participants))
        connection.commit()
        new_id = cursor.lastrowid

        # Audit log (best-effort, doesn't fail the request)
        discord_user = session.get('discord_user', {})
        discord_user_id = discord_user.get('id')
        if discord_user_id:
            try:
                action_note = f"Added bingo winner: {bingo_name} - {team_name}"
                audit_query = """
                    INSERT INTO sanity2.auditlogs (userId, affectedUsers, actionType, actionNote, actionDate)
                    VALUES (%s, %s, %s, %s, NOW())
                """
                cursor.execute(audit_query, (discord_user_id, team_name, 10, action_note))
                connection.commit()
            except mysql.connector.Error as audit_err:
                print(f"Warning: Audit log failed: {audit_err}")

        return jsonify({"message": "Bingo winner created", "bingoId": new_id}), 201

    except mysql.connector.Error as err:
        if connection:
            connection.rollback()
        print(f"Error creating bingo winner: {err}")
        return jsonify({"error": str(err)}), 500
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()


@app.route('/api/admin/bingowinners/<int:bingo_id>', methods=['PUT'])
@council_required
def update_bingo_winner(bingo_id):
    """Update an existing bingo winner entry"""
    data = request.get_json()

    bingo_name = (data.get('bingoName') or '').strip()
    team_name = (data.get('teamName') or '').strip()
    participants = (data.get('participants') or '').strip()

    if not bingo_name or not team_name:
        return jsonify({"error": "bingoName and teamName are required"}), 400

    connection = None
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor()

        query = """UPDATE sanity2.bingoWinners
                   SET bingoName=%s, teamName=%s, participants=%s
                   WHERE bingoId=%s"""
        cursor.execute(query, (bingo_name, team_name, participants, bingo_id))
        connection.commit()

        if cursor.rowcount == 0:
            return jsonify({"error": "Bingo winner not found"}), 404

        discord_user = session.get('discord_user', {})
        discord_user_id = discord_user.get('id')
        if discord_user_id:
            try:
                action_note = f"Updated bingo winner #{bingo_id}: {bingo_name} - {team_name}"
                audit_query = """
                    INSERT INTO sanity2.auditlogs (userId, affectedUsers, actionType, actionNote, actionDate)
                    VALUES (%s, %s, %s, %s, NOW())
                """
                cursor.execute(audit_query, (discord_user_id, team_name, 10, action_note))
                connection.commit()
            except mysql.connector.Error as audit_err:
                print(f"Warning: Audit log failed: {audit_err}")

        return jsonify({"message": "Bingo winner updated successfully"})

    except mysql.connector.Error as err:
        if connection:
            connection.rollback()
        print(f"Error updating bingo winner: {err}")
        return jsonify({"error": str(err)}), 500
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()


@app.route('/api/admin/bingowinners/<int:bingo_id>', methods=['DELETE'])
@council_required
def delete_bingo_winner(bingo_id):
    """Delete a bingo winner entry"""
    connection = None
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor()
        cursor.execute("DELETE FROM sanity2.bingoWinners WHERE bingoId = %s", (bingo_id,))
        connection.commit()

        if cursor.rowcount == 0:
            return jsonify({"error": "Bingo winner not found"}), 404

        return jsonify({"message": "Bingo winner deleted successfully"})

    except mysql.connector.Error as err:
        if connection:
            connection.rollback()
        print(f"Error deleting bingo winner: {err}")
        return jsonify({"error": str(err)}), 500
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()


@app.route('/api/admin/ranks', methods=['GET'])
@council_required
def get_ranks():
    """
    Get all ranks, ordered by pointRequirement (mirrors clan rank progression)
    """
    connection = None
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor(dictionary=True)

        query = """
            SELECT id, name, pointRequirement, diaryPointRequirement,
                   masterDiaryRequirement, maintenancePoints, discordRoleId
            FROM sanity2.ranks
            ORDER BY id ASC
        """
        cursor.execute(query)
        ranks = cursor.fetchall()

        # discordRoleId is a bigint (Discord snowflake) that can exceed JavaScript's
        # safe integer range, so send it as a string to avoid precision loss when
        # the browser parses the JSON.
        for rank in ranks:
            if rank.get('discordRoleId') is not None:
                rank['discordRoleId'] = str(rank['discordRoleId'])

        return jsonify({'data': ranks})

    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return jsonify({"error": str(err)}), 500
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()


@app.route('/api/ranks', methods=['GET'])
def get_public_ranks():
    """
    Public endpoint: returns rank names, point requirements, diary/master diary
    requirements and maintenance points for the ranks page.
    Ordered by id DESC so the highest rank is listed first.
    """
    connection = None
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor(dictionary=True)

        query = """
            SELECT id, name, pointRequirement, diaryPointRequirement,
                   masterDiaryRequirement, maintenancePoints
            FROM sanity2.ranks
            ORDER BY id DESC
        """
        cursor.execute(query)
        ranks = cursor.fetchall()

        return jsonify({'data': ranks})

    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return jsonify({"error": str(err)}), 500
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()


@app.route('/api/admin/ranks', methods=['POST'])
@council_required
def create_rank():
    """Create a new rank"""
    data = request.get_json()

    name = (data.get('name') or '').strip()
    if not name:
        return jsonify({"error": "name is required"}), 400

    def to_int_or_none(value, default=None):
        if value is None or value == '':
            return default
        try:
            return int(value)
        except (ValueError, TypeError):
            return default

    rank_id = data.get('id')
    point_requirement = to_int_or_none(data.get('pointRequirement'))
    diary_point_requirement = to_int_or_none(data.get('diaryPointRequirement'), 0)
    master_diary_requirement = to_int_or_none(data.get('masterDiaryRequirement'), 0)
    maintenance_points = to_int_or_none(data.get('maintenancePoints'), 0)
    discord_role_id = to_int_or_none(data.get('discordRoleId'))

    if rank_id is None or rank_id == '':
        return jsonify({"error": "id is required"}), 400
    try:
        rank_id = int(rank_id)
    except (ValueError, TypeError):
        return jsonify({"error": "id must be an integer"}), 400

    connection = None
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor()

        query = """INSERT INTO sanity2.ranks
                   (id, name, pointRequirement, diaryPointRequirement, masterDiaryRequirement, maintenancePoints, discordRoleId)
                   VALUES (%s, %s, %s, %s, %s, %s, %s)"""
        cursor.execute(query, (rank_id, name, point_requirement, diary_point_requirement,
                                master_diary_requirement, maintenance_points, discord_role_id))
        connection.commit()

        discord_user = session.get('discord_user', {})
        discord_user_id = discord_user.get('id')
        if discord_user_id:
            try:
                action_note = f"Added rank: {name} (id {rank_id})"
                audit_query = """
                    INSERT INTO sanity2.auditlogs (userId, affectedUsers, actionType, actionNote, actionDate)
                    VALUES (%s, %s, %s, %s, NOW())
                """
                cursor.execute(audit_query, (discord_user_id, name, 10, action_note))
                connection.commit()
            except mysql.connector.Error as audit_err:
                print(f"Warning: Audit log failed: {audit_err}")

        return jsonify({"message": "Rank created", "id": rank_id}), 201

    except mysql.connector.Error as err:
        if connection:
            connection.rollback()
        print(f"Error creating rank: {err}")
        return jsonify({"error": str(err)}), 500
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()


@app.route('/api/admin/ranks/<rank_id>', methods=['PUT'])
@council_required
def update_rank(rank_id):
    """Update an existing rank"""
    try:
        rank_id = int(rank_id)
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid rank id"}), 400

    data = request.get_json()

    name = (data.get('name') or '').strip()
    if not name:
        return jsonify({"error": "name is required"}), 400

    def to_int_or_none(value, default=None):
        if value is None or value == '':
            return default
        try:
            return int(value)
        except (ValueError, TypeError):
            return default

    point_requirement = to_int_or_none(data.get('pointRequirement'))
    diary_point_requirement = to_int_or_none(data.get('diaryPointRequirement'), 0)
    master_diary_requirement = to_int_or_none(data.get('masterDiaryRequirement'), 0)
    maintenance_points = to_int_or_none(data.get('maintenancePoints'), 0)
    discord_role_id = to_int_or_none(data.get('discordRoleId'))

    connection = None
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor()

        query = """UPDATE sanity2.ranks
                   SET name=%s, pointRequirement=%s, diaryPointRequirement=%s,
                       masterDiaryRequirement=%s, maintenancePoints=%s, discordRoleId=%s
                   WHERE id=%s"""
        cursor.execute(query, (name, point_requirement, diary_point_requirement,
                                master_diary_requirement, maintenance_points, discord_role_id, rank_id))
        connection.commit()

        if cursor.rowcount == 0:
            return jsonify({"error": "Rank not found"}), 404

        discord_user = session.get('discord_user', {})
        discord_user_id = discord_user.get('id')
        if discord_user_id:
            try:
                action_note = f"Updated rank #{rank_id}: {name}"
                audit_query = """
                    INSERT INTO sanity2.auditlogs (userId, affectedUsers, actionType, actionNote, actionDate)
                    VALUES (%s, %s, %s, %s, NOW())
                """
                cursor.execute(audit_query, (discord_user_id, name, 10, action_note))
                connection.commit()
            except mysql.connector.Error as audit_err:
                print(f"Warning: Audit log failed: {audit_err}")

        return jsonify({"message": "Rank updated successfully"})

    except mysql.connector.Error as err:
        if connection:
            connection.rollback()
        print(f"Error updating rank: {err}")
        return jsonify({"error": str(err)}), 500
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()


@app.route('/api/admin/ranks/<rank_id>', methods=['DELETE'])
@council_required
def delete_rank(rank_id):
    """Delete a rank"""
    try:
        rank_id = int(rank_id)
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid rank id"}), 400

    connection = None
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor()
        cursor.execute("DELETE FROM sanity2.ranks WHERE id = %s", (rank_id,))
        connection.commit()

        if cursor.rowcount == 0:
            return jsonify({"error": "Rank not found"}), 404

        return jsonify({"message": "Rank deleted successfully"})

    except mysql.connector.Error as err:
        if connection:
            connection.rollback()
        print(f"Error deleting rank: {err}")
        return jsonify({"error": str(err)}), 500
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()


@app.route('/api/admin/bosses', methods=['GET'])
@council_required
def get_admin_bosses():
    """Get all bosses (id, name) for use in dropdowns/lookups in the admin panel"""
    connection = None
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT id, name FROM sanity2.bosses ORDER BY name")
        bosses = cursor.fetchall()
        return jsonify({'data': bosses})
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return jsonify({"error": str(err)}), 500
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()


@app.route('/api/admin/diarytimes', methods=['GET'])
@council_required
def get_admin_diary_times():
    """
    Get all diary times, ordered by diaryId
    """
    connection = None
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor(dictionary=True)

        query = """
            SELECT dt.diaryId, dt.bossId, b.name AS bossName, dt.scale, dt.maxDifficulty,
                   dt.timeEasy, dt.timeMedium, dt.timeHard, dt.timeElite, dt.timeMaster
            FROM sanity2.diarytimes dt
            LEFT JOIN sanity2.bosses b ON b.id = dt.bossId
            ORDER BY dt.diaryId ASC
        """
        cursor.execute(query)
        diary_times = cursor.fetchall()

        return jsonify({'data': diary_times})

    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return jsonify({"error": str(err)}), 500
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()


@app.route('/api/admin/diarytimes', methods=['POST'])
@council_required
def create_diary_time():
    """Create a new diary time entry"""
    data = request.get_json()

    def to_int_or_none(value, default=None):
        if value is None or value == '':
            return default
        try:
            return int(value)
        except (ValueError, TypeError):
            return default

    diary_id = data.get('diaryId')
    boss_id = data.get('bossId')

    if diary_id is None or diary_id == '':
        return jsonify({"error": "diaryId is required"}), 400
    if boss_id is None or boss_id == '':
        return jsonify({"error": "bossId is required"}), 400

    try:
        diary_id = int(diary_id)
        boss_id = int(boss_id)
    except (ValueError, TypeError):
        return jsonify({"error": "diaryId and bossId must be integers"}), 400

    scale = to_int_or_none(data.get('scale'))
    max_difficulty = to_int_or_none(data.get('maxDifficulty'))
    time_easy = (data.get('timeEasy') or '0').strip()
    time_medium = (data.get('timeMedium') or '0').strip()
    time_hard = (data.get('timeHard') or '0').strip()
    time_elite = (data.get('timeElite') or '0').strip()
    time_master = (data.get('timeMaster') or '0').strip()

    connection = None
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor()

        query = """INSERT INTO sanity2.diarytimes
                   (diaryId, bossId, scale, maxDifficulty, timeEasy, timeMedium, timeHard, timeElite, timeMaster)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"""
        cursor.execute(query, (diary_id, boss_id, scale, max_difficulty,
                                time_easy, time_medium, time_hard, time_elite, time_master))
        connection.commit()

        discord_user = session.get('discord_user', {})
        discord_user_id = discord_user.get('id')
        if discord_user_id:
            try:
                action_note = f"Added diary time entry: diaryId {diary_id} (boss {boss_id})"
                audit_query = """
                    INSERT INTO sanity2.auditlogs (userId, affectedUsers, actionType, actionNote, actionDate)
                    VALUES (%s, %s, %s, %s, NOW())
                """
                cursor.execute(audit_query, (discord_user_id, str(diary_id), 10, action_note))
                connection.commit()
            except mysql.connector.Error as audit_err:
                print(f"Warning: Audit log failed: {audit_err}")

        return jsonify({"message": "Diary time created", "diaryId": diary_id}), 201

    except mysql.connector.Error as err:
        if connection:
            connection.rollback()
        print(f"Error creating diary time: {err}")
        return jsonify({"error": str(err)}), 500
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()


@app.route('/api/admin/diarytimes/<int:diary_id>', methods=['PUT'])
@council_required
def update_diary_time(diary_id):
    """Update an existing diary time entry"""
    data = request.get_json()

    def to_int_or_none(value, default=None):
        if value is None or value == '':
            return default
        try:
            return int(value)
        except (ValueError, TypeError):
            return default

    boss_id = data.get('bossId')
    if boss_id is None or boss_id == '':
        return jsonify({"error": "bossId is required"}), 400
    try:
        boss_id = int(boss_id)
    except (ValueError, TypeError):
        return jsonify({"error": "bossId must be an integer"}), 400

    scale = to_int_or_none(data.get('scale'))
    max_difficulty = to_int_or_none(data.get('maxDifficulty'))
    time_easy = (data.get('timeEasy') or '0').strip()
    time_medium = (data.get('timeMedium') or '0').strip()
    time_hard = (data.get('timeHard') or '0').strip()
    time_elite = (data.get('timeElite') or '0').strip()
    time_master = (data.get('timeMaster') or '0').strip()

    connection = None
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor()

        query = """UPDATE sanity2.diarytimes
                   SET bossId=%s, scale=%s, maxDifficulty=%s, timeEasy=%s,
                       timeMedium=%s, timeHard=%s, timeElite=%s, timeMaster=%s
                   WHERE diaryId=%s"""
        cursor.execute(query, (boss_id, scale, max_difficulty, time_easy,
                                time_medium, time_hard, time_elite, time_master, diary_id))
        connection.commit()

        if cursor.rowcount == 0:
            return jsonify({"error": "Diary time entry not found"}), 404

        discord_user = session.get('discord_user', {})
        discord_user_id = discord_user.get('id')
        if discord_user_id:
            try:
                action_note = f"Updated diary time entry: diaryId {diary_id} (boss {boss_id})"
                audit_query = """
                    INSERT INTO sanity2.auditlogs (userId, affectedUsers, actionType, actionNote, actionDate)
                    VALUES (%s, %s, %s, %s, NOW())
                """
                cursor.execute(audit_query, (discord_user_id, str(diary_id), 10, action_note))
                connection.commit()
            except mysql.connector.Error as audit_err:
                print(f"Warning: Audit log failed: {audit_err}")

        return jsonify({"message": "Diary time updated successfully"})

    except mysql.connector.Error as err:
        if connection:
            connection.rollback()
        print(f"Error updating diary time: {err}")
        return jsonify({"error": str(err)}), 500
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()


@app.route('/api/admin/diarytimes/<int:diary_id>', methods=['DELETE'])
@council_required
def delete_diary_time(diary_id):
    """Delete a diary time entry"""
    connection = None
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor()
        cursor.execute("DELETE FROM sanity2.diarytimes WHERE diaryId = %s", (diary_id,))
        connection.commit()

        if cursor.rowcount == 0:
            return jsonify({"error": "Diary time entry not found"}), 404

        return jsonify({"message": "Diary time entry deleted successfully"})

    except mysql.connector.Error as err:
        if connection:
            connection.rollback()
        print(f"Error deleting diary time: {err}")
        return jsonify({"error": str(err)}), 500
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()


@app.route('/api/admin/setupvalues', methods=['GET'])
@council_required
def get_setup_values():
    """Get all setup values, ordered by Id"""
    connection = None
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor(dictionary=True)

        query = """
            SELECT Id, Name, Value
            FROM sanity2.setupValues
            ORDER BY Id ASC
        """
        cursor.execute(query)
        setup_values = cursor.fetchall()

        return jsonify({'data': setup_values})

    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return jsonify({"error": str(err)}), 500
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()


@app.route('/api/admin/setupvalues', methods=['POST'])
@council_required
def create_setup_value():
    """Create a new setup value"""
    data = request.get_json()

    name = (data.get('Name') or '').strip()
    if not name:
        return jsonify({"error": "Name is required"}), 400

    value = data.get('Value')
    if value is None or value == '':
        value = None
    else:
        try:
            value = int(value)
        except (ValueError, TypeError):
            return jsonify({"error": "Value must be an integer"}), 400

    connection = None
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor()

        query = "INSERT INTO sanity2.setupValues (Name, Value) VALUES (%s, %s)"
        cursor.execute(query, (name, value))
        connection.commit()
        new_id = cursor.lastrowid

        discord_user = session.get('discord_user', {})
        discord_user_id = discord_user.get('id')
        if discord_user_id:
            try:
                action_note = f"Added setup value: {name} = {value}"
                audit_query = """
                    INSERT INTO sanity2.auditlogs (userId, affectedUsers, actionType, actionNote, actionDate)
                    VALUES (%s, %s, %s, %s, NOW())
                """
                cursor.execute(audit_query, (discord_user_id, name, 10, action_note))
                connection.commit()
            except mysql.connector.Error as audit_err:
                print(f"Warning: Audit log failed: {audit_err}")

        return jsonify({"message": "Setup value created", "Id": new_id}), 201

    except mysql.connector.Error as err:
        if connection:
            connection.rollback()
        print(f"Error creating setup value: {err}")
        return jsonify({"error": str(err)}), 500
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()


@app.route('/api/admin/setupvalues/<int:setup_id>', methods=['PUT'])
@council_required
def update_setup_value(setup_id):
    """Update an existing setup value"""
    data = request.get_json()

    name = (data.get('Name') or '').strip()
    if not name:
        return jsonify({"error": "Name is required"}), 400

    value = data.get('Value')
    if value is None or value == '':
        value = None
    else:
        try:
            value = int(value)
        except (ValueError, TypeError):
            return jsonify({"error": "Value must be an integer"}), 400

    connection = None
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor()

        query = "UPDATE sanity2.setupValues SET Name=%s, Value=%s WHERE Id=%s"
        cursor.execute(query, (name, value, setup_id))
        connection.commit()

        if cursor.rowcount == 0:
            return jsonify({"error": "Setup value not found"}), 404

        discord_user = session.get('discord_user', {})
        discord_user_id = discord_user.get('id')
        if discord_user_id:
            try:
                action_note = f"Updated setup value #{setup_id}: {name} = {value}"
                audit_query = """
                    INSERT INTO sanity2.auditlogs (userId, affectedUsers, actionType, actionNote, actionDate)
                    VALUES (%s, %s, %s, %s, NOW())
                """
                cursor.execute(audit_query, (discord_user_id, name, 10, action_note))
                connection.commit()
            except mysql.connector.Error as audit_err:
                print(f"Warning: Audit log failed: {audit_err}")

        return jsonify({"message": "Setup value updated successfully"})

    except mysql.connector.Error as err:
        if connection:
            connection.rollback()
        print(f"Error updating setup value: {err}")
        return jsonify({"error": str(err)}), 500
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()


@app.route('/api/admin/setupvalues/<int:setup_id>', methods=['DELETE'])
@council_required
def delete_setup_value(setup_id):
    """Delete a setup value"""
    connection = None
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor()
        cursor.execute("DELETE FROM sanity2.setupValues WHERE Id = %s", (setup_id,))
        connection.commit()

        if cursor.rowcount == 0:
            return jsonify({"error": "Setup value not found"}), 404

        return jsonify({"message": "Setup value deleted successfully"})

    except mysql.connector.Error as err:
        if connection:
            connection.rollback()
        print(f"Error deleting setup value: {err}")
        return jsonify({"error": str(err)}), 500
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()


# --- DISCORD CHECKLIST GENERATOR ---

def _ensure_checklists_table():
    """Create the checklists table (in the sanitybingo schema) if it does not exist yet."""
    conn = mysql.connector.connect(**BINGO_DB_CONFIG)
    try:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS checklists (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                data LONGTEXT NOT NULL
            )
        """)
        conn.commit()
    finally:
        conn.close()


def _normalize_checklist_data(data):
    """
    Validate and normalize a checklist structure into a canonical dict:
        {"bosses": [{"name": str, "sections": [str]}]}
    Returns None when the input is not a valid checklist structure.
    """
    if not isinstance(data, dict):
        return None
    bosses = data.get('bosses')
    if not isinstance(bosses, list):
        return None

    normalized_bosses = []
    for boss in bosses:
        if not isinstance(boss, dict):
            continue
        boss_name = (boss.get('name') or '').strip()
        if not boss_name:
            continue
        sections = boss.get('sections')
        if not isinstance(sections, list):
            sections = []

        normalized_sections = []
        for section in sections:
            if isinstance(section, str):
                section = section.strip()
                if section:
                    normalized_sections.append(section)

        normalized_bosses.append({
            'name': boss_name,
            'sections': normalized_sections,
        })

    return {'bosses': normalized_bosses}


@app.route('/api/checklists', methods=['GET'])
def get_checklists():
    """Public: list all checklist sets (id + name) for the dropdown."""
    connection = None
    try:
        _ensure_checklists_table()
        connection = mysql.connector.connect(**BINGO_DB_CONFIG)
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT id, name FROM checklists ORDER BY id ASC")
        rows = cursor.fetchall()
        return jsonify({'data': rows})
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return jsonify({"error": str(err)}), 500
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()


@app.route('/api/checklists/<int:checklist_id>', methods=['GET'])
def get_checklist(checklist_id):
    """Public: get a single checklist including its parsed structure."""
    connection = None
    try:
        _ensure_checklists_table()
        connection = mysql.connector.connect(**BINGO_DB_CONFIG)
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT id, name, data FROM checklists WHERE id = %s", (checklist_id,))
        row = cursor.fetchone()
        if not row:
            return jsonify({"error": "Checklist not found"}), 404

        try:
            row['data'] = json.loads(row['data'])
        except (ValueError, TypeError):
            row['data'] = {'bosses': []}
        return jsonify(row)
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return jsonify({"error": str(err)}), 500
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()


@app.route('/api/admin/checklists', methods=['GET'])
@council_required
def get_admin_checklists():
    """Admin: list all checklists with their parsed structure."""
    connection = None
    try:
        _ensure_checklists_table()
        connection = mysql.connector.connect(**BINGO_DB_CONFIG)
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT id, name, data FROM checklists ORDER BY id ASC")
        rows = cursor.fetchall()
        for row in rows:
            try:
                row['data'] = json.loads(row['data'])
            except (ValueError, TypeError):
                row['data'] = {'bosses': []}
        return jsonify({'data': rows})
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return jsonify({"error": str(err)}), 500
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()


@app.route('/api/admin/checklists', methods=['POST'])
@council_required
def create_checklist():
    """Create a new checklist set."""
    data = request.get_json() or {}
    name = (data.get('name') or '').strip()
    if not name:
        return jsonify({"error": "Name is required"}), 400

    checklist_data = _normalize_checklist_data(data.get('data'))
    if checklist_data is None:
        return jsonify({"error": "Invalid checklist data"}), 400

    connection = None
    try:
        _ensure_checklists_table()
        connection = mysql.connector.connect(**BINGO_DB_CONFIG)
        cursor = connection.cursor()
        cursor.execute(
            "INSERT INTO checklists (name, data) VALUES (%s, %s)",
            (name, json.dumps(checklist_data))
        )
        connection.commit()
        new_id = cursor.lastrowid
        return jsonify({"message": "Checklist created", "id": new_id}), 201
    except mysql.connector.Error as err:
        if connection:
            connection.rollback()
        print(f"Error creating checklist: {err}")
        return jsonify({"error": str(err)}), 500
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()


@app.route('/api/admin/checklists/<int:checklist_id>', methods=['PUT'])
@council_required
def update_checklist(checklist_id):
    """Update an existing checklist set."""
    data = request.get_json() or {}
    name = (data.get('name') or '').strip()
    if not name:
        return jsonify({"error": "Name is required"}), 400

    checklist_data = _normalize_checklist_data(data.get('data'))
    if checklist_data is None:
        return jsonify({"error": "Invalid checklist data"}), 400

    connection = None
    try:
        _ensure_checklists_table()
        connection = mysql.connector.connect(**BINGO_DB_CONFIG)
        cursor = connection.cursor()
        cursor.execute(
            "UPDATE checklists SET name = %s, data = %s WHERE id = %s",
            (name, json.dumps(checklist_data), checklist_id)
        )
        connection.commit()
        if cursor.rowcount == 0:
            return jsonify({"error": "Checklist not found"}), 404
        return jsonify({"message": "Checklist updated successfully"})
    except mysql.connector.Error as err:
        if connection:
            connection.rollback()
        print(f"Error updating checklist: {err}")
        return jsonify({"error": str(err)}), 500
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()


@app.route('/api/admin/checklists/<int:checklist_id>', methods=['DELETE'])
@council_required
def delete_checklist(checklist_id):
    """Delete a checklist set."""
    connection = None
    try:
        _ensure_checklists_table()
        connection = mysql.connector.connect(**BINGO_DB_CONFIG)
        cursor = connection.cursor()
        cursor.execute("DELETE FROM checklists WHERE id = %s", (checklist_id,))
        connection.commit()
        if cursor.rowcount == 0:
            return jsonify({"error": "Checklist not found"}), 404
        return jsonify({"message": "Checklist deleted successfully"})
    except mysql.connector.Error as err:
        if connection:
            connection.rollback()
        print(f"Error deleting checklist: {err}")
        return jsonify({"error": str(err)}), 500
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()


@app.route('/api/admin/audit-log', methods=['POST'])
@council_required
def create_admin_audit_log():
    data = request.get_json()
    connection = None
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor()
        user_info = session.get('discord_user', {})
        admin_username = user_info.get('username', 'Unknown')
        query = "INSERT INTO sanity2.auditlogs (actionNote, actionDate) VALUES (%s, NOW())"
        action_note = f"ADMIN ACTION by {admin_username}: {data['action']}"
        cursor.execute(query, (action_note,))
        connection.commit()
        return jsonify({"message": "Logged"}), 201
    except mysql.connector.Error as err:
        if connection:
            connection.rollback()
        return jsonify({"error": str(err)}), 500
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()


# --- EXISTING API ENDPOINTS (No changes here) ---

@app.route('/api/rankChanges', methods=['GET'])
def get_rank_changes():
    """
    OPTIMIZED with pagination support
    By default, returns first 100 rank changes (for home page widget)
    Can be paginated for full rank changes page if needed
    """
    connection = None
    try:
        # Get pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 100, type=int)  # Default 100 for home page

        # Limit per_page
        per_page = min(per_page, 500)
        per_page = max(per_page, 10)

        # Calculate offset
        offset = (page - 1) * per_page

        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor(dictionary=True)

        query = """
            SELECT
                a.actionDate,
                u.userid,
                u.displayName,
                r_before.name AS rank_before,
                r_after.name AS rank_after,
                r_before.id as rankId_before,
                r_after.id as rankId_after
            FROM
                sanity2.auditlogs a
            JOIN
                sanity2.users u ON u.userid = SUBSTRING_INDEX(SUBSTRING_INDEX(a.actionNote, ' ', 2), ' ', -1)
            JOIN
                sanity2.ranks r_before ON r_before.id = SUBSTRING_INDEX(SUBSTRING_INDEX(a.actionNote, ' from ', -1), ' to ', 1)
            JOIN
                sanity2.ranks r_after ON r_after.id = SUBSTRING_INDEX(a.actionNote, ' to ', -1)
            WHERE
                a.actionNote LIKE 'UPDATED % RANK from % to %' and 
                r_before.name != 'quit' and 
                r_before.name != 'retired' and 
                r_after.name  != 'quit' and 
                r_after.name  != 'retired'
            ORDER BY 
                a.actionDate DESC
            LIMIT %s OFFSET %s
        """

        cursor.execute(query, (per_page, offset))
        rank_changes = cursor.fetchall()

        # Get total count (cache this for better performance)
        count_query = """
            SELECT COUNT(*) as total
            FROM sanity2.auditlogs a
            WHERE a.actionNote LIKE 'UPDATED % RANK from % to %'
        """
        cursor.execute(count_query)
        count_result = cursor.fetchone()
        total = count_result['total'] if count_result else 0

        # Return with pagination metadata
        return jsonify({
            'data': rank_changes,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'total_pages': (total + per_page - 1) // per_page
            }
        })

    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return jsonify({"error": str(err)}), 500
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()
            print("MySQL connection closed")


# ============================================================================
# ALTERNATIVE: Simple version for backward compatibility
# ============================================================================
# If you want to keep the old endpoint that returns ALL rank changes,
# create a separate endpoint:

@app.route('/api/rankChanges/all', methods=['GET'])
def get_rank_changes_all():
    """
    Legacy endpoint - returns all rank changes (for backward compatibility)
    Use /api/rankChanges with pagination instead
    """
    connection = None
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor(dictionary=True)

        query = """
            SELECT
                a.actionDate,
                u.userid,
                u.displayName,
                r_before.name AS rank_before,
                r_after.name AS rank_after,
                r_before.id as rankId_before,
                r_after.id as rankId_after
            FROM
                sanity2.auditlogs a
            JOIN
                sanity2.users u ON u.userid = SUBSTRING_INDEX(SUBSTRING_INDEX(a.actionNote, ' ', 2), ' ', -1)
            JOIN
                sanity2.ranks r_before ON r_before.id = SUBSTRING_INDEX(SUBSTRING_INDEX(a.actionNote, ' from ', -1), ' to ', 1)
            JOIN
                sanity2.ranks r_after ON r_after.id = SUBSTRING_INDEX(a.actionNote, ' to ', -1)
            WHERE
                a.actionNote LIKE 'UPDATED % RANK from % to %' and 
                r_before.name != 'quit' and 
                r_before.name != 'retired' and 
                r_after.name  != 'quit' and 
                r_after.name  != 'retired'
            ORDER BY 
                a.actionDate DESC
            LIMIT 1000  -- At least add a limit for safety
        """

        cursor.execute(query)
        users_data = cursor.fetchall()
        return jsonify(users_data)

    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return jsonify({"error": str(err)}), 500
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()
            print("MySQL connection closed")


@app.route('/api/getUserEhb', methods=['GET'])
def get_user_ehb():
    """
    Connects to the MySQL database, executes the user query,
    and returns the data as JSON.
    """
    connection = None
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor(dictionary=True)  # dictionary=True makes rows accessible by column name

        query = """
            SELECT
                u.displayName,
                GROUP_CONCAT(DISTINCT s.displayName SEPARATOR ', ') AS associated_rsns,
                SUM(s.ehbWeeklyEhb) AS total_weekly_ehb,
                SUM(s.chambers_of_xericWeeklyEHB) as 'chambers_of_xericWeeklyEHB', 
                SUM(s.chambers_of_xeric_challenge_modeWeeklyEHB) as 'chambers_of_xeric_challenge_modeWeeklyEHB',
                sum(s.the_corrupted_gauntletWeeklyEHB) as 'the_corrupted_gauntletWeeklyEHB',
                sum(s.sol_hereditWeeklyEHB) as 'sol_hereditWeeklyEHB',
                sum(s.theatre_of_bloodWeeklyEHB) as 'theatre_of_bloodWeeklyEHB',
                sum(s.theatre_of_blood_hard_modeWeeklyEHB) as 'theatre_of_blood_hard_modeWeeklyEHB',
                sum(s.tzkal_zukWeeklyEHB) as 'tzkal_zukWeeklyEHB',
                sum(s.tztok_jadWeeklyEHB) as 'tztok_jadWeeklyEHB',
                sum(s.doom_of_mokhaiotlWeeklyEHB) as 'doom_of_mokhaiotlWeeklyEHB'
            FROM
                sanity2.users u
            JOIN
                sanity2.userStats s ON s.displayName = u.mainrsn OR s.displayName = u.altrsn
            GROUP BY
                u.userId
            order by sum(s.ehbWeeklyEhb) desc 
        """
        cursor.execute(query)
        users_data = cursor.fetchall()
        return jsonify(users_data)

    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return jsonify({"error": str(err)}), 500
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()
            print("MySQL connection closed")


@app.route('/api/womehb', methods=['GET'])
def get_wom_ehb():
    """
    Proxy WiseOldMan player EHB for a given RSN so the profile page can show
    total EHB / rank without CORS issues.
    """
    rsn = (request.args.get('rsn') or '').strip()
    if not rsn:
        return jsonify({"error": "rsn is required"}), 400

    try:
        resp = _wom_get(f"{WOM_API_BASE}/players/{requests.utils.quote(rsn)}", timeout=15)
    except requests.RequestException:
        return jsonify({"error": "WiseOldMan request failed"}), 502

    if resp.status_code != 200:
        return jsonify({"error": "Player not found on WiseOldMan"}), 404

    try:
        data = resp.json()
    except ValueError:
        return jsonify({"error": "Invalid WiseOldMan response"}), 502

    return jsonify({
        "username": data.get("username"),
        "ehb": data.get("ehb"),
        "ehbRank": data.get("ehbRank"),
        "lastImportedAt": data.get("lastImportedAt"),
    })


@app.route('/api/miscroles', methods=['GET'])
def get_miscroles():
    """
    Connects to the MySQL database, executes the user query,
    and returns the data as JSON.
    """
    connection = None
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor(dictionary=True)  # dictionary=True makes rows accessible by column name

        query = """
            select mr.roleName,u.displayName from sanity2.miscRoles mr 
            left join sanity2.users u on u.userId = mr.userId 
        """
        cursor.execute(query)
        users_data = cursor.fetchall()
        return jsonify(users_data)

    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return jsonify({"error": str(err)}), 500
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()
            print("MySQL connection closed")


@app.route('/api/bingo/drops', methods=['GET'])
def get_bingo_drops():
    """
    Returns bingo drops. Use ?event_id= to filter by event date range.
    """
    event_id = request.args.get('event_id', default=None, type=int)
    connection = None
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor(dictionary=True)

        params = []
        event_filter = ""
        if event_id:
            bingo_conn = mysql.connector.connect(**BINGO_DB_CONFIG)
            bingo_cursor = bingo_conn.cursor(dictionary=True)
            bingo_cursor.execute(
                "SELECT start_date, end_date FROM bingo_events WHERE id = %s", (event_id,)
            )
            event = bingo_cursor.fetchone()
            bingo_cursor.close()
            bingo_conn.close()
            if event:
                event_filter = " AND s.reviewedDate >= DATE_SUB(%s, INTERVAL 7 DAY) AND s.reviewedDate <= DATE_ADD(%s, INTERVAL 7 DAY)"
                params = [event['start_date'], event['end_date']]

        query = f"""
            SELECT
                s.Id,
                submitter_u.displayName AS submitter,
                GROUP_CONCAT(participant_u.displayName ORDER BY FIND_IN_SET(participant_u.userId, REPLACE(s.participants, '*', '')) SEPARATOR ', ') AS member_names,
                s.notes,
                s.value,
                s2.name AS status_name,
                s.imageUrl,
                s.reviewedDate,
                reviewer_u.displayName AS reviewer
            FROM
                sanity2.submissions s
            LEFT JOIN
                sanity2.users submitter_u ON s.userId = submitter_u.userId
            LEFT JOIN
                sanity2.users participant_u ON FIND_IN_SET(participant_u.userId, REPLACE(s.participants, '*', '')) > 0
            LEFT JOIN
                sanity2.users reviewer_u ON s.reviewedBy = reviewer_u.userId
            LEFT JOIN
                sanity2.submissionstatus s2 ON s.status = s2.id
            WHERE s.status IN (2,3,1,4) AND s.bingo = 1{event_filter}
            GROUP BY
                s.Id,
                submitter_u.displayName,
                s.notes,
                s.value,
                s.imageUrl,
                s.reviewedDate,
                s2.name
            ORDER BY
                Id DESC
            LIMIT 1000
        """
        cursor.execute(query, params)
        drops_data = cursor.fetchall()
        return jsonify(drops_data)

    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return jsonify({"error": str(err)}), 500
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()
            print("MySQL connection closed")


@app.route('/api/discordProfileUrl', methods=['GET'])
def get_discord_profile_url():
    """
    Connects to the MySQL database, executes the user query,
    and returns the data as JSON.
    """
    connection = None
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor(dictionary=True)  # dictionary=True makes rows accessible by column name

        query = """
            SELECT
                u.displayName , discordProfileImageUrl 
            FROM 
                sanity2.discordProfileImageUrl dpiu 
            left join sanity2.users u on u.userId = dpiu.userId 
        """
        cursor.execute(query)
        users_data = cursor.fetchall()
        return jsonify(users_data)

    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return jsonify({"error": str(err)}), 500
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()
            print("MySQL connection closed")


@app.route('/api/getRSNkc', methods=['GET'])
def get_rsn_kc():
    """
    Connects to the MySQL database, executes the user query,
    and returns the data as JSON.
    """
    connection = None
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor(dictionary=True)  # dictionary=True makes rows accessible by column name

        # Build column list dynamically so newly added bosses appear automatically
        cursor.execute("SHOW COLUMNS FROM sanity2.bingobosskc")
        columns = [row['Field'] for row in cursor.fetchall()]
        col_list = ', '.join(f'`{c}`' for c in columns)

        query = f"SELECT {col_list} FROM sanity2.bingobosskc;"
        cursor.execute(query)
        users_data = cursor.fetchall()
        return jsonify(users_data)

    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return jsonify({"error": str(err)}), 500
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()
            print("MySQL connection closed")


@app.route('/api/auditlog', methods=['GET'])
def get_auditlog():
    """
    Paginated auditlog endpoint - fetches only what's needed
    Much faster than loading 23,000 rows!
    """
    connection = None
    try:
        # Get pagination parameters from query string
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 200, type=int)

        # Limit per_page to prevent abuse
        per_page = min(per_page, 50000)
        per_page = max(per_page, 10)

        # Calculate offset
        offset = (page - 1) * per_page

        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor(dictionary=True)

        # Main query with pagination
        query = """
             SELECT
                  a.id,
                  u.displayName,
                  CASE
                    WHEN a.affectedUsers IS NULL THEN NULL
                    WHEN a.affectedUsers NOT LIKE '%,%' THEN (
                      SELECT
                        displayName
                      FROM
                        sanity2.users
                      WHERE
                        userId = a.affectedUsers
                    )
                    ELSE (
                      SELECT
                        GROUP_CONCAT(displayName)
                      FROM
                        sanity2.users
                      WHERE
                        FIND_IN_SET(userId, a.affectedUsers) > 0
                    )
                  END AS affectedUserNames,
                  a2.name,
                  a.actionNote,
                  a.actionDate
                FROM
                  sanity2.auditlogs a
                  LEFT JOIN sanity2.users u ON u.userId = a.userId
                  LEFT JOIN sanity2.auditactiontype a2 ON a2.id = a.actionType
                ORDER BY
                  a.actionDate DESC
                LIMIT %s OFFSET %s;
        """

        cursor.execute(query, (per_page, offset))
        audit_logs = cursor.fetchall()

        # Get total count for pagination (cache this for better performance)
        count_query = "SELECT COUNT(*) as total FROM sanity2.auditlogs"
        cursor.execute(count_query)
        count_result = cursor.fetchone()
        total = count_result['total'] if count_result else 0

        # Calculate total pages
        total_pages = (total + per_page - 1) // per_page

        return jsonify({
            'data': audit_logs,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'total_pages': total_pages
            }
        })

    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return jsonify({"error": str(err)}), 500
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()


# ============================================================================
# ALTERNATIVE: More optimized version with batch user lookup
# ============================================================================

@app.route('/api/auditlog/optimized', methods=['GET'])
def get_auditlog_optimized():
    """
    Even faster version - resolves affected users in batch
    Use this if the above is still slow
    """
    connection = None
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 200, type=int)
        per_page = min(per_page, 500)
        offset = (page - 1) * per_page

        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor(dictionary=True)

        # Get audit logs without the slow subqueries
        query = """
            SELECT
                a.id,
                u.displayName,
                a.affectedUsers,
                a2.name,
                a.actionNote,
                a.actionDate
            FROM
                sanity2.auditlogs a
                LEFT JOIN sanity2.users u ON u.userId = a.userId
                LEFT JOIN sanity2.auditactiontype a2 ON a2.id = a.actionType
            ORDER BY
                a.actionDate DESC
            LIMIT %s OFFSET %s
        """

        cursor.execute(query, (per_page, offset))
        audit_logs = cursor.fetchall()

        # Batch lookup for affected users
        affected_user_ids = set()
        for log in audit_logs:
            if log.get('affectedUsers'):
                ids = log['affectedUsers'].split(',')
                affected_user_ids.update([uid.strip() for uid in ids if uid.strip()])

        # Get all affected users in one query
        user_map = {}
        if affected_user_ids:
            placeholders = ','.join(['%s'] * len(affected_user_ids))
            user_query = f"SELECT userId, displayName FROM sanity2.users WHERE userId IN ({placeholders})"
            cursor.execute(user_query, tuple(affected_user_ids))
            users = cursor.fetchall()
            user_map = {str(u['userId']): u['displayName'] for u in users}

        # Resolve affected user names
        for log in audit_logs:
            if log.get('affectedUsers'):
                user_ids = [uid.strip() for uid in log['affectedUsers'].split(',') if uid.strip()]
                user_names = [user_map.get(uid, f'Unknown ({uid})') for uid in user_ids]
                log['affectedUserNames'] = ', '.join(user_names)
            else:
                log['affectedUserNames'] = None
            del log['affectedUsers']  # Remove raw data

        # Get total count
        cursor.execute("SELECT COUNT(*) as total FROM sanity2.auditlogs")
        total = cursor.fetchone()['total']

        return jsonify({
            'data': audit_logs,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'total_pages': (total + per_page - 1) // per_page
            }
        })

    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return jsonify({"error": str(err)}), 500
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()


@app.route('/api/discordmsgssentyearly', methods=['GET'])
def get_yearly_discord_msgs():
    """
    Connects to the MySQL database, executes the user query,
    and returns the data as JSON.
    """
    connection = None
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor(dictionary=True)  # dictionary=True makes rows accessible by column name

        query = """
            select count(l.authorID) as 'messageCount',u.displayName from sanity2.loggedmsgs l 
            inner join sanity2.users u on u.userId = l.authorID 
            where l.datetimeMSG >= DATE_SUB(CURDATE(), INTERVAL 1 year) 
            group by 2
            order by count(l.authorID) desc 
        """
        cursor.execute(query)
        users_data = cursor.fetchall()
        return jsonify(users_data)

    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return jsonify({"error": str(err)}), 500
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()
            print("MySQL connection closed")


@app.route('/api/discordmsgssentmonthly', methods=['GET'])
def get_monthly_discord_msgs():
    """
    Connects to the MySQL database, executes the user query,
    and returns the data as JSON.
    """
    connection = None
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor(dictionary=True)  # dictionary=True makes rows accessible by column name

        query = """
            select count(l.authorID) as 'messageCount',u.displayName from sanity2.loggedmsgs l 
            inner join sanity2.users u on u.userId = l.authorID 
            where l.datetimeMSG >= DATE_SUB(CURDATE(), INTERVAL 1 month) 
            group by 2
            order by count(l.authorID) desc 
        """
        cursor.execute(query)
        users_data = cursor.fetchall()
        return jsonify(users_data)

    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return jsonify({"error": str(err)}), 500
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()
            print("MySQL connection closed")


@app.route('/api/discordmsgssent', methods=['GET'])
def get_weekly_discord_msgs():
    """
    Connects to the MySQL database, executes the user query,
    and returns the data as JSON.
    """
    connection = None
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor(dictionary=True)  # dictionary=True makes rows accessible by column name

        query = """
            select count(l.authorID) as 'messageCount',u.displayName from sanity2.loggedmsgs l 
            inner join sanity2.users u on u.userId = l.authorID 
            where l.datetimeMSG >= DATE_SUB(CURDATE(), INTERVAL 7 DAY) 
            group by 2
            order by count(l.authorID) desc 
        """
        cursor.execute(query)
        users_data = cursor.fetchall()
        return jsonify(users_data)

    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return jsonify({"error": str(err)}), 500
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()
            print("MySQL connection closed")


@app.route('/api/users', methods=['GET'])
def get_users_data():
    """
    Connects to the MySQL database, executes the user query,
    and returns the data as JSON.
    """
    connection = None
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor(dictionary=True)  # dictionary=True makes rows accessible by column name

        query = """
      SELECT
            u.displayName,
            u.points,
            u.rankId,
            r.name AS rank_name,
            u.mainRSN,
            u.altRSN,
            u.joinDate,
            u.diaryPoints,
            u.masterDiaryPoints,
            d.flavourText,
            u.diaryTierClaimed,
            u.nationality,
            COALESCE(pt_sum.points_past_3_months, 0) AS points_past_3_months,
            COALESCE(pt_sum.points_current_month_to_today, 0) AS points_current_month_to_today,
            COALESCE(pt_sum.points_last_month, 0) AS points_last_month,
            COALESCE(pt_sum.points_two_months_ago, 0) AS points_two_months_ago
        FROM
            sanity2.users u
        LEFT JOIN
            sanity2.ranks r ON r.id = u.rankId
        LEFT JOIN
            sanity2.diarytypes d ON d.difficulty = u.diaryTierClaimed
        LEFT JOIN (
            SELECT
                pt.userId,
                SUM(pt.points) AS points_past_3_months,
                SUM(CASE WHEN pt.date >= DATE_FORMAT(CURDATE(), '%Y-%m-01') THEN pt.points ELSE 0 END) AS points_current_month_to_today,
                SUM(CASE WHEN pt.date BETWEEN DATE_FORMAT(CURDATE() - INTERVAL 1 MONTH, '%Y-%m-01') AND LAST_DAY(CURDATE() - INTERVAL 1 MONTH) THEN pt.points ELSE 0 END) AS points_last_month,
                SUM(CASE WHEN pt.date BETWEEN DATE_FORMAT(CURDATE() - INTERVAL 2 MONTH, '%Y-%m-01') AND LAST_DAY(CURDATE() - INTERVAL 2 MONTH) THEN pt.points ELSE 0 END) AS points_two_months_ago
            FROM
                sanity2.pointtracker pt
            WHERE
                -- Pre-filter the pointtracker table for efficiency
                pt.date >= DATE_FORMAT(CURDATE() - INTERVAL 2 MONTH, '%Y-%m-01')
            GROUP BY
                pt.userId
        ) AS pt_sum ON u.userId = pt_sum.userId
        WHERE
            u.isActive = 1
        ORDER BY
            u.rankId DESC,
            u.points DESC;
        """
        cursor.execute(query)
        users_data = cursor.fetchall()
        return jsonify(users_data)

    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return jsonify({"error": str(err)}), 500
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()
            print("MySQL connection closed")


@app.route('/api/diarytimes', methods=['GET'])
def get_diary_times():
    """
    Connects to the MySQL database, executes the points query,
    and returns the data as JSON.
    """
    connection = None
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor(dictionary=True)

        query = """
                select b.name,d.`scale`,d.maxDifficulty,d.timeEasy,d.timeMedium,d.timeHard,d.timeElite,d.timeMaster from sanity2.diarytimes d 
                left join sanity2.bosses b on b.id = d.bossId 
                where timeEasy != 0
                order by name asc
                """
        cursor.execute(query)
        points_data = cursor.fetchall()
        return jsonify(points_data)

    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return jsonify({"error": str(err)}), 500
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()
            print("MySQL connection closed")


@app.route('/api/approveddrops', methods=['GET'])
def get_approved_drops():
    """
    Connects to the MySQL database, executes the points query,
    and returns the data as JSON.
    """
    connection = None
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor(dictionary=True)

        query = """
                    select count(*),u.displayName ,s2.name from sanity2.submissions s
                    inner join sanity2.submissionstatus s2 on s2.id = s.status 
                    inner join sanity2.users u on u.userId = s.reviewedBy 
                    where s.reviewedDate >= DATE_SUB(CURDATE(), INTERVAL 12 MONTH)
                    group by 2,3
                    order by COUNT(*) DESC	
                """
        cursor.execute(query)
        points_data = cursor.fetchall()
        return jsonify(points_data)

    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return jsonify({"error": str(err)}), 500
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()
            print("MySQL connection closed")


@app.route('/api/bingowinners', methods=['GET'])
def get_bingowinners():
    """
    Connects to the MySQL database, executes the points query,
    and returns the data as JSON.
    """
    connection = None
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor(dictionary=True)

        query = """
                    select bingoId,bingoName,teamName,participants from sanity2.bingoWinners bw 
                    order by bingoId DESC 
                """
        cursor.execute(query)
        points_data = cursor.fetchall()
        return jsonify(points_data)

    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return jsonify({"error": str(err)}), 500
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()
            print("MySQL connection closed")


@app.route('/api/approvedpbs', methods=['GET'])
def get_approved_pbs():
    """
    Connects to the MySQL database, executes the points query,
    and returns the data as JSON.
    """
    connection = None
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor(dictionary=True)

        query = """
                    select count(*),u.displayName ,s2.name from sanity2.personalbests s
                    inner join sanity2.submissionstatus s2 on s2.id = s.status 
                    inner join sanity2.users u on u.userId = s.reviewedBy 
                    where s.reviewedDate >= DATE_SUB(CURDATE(), INTERVAL 12 MONTH)  and s.status != 6 
                    group by 2,3
                    order by COUNT(*) DESC	
                """
        cursor.execute(query)
        points_data = cursor.fetchall()
        return jsonify(points_data)

    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return jsonify({"error": str(err)}), 500
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()
            print("MySQL connection closed")


@app.route('/api/pointslimited', methods=['GET'])
def get_points_data_limited():
    """
    Connects to the MySQL database, executes the points query,
    and returns the data as JSON.
    """
    connection = None
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor(dictionary=True)

        query = """
                    SELECT p.Id, u.displayName, p.points, p.notes, s.messageUrl, p.`date` 
                    FROM sanity2.pointtracker p 
                    INNER JOIN sanity2.users u ON u.userId = p.userId 
                    LEFT JOIN sanity2.submissions s ON s.Id = p.dropId 
                    ORDER BY p.Id DESC
                    limit 1000
                """
        cursor.execute(query)
        points_data = cursor.fetchall()
        return jsonify(points_data)

    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return jsonify({"error": str(err)}), 500
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()
            print("MySQL connection closed")


@app.route('/api/points', methods=['GET'])
def get_points_data():
    # 1. Get pagination parameters
    page = request.args.get('page', default=1, type=int)
    per_page = request.args.get('per_page', default=100000, type=int)

    page = max(1, page)
    offset = (page - 1) * per_page

    connection = None
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor(dictionary=True)

        # 2. Main Query with LIMIT and OFFSET
        # Note: Added p.userId and p.dropId just in case you need them later
        query = """
            SELECT p.Id, u.displayName, p.points, p.notes, s.messageUrl, p.`date` 
            FROM sanity2.pointtracker p 
            INNER JOIN sanity2.users u ON u.userId = p.userId 
            LEFT JOIN sanity2.submissions s ON s.Id = p.dropId 
            ORDER BY p.Id DESC
            LIMIT %s OFFSET %s
        """

        cursor.execute(query, (per_page, offset))
        points_data = cursor.fetchall()

        # 3. Get total count for the frontend
        cursor.execute("SELECT COUNT(*) as total FROM sanity2.pointtracker")
        total_count = cursor.fetchone()['total']

        return jsonify({
            "metadata": {
                "total_points_records": total_count,
                "page": page,
                "per_page": per_page,
                "total_pages": (total_count + per_page - 1) // per_page
            },
            "data": points_data
        })

    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return jsonify({"error": str(err)}), 500
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()
            print("MySQL connection closed")


@app.route('/api/bossImages', methods=['GET'])
def get_boss_images():
    """
    Connects to the MySQL database, executes the drops query,
    and returns the data as JSON.
    """
    connection = None
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor(dictionary=True)

        query = """
            select name,imageUrl from sanity2.bosses b 
        """
        cursor.execute(query)
        drops_data = cursor.fetchall()
        return jsonify(drops_data)

    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return jsonify({"error": str(err)}), 500
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()
            print("MySQL connection closed")


@app.route('/api/dropslimited', methods=['GET'])
def get_drops_limited_data():
    """
    Connects to the MySQL database, executes the drops query,
    and returns the data as JSON.
    """
    connection = None
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor(dictionary=True)

        query = """
            SELECT
                s.Id,
                submitter_u.displayName AS submitter,
                GROUP_CONCAT(participant_u.displayName ORDER BY FIND_IN_SET(participant_u.userId, s.participants) SEPARATOR ', ') AS member_names,
                s.notes,
                s.value,
                s2.name AS status_name,
                s.imageUrl,
                s.reviewedDate,
                reviewer_u.displayName AS reviewer
            FROM
                sanity2.submissions s
            LEFT JOIN
                sanity2.users submitter_u ON s.userId = submitter_u.userId
            LEFT JOIN
                sanity2.users participant_u ON FIND_IN_SET(participant_u.userId, s.participants) > 0
            LEFT JOIN
            	sanity2.users reviewer_u ON s.reviewedBy  = reviewer_u.userId
            LEFT JOIN
            	sanity2.submissionstatus s2 ON s.status = s2.id
            WHERE s.status IN (2,3,1,4)
            GROUP BY
                s.Id,
                submitter_u.displayName,
                s.notes,
                s.value,
                s.imageUrl,
                s.reviewedDate,
                s2.name
            ORDER BY
            	Id DESC
            limit 1000
        """
        cursor.execute(query)
        drops_data = cursor.fetchall()
        return jsonify(drops_data)

    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return jsonify({"error": str(err)}), 500
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()
            print("MySQL connection closed")


@app.route('/api/drops', methods=['GET'])
def get_drops_data():
    # 1. Get pagination parameters
    page = request.args.get('page', default=1, type=int)
    per_page = request.args.get('per_page', default=100000, type=int)

    page = max(1, page)
    offset = (page - 1) * per_page

    connection = None
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor(dictionary=True)

        # 2. Main Query with LIMIT and OFFSET
        query = """
                    SELECT
                        s.Id,
                        submitter_u.displayName AS submitter,
                        GROUP_CONCAT(participant_u.displayName ORDER BY sp.id SEPARATOR ', ') AS member_names,
                        s.notes,
                        s.value,
                        s2.name AS status_name,
                        s.imageUrl,
                        s.reviewedDate,
                        reviewer_u.displayName AS reviewer,
                        s.bingo 
                    FROM
                        sanity2.submissions s
                    LEFT JOIN
                        sanity2.submission_participants sp ON s.Id = sp.dropId
                    LEFT JOIN
                        sanity2.users participant_u ON sp.userId = participant_u.userId
                    LEFT JOIN
                        sanity2.users submitter_u ON REPLACE(s.userId, '*', '') = submitter_u.userId
                    LEFT JOIN
                        sanity2.users reviewer_u ON REPLACE(s.reviewedBy, '*', '') = reviewer_u.userId
                    LEFT JOIN
                        sanity2.submissionstatus s2 ON s.status = s2.id
                    WHERE s.status IN (2,3,1,4)
                    GROUP BY
                        s.Id,
                        submitter_u.displayName,
                        s.notes,
                        s.value,
                        s2.name,
                        s.imageUrl,
                        s.reviewedDate,
                        reviewer_u.displayName,
                        s.bingo
                    ORDER BY
                        s.Id DESC
                    LIMIT %s OFFSET %s;
                """

        cursor.execute(query, (per_page, offset))
        drops_data = cursor.fetchall()

        # 3. Get total count for pagination metadata
        count_query = "SELECT COUNT(*) as total FROM sanity2.submissions WHERE status IN (2,3,1,4)"
        cursor.execute(count_query)
        total_count = cursor.fetchone()['total']

        return jsonify({
            "metadata": {
                "total_drops": total_count,
                "page": page,
                "per_page": per_page,
                "total_pages": (total_count + per_page - 1) // per_page
            },
            "data": drops_data
        })

    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return jsonify({"error": str(err)}), 500
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()


@app.route('/api/personalbestslimited', methods=['GET'])
def get_personal_bests_data_limited():
    """
    Connects to the MySQL database, executes the personal bests query,
    and returns the data as JSON.
    """
    connection = None
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor(dictionary=True)

        # Updated query for personalbests
        query = """
            SELECT
                p.submissionId,
                GROUP_CONCAT(u.displayName ORDER BY FIND_IN_SET(u.userId, p.members) SEPARATOR ', ') AS member_names,
                b.name AS boss_name,
                p.scale,
                p.time,
                p.imageUrl,
                p.submittedDate
            FROM
                sanity2.personalbests p
            JOIN
                sanity2.users u ON FIND_IN_SET(u.userId, p.members) > 0 
            JOIN
                sanity2.bosses b ON b.id = p.bossId 
            where p.status = 2
            GROUP BY
                p.submissionId, p.submitterUserId, p.members, p.status,
                p.bossId, p.scale, p.time, p.imageUrl, p.submittedDate
            ORDER BY
                submissionId DESC
            limit 1000
        """
        cursor.execute(query)
        personal_bests_data = cursor.fetchall()
        return jsonify(personal_bests_data)

    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return jsonify({"error": str(err)}), 500
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()
            print("MySQL connection closed")


@app.route('/api/personalbests', methods=['GET'])
def get_personal_bests_data():
    """
    Connects to the MySQL database, executes the personal bests query,
    and returns the data as JSON.
    """
    connection = None
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor(dictionary=True)

        # Updated query for personalbests
        query = """
            SELECT
                p.submissionId,
                GROUP_CONCAT(u.displayName ORDER BY FIND_IN_SET(u.userId, p.members) SEPARATOR ', ') AS member_names,
                b.name AS boss_name,
                p.scale,
                p.time,
                p.imageUrl,
                p.submittedDate,
                p.status
            FROM
                sanity2.personalbests p
            JOIN
                sanity2.users u ON FIND_IN_SET(u.userId, p.members) > 0
            JOIN
                sanity2.bosses b ON b.id = p.bossId 
            where (p.status = 2 or p.status = 6) and p.bossId not in (38,39,42)
            GROUP BY
                p.submissionId, p.submitterUserId, p.members, p.status,
                p.bossId, p.scale, p.time, p.imageUrl, p.submittedDate
            ORDER BY
                submissionId DESC
        """
        cursor.execute(query)
        personal_bests_data = cursor.fetchall()
        return jsonify(personal_bests_data)

    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return jsonify({"error": str(err)}), 500
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()
            print("MySQL connection closed")


# --- NEW BINGO API ENDPOINTS ---


@app.route('/api/bingo/teammembers', methods=['GET'])
def get_bingo_teammembers():
    """
    Returns team member roster. Use ?event_id= to filter by event.
    """
    event_id = request.args.get('event_id', default=None, type=int)
    connection = None
    try:
        connection = mysql.connector.connect(**BINGO_DB_CONFIG)
        cursor = connection.cursor(dictionary=True)

        if event_id:
            query = """
                SELECT btm.team_id, u.displayName, u.mainRSN, u.altRSN, btm.rsn
                FROM bingo_team_members btm
                JOIN sanity2.users u ON btm.user_id = u.userId
                JOIN bingo_teams t ON btm.team_id = t.id
                WHERE t.event_id = %s
            """
            cursor.execute(query, (event_id,))
        else:
            query = """
                SELECT btm.team_id, u.displayName, u.mainRSN, u.altRSN, btm.rsn
                FROM bingo_team_members btm
                JOIN sanity2.users u ON btm.user_id = u.userId
            """
            cursor.execute(query)
        board_data = cursor.fetchall()
        return jsonify(board_data)

    except mysql.connector.Error as err:
        print(f"Error fetching team members: {err}")
        return jsonify({"error": str(err)}), 500
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()


@app.route('/api/bingo/board', methods=['GET'])
def get_bingo_board():
    """
    Fetches all tiles for a bingo board.
    Use ?event_id= to load a specific event, defaults to the active event.
    """
    event_id = request.args.get('event_id', default=None, type=int)
    connection = None
    try:
        connection = mysql.connector.connect(**BINGO_DB_CONFIG)
        cursor = connection.cursor(dictionary=True)

        if event_id:
            cursor.execute("SELECT id FROM bingo_boards WHERE event_id = %s", (event_id,))
        else:
            cursor.execute("""
                SELECT b.id FROM bingo_boards b
                JOIN bingo_events e ON b.event_id = e.id
                WHERE e.is_active = 1 LIMIT 1
            """)
        board_result = cursor.fetchone()
        if not board_result:
            return jsonify([])

        board_id = board_result['id']
        tile_query = """
            SELECT
                t.id as tile_id,
                t.task_name as text,
                t.description as sub_text,
                t.points,
                t.tileType,
                t.dropOrPointReq,
                bbi.bossImageUrl as image_url,
                0 as completed
            FROM bingo_tiles t
            LEFT JOIN sanitybingo.bingo_bossImages bbi ON bbi.bossName = t.task_name
            WHERE t.board_id = %s
            ORDER BY t.position;
        """
        cursor.execute(tile_query, (board_id,))
        board_data = cursor.fetchall()
        return jsonify(board_data)

    except mysql.connector.Error as err:
        print(f"Error fetching bingo board: {err}")
        return jsonify({"error": str(err)}), 500
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()


@app.route('/api/bingo/raiditemvalues', methods=['GET'])
def get_raid_item_values():
    """
    Fetches raid item point values. Use ?event_id= to filter, defaults to active event.
    """
    event_id = request.args.get('event_id', default=None, type=int)
    connection = None
    try:
        connection = mysql.connector.connect(**BINGO_DB_CONFIG)
        cursor = connection.cursor(dictionary=True)
        if event_id:
            query = "SELECT boss, item, points FROM bingo_item_values WHERE event_id = %s;"
            cursor.execute(query, (event_id,))
        else:
            query = "SELECT boss, item, points FROM bingo_item_values WHERE event_id = (SELECT id FROM bingo_events WHERE is_active = 1);"
            cursor.execute(query)
        data = cursor.fetchall()
        return jsonify(data)
    except mysql.connector.Error as err:
        print(f"Error fetching raid item values: {err}")
        return jsonify({"error": str(err)}), 500
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()


@app.route('/api/bingo/bossehb', methods=['GET'])
def get_boss_ehb_values():
    """
    Fetches boss EHB values. Use ?event_id= to filter.
    """
    event_id = request.args.get('event_id', type=int)
    connection = None
    try:
        connection = mysql.connector.connect(**BINGO_DB_CONFIG)
        cursor = connection.cursor(dictionary=True)
        if event_id:
            cursor.execute("SELECT id, boss, ehb, event_id FROM bingo_boss_ehb WHERE event_id = %s ORDER BY boss;", (event_id,))
        else:
            cursor.execute("SELECT id, boss, ehb, event_id FROM bingo_boss_ehb ORDER BY boss;")
        data = cursor.fetchall()
        return jsonify(data)
    except mysql.connector.Error as err:
        print(f"Error fetching boss ehb values: {err}")
        return jsonify({"error": str(err)}), 500
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()


@app.route('/api/bingo/tileitems', methods=['GET'])
def get_bingo_tileitems():
    """
    Returns tile-to-item mappings. Use ?event_id= to filter by event.
    """
    event_id = request.args.get('event_id', default=None, type=int)
    connection = None
    try:
        connection = mysql.connector.connect(**BINGO_DB_CONFIG)
        cursor = connection.cursor(dictionary=True)
        if event_id:
            query = "SELECT id, eventId, dropName, tileId FROM bingo_tile_items WHERE eventId = %s;"
            cursor.execute(query, (event_id,))
        else:
            query = "SELECT id, eventId, dropName, tileId FROM bingo_tile_items;"
            cursor.execute(query)
        data = cursor.fetchall()
        return jsonify(data)
    except mysql.connector.Error as err:
        print(f"Error fetching tile items: {err}")
        return jsonify({"error": str(err)}), 500
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()


@app.route('/api/bingo/teams', methods=['GET'])
def get_bingo_teams():
    """
    Returns bingo teams. Use ?event_id= to filter by event.
    """
    event_id = request.args.get('event_id', default=None, type=int)
    connection = None
    try:
        connection = mysql.connector.connect(**BINGO_DB_CONFIG)
        cursor = connection.cursor(dictionary=True)
        # Ensure image_url column exists (ignore if no ALTER permission)
        try:
            cursor.execute("""
                SELECT COUNT(*) as cnt FROM information_schema.COLUMNS
                WHERE TABLE_SCHEMA = 'sanitybingo' AND TABLE_NAME = 'bingo_teams' AND COLUMN_NAME = 'image_url'
            """)
            if cursor.fetchone()['cnt'] == 0:
                cursor.execute("ALTER TABLE bingo_teams ADD COLUMN image_url VARCHAR(500) DEFAULT NULL")
        except:
            pass

        if event_id:
            query = """SELECT
                        bt.id, bt.name, bt.captain_userid, u_cap.displayName AS captain_name,
                        bt.cocaptain_userid, u_cocap.displayName AS cocaptain_name,
                        bt.event_id, bt.image_url
                    FROM sanitybingo.bingo_teams bt
                    LEFT JOIN sanity2.users u_cap ON u_cap.userId = bt.captain_userid
                    LEFT JOIN sanity2.users u_cocap ON u_cocap.userId = bt.cocaptain_userid
                    WHERE bt.event_id = %s;"""
            cursor.execute(query, (event_id,))
        else:
            query = """SELECT
                        bt.id, bt.name, bt.captain_userid, u_cap.displayName AS captain_name,
                        bt.cocaptain_userid, u_cocap.displayName AS cocaptain_name,
                        bt.event_id, bt.image_url
                    FROM sanitybingo.bingo_teams bt
                    LEFT JOIN sanity2.users u_cap ON u_cap.userId = bt.captain_userid
                    LEFT JOIN sanity2.users u_cocap ON u_cocap.userId = bt.cocaptain_userid;"""
            cursor.execute(query)
        data = cursor.fetchall()
        return jsonify(data)
    except mysql.connector.Error as err:
        print(f"Error fetching teams: {err}")
        return jsonify({"error": str(err)}), 500
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()


@app.route('/api/bingo/overview', methods=['GET'])
def get_bingo_overview():
    """
    Aggregated bingo overview data.
    Use ?event_id= to load a specific event, defaults to the active event.
    """
    event_id = request.args.get('event_id', default=None, type=int)
    connection = None
    try:
        connection = mysql.connector.connect(**BINGO_DB_CONFIG)
        cursor = connection.cursor(dictionary=True)

        if event_id:
            cursor.execute("""
                SELECT e.id as event_id, b.id as board_id
                FROM bingo_events e
                JOIN bingo_boards b ON e.id = b.event_id
                WHERE e.id = %s LIMIT 1
            """, (event_id,))
        else:
            cursor.execute("""
                SELECT e.id as event_id, b.id as board_id
                FROM bingo_events e
                JOIN bingo_boards b ON e.id = b.event_id
                WHERE e.is_active = 1 LIMIT 1
            """)
        event_info = cursor.fetchone()
        if not event_info:
            return jsonify({"error": "No bingo event found"}), 404
        active_event_id = event_info['event_id']
        active_board_id = event_info['board_id']

        # Total tiles on this board
        cursor.execute("SELECT COUNT(*) as total FROM bingo_tiles WHERE board_id = %s", (active_board_id,))
        total_tiles_result = cursor.fetchone()
        total_tiles = total_tiles_result['total'] if total_tiles_result else 25

        # Team leaderboard with per-team completion
        leaderboard_query = """
            SELECT
                t.id as team_id,
                t.name as team_name,
                capt.displayName as captain,
                cocapt.displayName as co_captain,
                COALESCE(SUM(ti.points), 0) as team_points,
                COUNT(DISTINCT c.tile_id) as tiles_done,
                ROUND((COUNT(DISTINCT c.tile_id) / %s) * 100, 1) as completion_percentage
            FROM bingo_teams t
            LEFT JOIN bingo_tile_completion c ON t.id = c.team_id
            LEFT JOIN bingo_tiles ti ON c.tile_id = ti.id
            LEFT JOIN sanity2.users capt ON t.captain_userid = capt.userId
            LEFT JOIN sanity2.users cocapt ON t.cocaptain_userid = cocapt.userId
            WHERE t.event_id = %s
            GROUP BY t.id, t.name, capt.displayName, cocapt.displayName
            ORDER BY team_points DESC;
        """
        cursor.execute(leaderboard_query, (total_tiles, active_event_id))
        team_leaderboard = cursor.fetchall()

        for team in team_leaderboard:
            team['completion_percentage'] = float(team['completion_percentage'])

        overview_data = {
            "event_id": active_event_id,
            "board_id": active_board_id,
            "total_tiles": total_tiles,
            "team_leaderboard": team_leaderboard
        }

        return jsonify(overview_data)

    except mysql.connector.Error as err:
        print(f"Error fetching bingo overview: {err}")
        return jsonify({"error": str(err)}), 500
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()


# --- NEW BINGO BUILDER & MANAGEMENT API ENDPOINTS ---

@app.route('/api/bingo/events', methods=['GET'])
def get_all_events():
    """ Fetches bingo events. Use ?active_only=1 to filter to active events only. """
    active_only = request.args.get('active_only', default=None)
    connection = None
    try:
        connection = mysql.connector.connect(**BINGO_DB_CONFIG, autocommit=True)
        cursor = connection.cursor(dictionary=True)
        # Ensure wom_id column exists
        try:
            cursor.execute("""
                SELECT COUNT(*) as cnt FROM information_schema.COLUMNS
                WHERE TABLE_SCHEMA = 'sanitybingo' AND TABLE_NAME = 'bingo_events' AND COLUMN_NAME = 'wom_id'
            """)
            if cursor.fetchone()['cnt'] == 0:
                cursor.execute("ALTER TABLE bingo_events ADD COLUMN wom_id INT DEFAULT NULL")
        except:
            pass
        if active_only == '1':
            cursor.execute("SELECT id, name, start_date, end_date, is_active, wom_id FROM bingo_events WHERE is_active = 1 ORDER BY start_date DESC;")
        else:
            cursor.execute("SELECT id, name, start_date, end_date, is_active, wom_id FROM bingo_events ORDER BY start_date DESC;")
        events = cursor.fetchall()
        return jsonify(events)
    except mysql.connector.Error as err:
        return jsonify({"error": str(err)}), 500
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()


@app.route('/api/bingo/board_details/<int:event_id>', methods=['GET'])
def get_board_details(event_id):
    """ Fetches all tiles and their associated items for a specific event's board. """
    connection = None
    try:
        connection = mysql.connector.connect(**BINGO_DB_CONFIG)
        cursor = connection.cursor(dictionary=True)

        cursor.execute("SELECT id FROM bingo_boards WHERE event_id = %s", (event_id,))
        board_result = cursor.fetchone()
        if not board_result:
            return jsonify([])

        board_id = board_result['id']

        # Fetch tiles with boss images
        tile_query = """
            SELECT 
                bt.id, 
                bt.position, 
                bt.task_name, 
                bt.description, 
                bt.tileType, 
                bt.dropOrPointReq, 
                bt.points,
                bbi.bossImageUrl as image_url
            FROM bingo_tiles bt 
            LEFT JOIN sanitybingo.bingo_bossImages bbi on bbi.bossName = bt.task_name
            WHERE bt.board_id = %s
            ORDER BY bt.position
        """
        cursor.execute(tile_query, (board_id,))
        tiles = cursor.fetchall()

        if not tiles:
            return jsonify([])

        tile_ids = [tile['id'] for tile in tiles]
        placeholders = ','.join(['%s'] * len(tile_ids))

        # Fetch associated items
        item_query = f"SELECT tileId, dropName FROM bingo_tile_items WHERE tileId IN ({placeholders});"
        cursor.execute(item_query, tuple(tile_ids))
        items = cursor.fetchall()

        items_map = {}
        for item in items:
            tile_id = item['tileId']
            if tile_id not in items_map:
                items_map[tile_id] = []
            items_map[tile_id].append(item['dropName'])

        for tile in tiles:
            tile['items'] = items_map.get(tile['id'], [])

        return jsonify(tiles)

    except mysql.connector.Error as err:
        print(f"Error in get_board_details: {err}")
        return jsonify({"error": str(err)}), 500
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()


@app.route('/api/bingo/board_settings/<int:event_id>', methods=['GET'])
def get_board_settings(event_id):
    """ Returns board-level settings such as the per-line bonus points. """
    connection = None
    try:
        connection = mysql.connector.connect(**BINGO_DB_CONFIG)
        cursor = connection.cursor(dictionary=True)

        # Ensure bonus_points column exists
        try:
            cursor.execute("""
                SELECT COUNT(*) as cnt FROM information_schema.COLUMNS
                WHERE TABLE_SCHEMA = 'sanitybingo' AND TABLE_NAME = 'bingo_boards' AND COLUMN_NAME = 'bonus_points'
            """)
            if cursor.fetchone()['cnt'] == 0:
                cursor.execute("ALTER TABLE bingo_boards ADD COLUMN bonus_points INT DEFAULT 0")
        except:
            pass

        cursor.execute(
            "SELECT id, COALESCE(bonus_points, 0) AS bonus_points FROM bingo_boards WHERE event_id = %s",
            (event_id,)
        )
        board = cursor.fetchone()
        if not board:
            return jsonify({"board_id": None, "bonus_points": 0})
        return jsonify({"board_id": board['id'], "bonus_points": int(board['bonus_points'] or 0)})
    except mysql.connector.Error as err:
        print(f"Error fetching board settings: {err}")
        return jsonify({"error": str(err)}), 500
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()


@app.route('/api/bingo/update_board', methods=['POST'])
def update_bingo_board():
    """
    Updates an existing bingo board. Deletes old tiles and inserts new ones in a transaction.
    """
    data = request.get_json()
    event_id = data.get('eventId')
    tiles_data = data.get('tiles')
    bonus_points = data.get('bonusPoints')

    if not event_id:
        return jsonify({"error": "Missing eventId"}), 400

    if not tiles_data:
        return jsonify({"error": "Missing tiles data"}), 400

    connection = None
    try:
        connection = mysql.connector.connect(**BINGO_DB_CONFIG)
        cursor = connection.cursor()

        # Ensure bonus_points column exists
        try:
            cursor.execute("""
                SELECT COUNT(*) as cnt FROM information_schema.COLUMNS
                WHERE TABLE_SCHEMA = 'sanitybingo' AND TABLE_NAME = 'bingo_boards' AND COLUMN_NAME = 'bonus_points'
            """)
            if cursor.fetchone()[0] == 0:
                cursor.execute("ALTER TABLE bingo_boards ADD COLUMN bonus_points INT DEFAULT 0")
        except:
            pass

        # Get the board_id for this event
        cursor.execute("SELECT id FROM bingo_boards WHERE event_id = %s", (event_id,))
        board_result = cursor.fetchone()
        if not board_result:
            return jsonify({"error": "No board found for this event"}), 404
        board_id = board_result[0]

        # Delete old tile items first
        cursor.execute("SELECT id FROM bingo_tiles WHERE board_id = %s", (board_id,))
        old_tile_ids_result = cursor.fetchall()
        if old_tile_ids_result:
            old_tile_ids = [item[0] for item in old_tile_ids_result]
            placeholders = ','.join(['%s'] * len(old_tile_ids))
            cursor.execute(f"DELETE FROM bingo_tile_items WHERE tileId IN ({placeholders})", tuple(old_tile_ids))

        # Delete old tiles
        cursor.execute("DELETE FROM bingo_tiles WHERE board_id = %s", (board_id,))

        # Insert new tiles
        tile_query = """
            INSERT INTO bingo_tiles (board_id, position, task_name, description, tileType, dropOrPointReq, points)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        item_query = "INSERT INTO bingo_tile_items (eventId, tileId, dropName) VALUES (%s, %s, %s)"

        tiles_inserted = 0
        for i, tile in enumerate(tiles_data):
            # Skip empty tiles
            if not tile.get('taskName') or tile['taskName'].strip() == '':
                continue

            # Determine the boss name to save in task_name
            final_boss_name = tile.get('customBossName', '') if tile.get('bossName') == 'custom' else tile.get(
                'bossName', '')

            # Combine taskName and description with a separator for the description field
            task_name_text = tile.get('taskName', '')
            description_text = tile.get('description', '')
            combined_description = f"{task_name_text} - {description_text}" if description_text else task_name_text

            cursor.execute(tile_query, (
                board_id,
                i + 1,
                final_boss_name,  # Boss name goes in task_name column
                combined_description,  # Combined task and description goes in description column
                tile.get('tileType', 'Unique'),
                tile.get('requirement', 1),
                tile.get('points', 0)
            ))
            tile_id = cursor.lastrowid
            tiles_inserted += 1

            # Insert associated items if any
            if tile.get('items'):
                items = [item.strip().lower() for item in tile['items'].split(',') if item.strip()]
                for item_name in items:
                    cursor.execute(item_query, (event_id, tile_id, item_name))

        # Update board-level bonus points if provided
        if bonus_points is not None:
            cursor.execute(
                "UPDATE bingo_boards SET bonus_points = %s WHERE id = %s",
                (int(bonus_points), board_id)
            )

        connection.commit()
        return jsonify({
            "message": f"Board updated successfully. {tiles_inserted} tiles saved.",
            "tiles_count": tiles_inserted
        }), 200

    except mysql.connector.Error as err:
        if connection:
            connection.rollback()
        print(f"Error updating board: {err}")
        return jsonify({"error": f"Database transaction failed: {err}"}), 500
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()


@app.route('/api/user/rankupnames', methods=['GET'])
def get_users_ranks():
    """
    Fetches all items with their boss and points for the auto-generator.
    This now reflects the user's provided JSON structure.
    """
    connection = None
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor(dictionary=True)
        # This query should match the structure of the user-provided JSON
        query = "select u.mainRSN, orm.osrsName from sanity2.users u inner join sanity2.osrsRankMapping orm on orm.discordRankId = u.rankId ;"
        cursor.execute(query)
        items = cursor.fetchall()
        return jsonify(items)
    except mysql.connector.Error as err:
        return jsonify({"error": f"Database query failed: {err}"}), 500
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()


@app.route('/api/bingo/bossitems', methods=['GET'])
def get_boss_items():
    """
    Fetches all boss items with their point values and drop rates.
    """
    connection = None
    try:
        connection = mysql.connector.connect(**BINGO_DB_CONFIG)
        cursor = connection.cursor(dictionary=True)
        query = "SELECT bossName, droprate, hoursToGetDrop, id, item, itemPoints FROM bingo_boss_items ORDER BY bossName, item;"
        cursor.execute(query)
        items = cursor.fetchall()
        return jsonify(items)
    except mysql.connector.Error as err:
        return jsonify({"error": f"Database query failed: {err}"}), 500
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()


@app.route('/api/bingo/create_event', methods=['POST'])
def create_new_event():
    """
    Creates a new, empty bingo event and an associated empty board.
    """
    data = request.get_json()
    connection = None
    try:
        connection = mysql.connector.connect(**BINGO_DB_CONFIG)
        cursor = connection.cursor()

        # Insert into bingo_events table
        event_query = "INSERT INTO bingo_events (name, start_date, end_date, is_active) VALUES (%s, %s, %s, 0)"
        cursor.execute(event_query, (data['name'], data['start_date'], data['end_date']))
        event_id = cursor.lastrowid

        # Create associated board with the event_id
        board_query = "INSERT INTO bingo_boards (event_id) VALUES (%s)"
        cursor.execute(board_query, (event_id,))

        connection.commit()
        return jsonify({"message": "Event created successfully", "id": event_id}), 201
    except mysql.connector.Error as err:
        if connection:
            connection.rollback()
        print(f"Error creating event: {err}")
        return jsonify({"error": str(err)}), 500
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()


@app.route('/api/bingo/update_event', methods=['POST'])
def update_event():
    """Update an event's name, start_date, end_date, is_active, or wom_id."""
    data = request.get_json()
    event_id = data.get('event_id')
    if not event_id:
        return jsonify({"error": "event_id required"}), 400

    connection = None
    try:
        connection = mysql.connector.connect(**BINGO_DB_CONFIG)
        cursor = connection.cursor()

        # Ensure wom_id column exists
        try:
            cursor.execute("""
                SELECT COUNT(*) as cnt FROM information_schema.COLUMNS
                WHERE TABLE_SCHEMA = 'sanitybingo' AND TABLE_NAME = 'bingo_events' AND COLUMN_NAME = 'wom_id'
            """)
            if cursor.fetchone()['cnt'] == 0:
                cursor.execute("ALTER TABLE bingo_events ADD COLUMN wom_id INT DEFAULT NULL")
        except:
            pass

        sets = []
        params = []
        if 'name' in data and data['name']:
            sets.append("name = %s")
            params.append(data['name'])
        if 'start_date' in data and data['start_date']:
            sets.append("start_date = %s")
            params.append(data['start_date'])
        if 'end_date' in data and data['end_date']:
            sets.append("end_date = %s")
            params.append(data['end_date'])
        if 'is_active' in data:
            sets.append("is_active = %s")
            params.append(1 if data['is_active'] else 0)
        if 'wom_id' in data:
            sets.append("wom_id = %s")
            params.append(data['wom_id'] or None)

        if not sets:
            return jsonify({"error": "Nothing to update"}), 400

        params.append(event_id)
        cursor.execute(f"UPDATE bingo_events SET {', '.join(sets)} WHERE id = %s", params)
        connection.commit()
        return jsonify({"message": "Event updated"}), 200
    except mysql.connector.Error as err:
        if connection: connection.rollback()
        return jsonify({"error": str(err)}), 500
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()


@app.route('/api/bingo/fetch_kc', methods=['POST'])
def fetch_kc():
    """
    Fetches boss KC gains from WiseOldMan for an event's competition and
    updates sanity2.bingobosskc. Expects JSON: {"event_id": int}.
    """
    data = request.get_json() or {}
    event_id = data.get('event_id')
    try:
        result = sync_wom_kc(event_id)
        _log_sync(
            event_id,
            'ok' if result.get('ok') else 'error',
            result.get('message', ''),
            result.get('players', 0),
            result.get('cells', 0),
            result.get('added_bosses', 0),
        )
        if not result.get('ok'):
            return jsonify({"error": result.get('message')}), 400
        return jsonify(result), 200
    except Exception as err:
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Internal error: {err}"}), 500


@app.route('/api/bingo/kc_snapshots', methods=['GET'])
def get_kc_snapshots():
    """
    Returns the KC snapshots recorded over time for an event, so the frontend
    can chart team EHB over time. Use ?event_id= to filter (defaults to the
    active event). Each entry is { time, kc: { rsn: { boss: kc, ... } } }.
    """
    event_id = request.args.get('event_id', type=int)
    connection = None
    try:
        connection = mysql.connector.connect(**BINGO_DB_CONFIG)
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bingo_kc_snapshots (
                id INT AUTO_INCREMENT PRIMARY KEY,
                event_id INT NOT NULL,
                snapshot_time DATETIME NOT NULL,
                data LONGTEXT NOT NULL,
                INDEX idx_event_time (event_id, snapshot_time)
            )
        """)
        if event_id:
            cursor.execute(
                "SELECT snapshot_time, data FROM bingo_kc_snapshots WHERE event_id = %s ORDER BY snapshot_time",
                (event_id,)
            )
        else:
            cursor.execute(
                "SELECT snapshot_time, data FROM bingo_kc_snapshots WHERE event_id = "
                "(SELECT id FROM bingo_events WHERE is_active = 1 ORDER BY id DESC LIMIT 1) "
                "ORDER BY snapshot_time"
            )
        rows = cursor.fetchall()
        snapshots = []
        for row in rows:
            try:
                kc = json.loads(row['data'])
            except (TypeError, ValueError):
                kc = {}
            snapshots.append({
                'time': row['snapshot_time'],
                'kc': kc,
            })
        return jsonify(snapshots)
    except mysql.connector.Error as err:
        print(f"Error fetching kc snapshots: {err}")
        return jsonify({"error": str(err)}), 500
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()


@app.route('/api/bingo/wom_troubleshoot', methods=['GET'])
def wom_troubleshoot():
    """
    Troubleshooting view: shows WiseOldMan competition/participants/KCs,
    the boss mapping, team-member RSNs, and what is currently in the DB.
    """
    event_id = request.args.get('event_id', type=int)

    bingo_conn = mysql.connector.connect(**BINGO_DB_CONFIG)
    try:
        cur = bingo_conn.cursor(dictionary=True)
        if event_id:
            cur.execute("SELECT id, name, wom_id, start_date, end_date, is_active FROM bingo_events WHERE id = %s", (event_id,))
        else:
            cur.execute("SELECT id, name, wom_id, start_date, end_date, is_active FROM bingo_events ORDER BY start_date DESC LIMIT 1")
        event = cur.fetchone()
        cur.close()
    finally:
        bingo_conn.close()

    resp = {
        "event": event,
        "competition": None,
        "wom_participants": [],
        "wom_boss_gains": [],
        "db_kc": [],
        "mapping": [],
        "boss_metrics": [],
        "members": [],
        "last_sync": None,
        "error": None,
    }
    if not event:
        resp["error"] = "No event found."
        return jsonify(resp)

    # Boss mapping
    try:
        bingo_conn = mysql.connector.connect(**BINGO_DB_CONFIG)
        cur = bingo_conn.cursor(dictionary=True)
        cur.execute("SELECT wom_metric, boss_name FROM bingo_boss_mapping ORDER BY wom_metric")
        resp["mapping"] = cur.fetchall()
        cur.close()
        bingo_conn.close()
    except mysql.connector.Error:
        resp["mapping"] = []

    # Team member roster (RSNs to match)
    try:
        bingo_conn = mysql.connector.connect(**BINGO_DB_CONFIG)
        cur = bingo_conn.cursor(dictionary=True)
        cur.execute("""
            SELECT btm.team_id, t.name AS team_name, u.displayName, u.mainRSN, u.altRSN, btm.rsn
            FROM bingo_team_members btm
            JOIN sanity2.users u ON btm.user_id = u.userId
            JOIN bingo_teams t ON btm.team_id = t.id
            WHERE t.event_id = %s
        """, (event['id'],))
        resp["members"] = cur.fetchall()
        cur.close()
        bingo_conn.close()
    except mysql.connector.Error:
        resp["members"] = []

    # Current DB KC rows
    try:
        kc_conn = mysql.connector.connect(**DB_CONFIG)
        cur = kc_conn.cursor(dictionary=True)
        cur.execute("SHOW COLUMNS FROM sanity2.bingobosskc")
        cols = [row['Field'] for row in cur.fetchall() if row['Field'] != 'RSN']
        cur.execute("SELECT * FROM sanity2.bingobosskc")
        db_kc = []
        for row in cur.fetchall():
            bosses = {}
            for c in cols:
                try:
                    v = int(row[c] or 0)
                except (TypeError, ValueError):
                    v = 0
                if v > 0:
                    bosses[c] = v
            db_kc.append({"RSN": row['RSN'], "totalKc": sum(bosses.values()), "bosses": bosses})
        resp["db_kc"] = db_kc
        cur.close()
        kc_conn.close()
    except mysql.connector.Error:
        resp["db_kc"] = []

    # Per-boss KC totals + mapping + tile assignment
    try:
        kc_conn = mysql.connector.connect(**DB_CONFIG)
        cur = kc_conn.cursor(dictionary=True)
        cur.execute("SHOW COLUMNS FROM sanity2.bingobosskc")
        boss_cols = [row['Field'] for row in cur.fetchall() if row['Field'] != 'RSN']
        sums = {}
        if boss_cols:
            sum_sql = ', '.join(f"SUM(`{c}`) AS `{c}`" for c in boss_cols)
            cur.execute(f"SELECT {sum_sql} FROM sanity2.bingobosskc")
            sums = cur.fetchone() or {}
        cur.close()
        kc_conn.close()
    except mysql.connector.Error:
        boss_cols = []
        sums = {}

    mapping_by_metric = {m['wom_metric']: m['boss_name'] for m in resp["mapping"]}

    tiles = []
    try:
        bingo_conn = mysql.connector.connect(**BINGO_DB_CONFIG)
        cur = bingo_conn.cursor(dictionary=True)
        cur.execute("""
            SELECT t.position, t.task_name
            FROM bingo_tiles t
            JOIN bingo_boards b ON t.board_id = b.id
            WHERE b.event_id = %s
            ORDER BY t.position
        """, (event['id'],))
        tiles = cur.fetchall()
        cur.close()
        bingo_conn.close()
    except mysql.connector.Error:
        tiles = []

    tile_by_name = {}
    for t in tiles:
        key = _norm_name(t.get('task_name') or '')
        if key:
            tile_by_name.setdefault(key, []).append(t.get('position'))

    boss_metrics = []
    for metric in boss_cols:
        total_kc = int(sums.get(metric) or 0) if sums else 0
        mapped_name = mapping_by_metric.get(metric)
        norm = _norm_name(metric)
        positions = tile_by_name.get(norm) or []
        if mapped_name and not positions:
            positions = tile_by_name.get(_norm_name(mapped_name)) or []
        boss_metrics.append({
            "metric": metric,
            "boss_name": mapped_name,
            "total_kc": total_kc,
            "tiles": ", ".join(f"#{p}" for p in sorted(positions)) if positions else "",
            "mapped": mapped_name is not None,
            "on_tile": bool(positions),
        })
    resp["boss_metrics"] = boss_metrics

    # Live WiseOldMan data
    if event.get('wom_id'):
        competition = _fetch_competition(event['wom_id'])
        if competition:
            resp["competition"] = {
                "id": competition.get('id'),
                "title": competition.get('title'),
                "metric": competition.get('metric'),
                "groupId": competition.get('groupId'),
                "startsAt": competition.get('startsAt'),
                "endsAt": competition.get('endsAt'),
                "participantCount": competition.get('participantCount'),
            }
            participants = []
            for p in competition.get('participations', []):
                player = p.get('player', {})
                participants.append({
                    "username": player.get('username'),
                    "displayName": player.get('displayName'),
                    "teamName": p.get('teamName'),
                    "ehbGained": (p.get('progress') or {}).get('gained', 0),
                })
            resp["wom_participants"] = participants
        else:
            resp["error"] = f"Could not fetch WiseOldMan competition {event['wom_id']}."

    resp["last_sync"] = _get_last_sync(event['id'])

    # Match each member's RSNs against WOM participants and DB rows
    wom_usernames = {_norm_name(p.get('username', '')) for p in resp["wom_participants"] if p.get('username')}
    db_rsns = {_norm_name(k['RSN']) for k in resp["db_kc"]}
    db_by_rsn = {_norm_name(k['RSN']): k for k in resp["db_kc"]}
    for m in resp["members"]:
        rsns = [r for r in (m.get('rsn'), m.get('mainRSN'), m.get('altRSN')) if r]
        m["rsns"] = rsns
        m["matchedWom"] = any(_norm_name(r) in wom_usernames for r in rsns)
        m["matchedDb"] = any(_norm_name(r) in db_rsns for r in rsns)
        total = 0
        for r in rsns:
            row = db_by_rsn.get(_norm_name(r))
            if row:
                total += row['totalKc']
        m["dbTotalKc"] = total

    return jsonify(resp)


@app.route('/api/bingo/copy_board', methods=['POST'])
def copy_bingo_board():
    """
    Copies all tiles from a source event's board to a target event's board.
    Expects JSON: {"source_event_id": int, "target_event_id": int}
    """
    data = request.get_json()
    source_event_id = data.get('source_event_id')
    target_event_id = data.get('target_event_id')

    if not source_event_id or not target_event_id:
        return jsonify({"error": "Missing source_event_id or target_event_id"}), 400

    connection = None
    try:
        connection = mysql.connector.connect(**BINGO_DB_CONFIG)
        cursor = connection.cursor()

        # Ensure bonus_points column exists
        try:
            cursor.execute("""
                SELECT COUNT(*) as cnt FROM information_schema.COLUMNS
                WHERE TABLE_SCHEMA = 'sanitybingo' AND TABLE_NAME = 'bingo_boards' AND COLUMN_NAME = 'bonus_points'
            """)
            if cursor.fetchone()[0] == 0:
                cursor.execute("ALTER TABLE bingo_boards ADD COLUMN bonus_points INT DEFAULT 0")
        except:
            pass

        # Get source board_id
        cursor.execute("SELECT id FROM bingo_boards WHERE event_id = %s", (source_event_id,))
        source_board = cursor.fetchone()
        if not source_board:
            return jsonify({"error": "Source board not found"}), 404

        # Get target board_id
        cursor.execute("SELECT id FROM bingo_boards WHERE event_id = %s", (target_event_id,))
        target_board = cursor.fetchone()
        if not target_board:
            return jsonify({"error": "Target board not found"}), 404

        source_board_id = source_board[0]
        target_board_id = target_board[0]

        # Clear existing tiles on target board
        cursor.execute("SELECT id FROM bingo_tiles WHERE board_id = %s", (target_board_id,))
        old_tile_ids = [row[0] for row in cursor.fetchall()]
        if old_tile_ids:
            placeholders = ','.join(['%s'] * len(old_tile_ids))
            cursor.execute(f"DELETE FROM bingo_tile_items WHERE tileId IN ({placeholders})", tuple(old_tile_ids))
        cursor.execute("DELETE FROM bingo_tiles WHERE board_id = %s", (target_board_id,))

        # Copy tiles from source
        cursor.execute("""
            SELECT position, task_name, description, tileType, dropOrPointReq, points
            FROM bingo_tiles WHERE board_id = %s ORDER BY position
        """, (source_board_id,))
        source_tiles = cursor.fetchall()

        tile_id_map = {}  # old_tile_id -> new_tile_id
        for tile in source_tiles:
            cursor.execute("""
                INSERT INTO bingo_tiles (board_id, position, task_name, description, tileType, dropOrPointReq, points)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (target_board_id, tile[0], tile[1], tile[2], tile[3], tile[4], tile[5]))
            new_tile_id = cursor.lastrowid

            # Get the old tile's ID for item copy
            cursor.execute("""
                SELECT id FROM bingo_tiles
                WHERE board_id = %s AND position = %s
            """, (source_board_id, tile[0]))
            old_tile = cursor.fetchone()
            if old_tile:
                tile_id_map[old_tile[0]] = new_tile_id

        # Copy tile items
        if tile_id_map:
            old_ids = list(tile_id_map.keys())
            placeholders = ','.join(['%s'] * len(old_ids))
            cursor.execute(f"""
                SELECT tileId, dropName FROM bingo_tile_items WHERE tileId IN ({placeholders})
            """, tuple(old_ids))
            for item in cursor.fetchall():
                new_tile_id = tile_id_map[item[0]]
                cursor.execute(
                    "INSERT INTO bingo_tile_items (eventId, tileId, dropName) VALUES (%s, %s, %s)",
                    (target_event_id, new_tile_id, item[1])
                )

        # Copy board-level bonus points
        cursor.execute("SELECT COALESCE(bonus_points, 0) FROM bingo_boards WHERE id = %s", (source_board_id,))
        source_bonus = cursor.fetchone()
        if source_bonus:
            cursor.execute("UPDATE bingo_boards SET bonus_points = %s WHERE id = %s", (source_bonus[0], target_board_id))

        connection.commit()
        return jsonify({
            "message": f"Copied {len(source_tiles)} tiles from event {source_event_id} to event {target_event_id}",
            "tiles_count": len(source_tiles)
        }), 200

    except mysql.connector.Error as err:
        if connection:
            connection.rollback()
        print(f"Error copying board: {err}")
        return jsonify({"error": str(err)}), 500
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()


# Boss Items Management
@app.route('/api/bingo/update_boss_item', methods=['POST'])
def update_boss_item():
    data = request.get_json()
    connection = None
    try:
        connection = mysql.connector.connect(**BINGO_DB_CONFIG)
        cursor = connection.cursor()

        if data.get('id'):
            # Update existing
            query = """UPDATE bingo_boss_items 
                       SET bossName=%s, item=%s, itemPoints=%s, droprate=%s, hoursToGetDrop=%s 
                       WHERE id=%s"""
            cursor.execute(query, (data['bossName'], data['item'], data['itemPoints'],
                                   data['droprate'], data['hoursToGetDrop'], data['id']))
        else:
            # Insert new
            query = """INSERT INTO bingo_boss_items (bossName, item, itemPoints, droprate, hoursToGetDrop) 
                       VALUES (%s, %s, %s, %s, %s)"""
            cursor.execute(query, (data['bossName'], data['item'], data['itemPoints'],
                                   data['droprate'], data['hoursToGetDrop']))

        connection.commit()
        return jsonify({"message": "Boss item saved successfully"}), 200
    except mysql.connector.Error as err:
        if connection: connection.rollback()
        return jsonify({"error": str(err)}), 500
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()


@app.route('/api/bingo/delete_boss_item', methods=['POST'])
def delete_boss_item():
    data = request.get_json()
    connection = None
    try:
        connection = mysql.connector.connect(**BINGO_DB_CONFIG)
        cursor = connection.cursor()
        cursor.execute("DELETE FROM bingo_boss_items WHERE id = %s", (data['id'],))
        connection.commit()
        return jsonify({"message": "Boss item deleted successfully"}), 200
    except mysql.connector.Error as err:
        if connection: connection.rollback()
        return jsonify({"error": str(err)}), 500
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()


@app.route('/api/bingo/update_boss_ehb', methods=['POST'])
def update_boss_ehb():
    data = request.get_json()
    connection = None
    try:
        connection = mysql.connector.connect(**BINGO_DB_CONFIG)
        cursor = connection.cursor()

        # Get the active event ID, or use NULL if none exists
        cursor.execute("SELECT id FROM bingo_events WHERE is_active = 1 LIMIT 1")
        event_result = cursor.fetchone()
        event_id = event_result[0] if event_result else None

        if data.get('isUpdate'):
            # Update existing
            query = "UPDATE bingo_boss_ehb SET ehb=%s WHERE boss=%s"
            cursor.execute(query, (data['ehb'], data['boss']))
        else:
            # Insert new
            query = "INSERT INTO bingo_boss_ehb (boss, ehb, event_id) VALUES (%s, %s, %s)"
            cursor.execute(query, (data['boss'], data['ehb'], event_id))

        connection.commit()
        return jsonify({"message": "Boss EHB saved successfully"}), 200
    except mysql.connector.Error as err:
        if connection: connection.rollback()
        print(f"Error updating boss EHB: {err}")
        return jsonify({"error": str(err)}), 500
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()


@app.route('/api/bingo/delete_boss_ehb', methods=['POST'])
def delete_boss_ehb():
    data = request.get_json()
    connection = None
    try:
        connection = mysql.connector.connect(**BINGO_DB_CONFIG)
        cursor = connection.cursor()
        cursor.execute("DELETE FROM bingo_boss_ehb WHERE boss = %s", (data['boss'],))
        connection.commit()
        return jsonify({"message": "Boss EHB deleted successfully"}), 200
    except mysql.connector.Error as err:
        if connection: connection.rollback()
        return jsonify({"error": str(err)}), 500
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()


# --- USER LIST ---
@app.route('/api/users/list', methods=['GET'])
def get_users_list():
    """Returns all users for dropdowns. userId returned as string to avoid JS precision loss."""
    connection = None
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT CAST(userId AS CHAR) as userId, displayName FROM sanity2.users ORDER BY displayName;")
        return jsonify(cursor.fetchall())
    except mysql.connector.Error as err:
        return jsonify({"error": str(err)}), 500
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()


@app.route('/api/bingo/users_rsns', methods=['GET'])
def get_users_rsns():
    """Returns every user's display name and RSNs, for resolving KC RSNs to names."""
    connection = None
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT displayName, mainRSN, altRSN FROM sanity2.users ORDER BY displayName;")
        return jsonify(cursor.fetchall())
    except mysql.connector.Error as err:
        return jsonify({"error": str(err)}), 500
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()


# --- BOSS IMAGES CRUD ---
@app.route('/api/bingo/boss_images', methods=['GET'])
def get_bingo_boss_images():
    connection = None
    try:
        connection = mysql.connector.connect(**BINGO_DB_CONFIG)
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT id, bossName, bossImageUrl FROM bingo_bossImages ORDER BY bossName;")
        return jsonify(cursor.fetchall())
    except mysql.connector.Error as err:
        return jsonify({"error": str(err)}), 500
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()


@app.route('/api/bingo/update_boss_image', methods=['POST'])
def update_boss_image():
    data = request.get_json()
    connection = None
    try:
        connection = mysql.connector.connect(**BINGO_DB_CONFIG)
        cursor = connection.cursor()
        if data.get('id'):
            cursor.execute("UPDATE bingo_bossImages SET bossName=%s, bossImageUrl=%s WHERE id=%s",
                           (data['bossName'], data.get('bossImageUrl', ''), data['id']))
        else:
            cursor.execute("INSERT INTO bingo_bossImages (bossName, bossImageUrl) VALUES (%s, %s)",
                           (data['bossName'], data.get('bossImageUrl', '')))
        connection.commit()
        return jsonify({"message": "Boss image saved"}), 200
    except mysql.connector.Error as err:
        if connection: connection.rollback()
        return jsonify({"error": str(err)}), 500
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()


@app.route('/api/bingo/delete_boss_image', methods=['POST'])
def delete_boss_image():
    data = request.get_json()
    connection = None
    try:
        connection = mysql.connector.connect(**BINGO_DB_CONFIG)
        cursor = connection.cursor()
        cursor.execute("DELETE FROM bingo_bossImages WHERE id = %s", (data['id'],))
        connection.commit()
        return jsonify({"message": "Boss image deleted"}), 200
    except mysql.connector.Error as err:
        if connection: connection.rollback()
        return jsonify({"error": str(err)}), 500
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()


# --- TEAM MANAGEMENT ---
@app.route('/api/bingo/add_team', methods=['POST'])
def add_team():
    data = request.get_json()
    if not data.get('captain_userid'):
        return jsonify({"error": "captain_userid is required"}), 400
    connection = None
    try:
        connection = mysql.connector.connect(**BINGO_DB_CONFIG)
        cursor = connection.cursor()
        cursor.execute(
            "INSERT INTO bingo_teams (event_id, name, captain_userid, cocaptain_userid) VALUES (%s, %s, %s, %s)",
            (data['event_id'], data['name'], data['captain_userid'], data.get('cocaptain_userid') or None)
        )
        team_id = cursor.lastrowid

        # Add captain and co-captain as team members
        cursor.execute(
            "INSERT INTO bingo_team_members (team_id, user_id, bingo_id) VALUES (%s, %s, %s)",
            (team_id, data['captain_userid'], data['event_id'])
        )
        if data.get('cocaptain_userid'):
            cursor.execute(
                "INSERT INTO bingo_team_members (team_id, user_id, bingo_id) VALUES (%s, %s, %s)",
                (team_id, data['cocaptain_userid'], data['event_id'])
            )

        connection.commit()
        return jsonify({"message": "Team added", "id": team_id}), 201
    except mysql.connector.Error as err:
        if connection: connection.rollback()
        return jsonify({"error": str(err)}), 500
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()


@app.route('/api/bingo/delete_team', methods=['POST'])
def delete_team():
    data = request.get_json()
    connection = None
    try:
        connection = mysql.connector.connect(**BINGO_DB_CONFIG)
        cursor = connection.cursor()
        cursor.execute("DELETE FROM bingo_team_members WHERE team_id = %s", (data['team_id'],))
        cursor.execute("DELETE FROM bingo_teams WHERE id = %s", (data['team_id'],))
        connection.commit()
        return jsonify({"message": "Team deleted"}), 200
    except mysql.connector.Error as err:
        if connection: connection.rollback()
        return jsonify({"error": str(err)}), 500
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()


@app.route('/api/bingo/update_team', methods=['POST'])
def update_team():
    """Update team captain/co-captain/image/name. Only updates fields that are provided."""
    data = request.get_json()
    connection = None
    try:
        connection = mysql.connector.connect(**BINGO_DB_CONFIG)
        cursor = connection.cursor()

        sets = []
        params = []
        if 'captain_userid' in data and data['captain_userid'] is not None:
            sets.append("captain_userid = %s")
            params.append(data['captain_userid'])
        if 'cocaptain_userid' in data and data['cocaptain_userid'] is not None:
            sets.append("cocaptain_userid = %s")
            params.append(data['cocaptain_userid'])
        if 'image_url' in data:
            sets.append("image_url = %s")
            params.append(data['image_url'])
        if 'name' in data and data['name']:
            sets.append("name = %s")
            params.append(data['name'])

        if sets:
            params.append(data['team_id'])
            cursor.execute(f"UPDATE bingo_teams SET {', '.join(sets)} WHERE id = %s", params)

        connection.commit()
        return jsonify({"message": "Team updated"}), 200
    except mysql.connector.Error as err:
        if connection: connection.rollback()
        return jsonify({"error": str(err)}), 500
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()


@app.route('/api/bingo/team_images/<path:filename>')
def serve_team_image(filename):
    """Serve an uploaded team logo from disk."""
    return send_from_directory(TEAM_IMAGE_DIR, filename)


@app.route('/api/bingo/upload_team_image', methods=['POST'])
def upload_team_image():
    """Upload a team logo image, store it on disk, and save its URL to the team."""
    if request.content_length and request.content_length > MAX_UPLOAD_SIZE:
        return jsonify({"error": "File too large (max 5 MB)"}), 413

    team_id_raw = request.form.get('team_id')
    file = request.files.get('file')
    if not team_id_raw or file is None or file.filename == '':
        return jsonify({"error": "team_id and file are required"}), 400

    try:
        team_id = int(team_id_raw)
    except (TypeError, ValueError):
        return jsonify({"error": "team_id must be an integer"}), 400

    ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        return jsonify({"error": "Unsupported file type"}), 400

    os.makedirs(TEAM_IMAGE_DIR, exist_ok=True)
    filename = f"team_{team_id}_{int(time.time())}.{ext}"
    file_path = os.path.join(TEAM_IMAGE_DIR, filename)

    connection = None
    try:
        connection = mysql.connector.connect(**BINGO_DB_CONFIG)
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT image_url FROM bingo_teams WHERE id = %s", (team_id,))
        row = cursor.fetchone()
        if not row:
            return jsonify({"error": "Team not found"}), 404
        old_url = row.get('image_url')

        file.save(file_path)

        image_url = f"/api/bingo/team_images/{filename}"
        cursor.execute("UPDATE bingo_teams SET image_url = %s WHERE id = %s", (image_url, team_id))
        connection.commit()

        # Clean up the previous uploaded logo (only files this app manages).
        if old_url and old_url.startswith('/api/bingo/team_images/'):
            old_path = os.path.join(TEAM_IMAGE_DIR, os.path.basename(old_url))
            if os.path.exists(old_path) and old_path != file_path:
                try:
                    os.remove(old_path)
                except OSError:
                    pass

        return jsonify({"message": "Team image uploaded", "image_url": image_url}), 200
    except mysql.connector.Error as err:
        if connection:
            connection.rollback()
        return jsonify({"error": str(err)}), 500
    except OSError as err:
        return jsonify({"error": f"Failed to save file: {err}"}), 500
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()


@app.route('/api/bingo/import_teams', methods=['POST'])
def import_teams():
    """
    Import teams from comma-separated text.
    Format per line: TeamName, DisplayName, RSN
    First member is captain, second is co-captain.
    """
    data = request.get_json()
    event_id = data.get('event_id')
    lines = data.get('lines', '')
    if not event_id or not lines:
        return jsonify({"error": "event_id and lines required"}), 400

    connection = None
    results = []
    failed = []
    try:
        connection = mysql.connector.connect(**BINGO_DB_CONFIG)
        cursor = connection.cursor()

        # Ensure rsn column exists
        try:
            cursor.execute("""
                SELECT COUNT(*) as cnt FROM information_schema.COLUMNS
                WHERE TABLE_SCHEMA = 'sanitybingo' AND TABLE_NAME = 'bingo_team_members' AND COLUMN_NAME = 'rsn'
            """)
            if cursor.fetchone()['cnt'] == 0:
                cursor.execute("ALTER TABLE bingo_team_members ADD COLUMN rsn VARCHAR(35) DEFAULT NULL")
        except:
            pass

        # Get user ID map
        user_conn = mysql.connector.connect(**DB_CONFIG)
        user_cursor = user_conn.cursor(dictionary=True)
        user_cursor.execute("SELECT userId, displayName FROM sanity2.users")
        user_map = {row['displayName'].lower(): row['userId'] for row in user_cursor.fetchall()}
        user_cursor.close()
        user_conn.close()

        for line in lines.strip().split('\n'):
            parts = [p.strip() for p in line.split(',') if p.strip()]
            if len(parts) < 2:
                continue

            team_name = parts[0]
            members_raw = parts[1:]  # [displayName, rsn, displayName, rsn, ...]
            # Group into pairs: (displayName, rsn)
            pairs = []
            for i in range(0, len(members_raw), 2):
                name = members_raw[i]
                rsn = members_raw[i + 1] if i + 1 < len(members_raw) else ''
                pairs.append((name, rsn))

            if not pairs:
                continue

            captain_name = pairs[0][0]
            captain_id = user_map.get(captain_name.lower())
            if not captain_id:
                failed.append(f"{team_name}: captain '{captain_name}' not found")
                continue

            cocaptain_name = pairs[1][0] if len(pairs) > 1 else ''
            cocaptain_id = user_map.get(cocaptain_name.lower()) if cocaptain_name else None

            # Create team
            cursor.execute(
                "INSERT INTO bingo_teams (event_id, name, captain_userid, cocaptain_userid) VALUES (%s, %s, %s, %s)",
                (event_id, team_name, captain_id, cocaptain_id)
            )
            team_id = cursor.lastrowid

            # Add all members
            added = 0
            line_failed = []
            for name, rsn in pairs:
                uid = user_map.get(name.lower())
                if not uid:
                    line_failed.append(name)
                    continue
                cursor.execute(
                    "INSERT INTO bingo_team_members (team_id, user_id, bingo_id, rsn) VALUES (%s, %s, %s, %s)",
                    (team_id, uid, event_id, rsn or None)
                )
                added += 1

            if line_failed:
                failed.append(f"{team_name}: unknown users: {', '.join(line_failed)}")
            results.append(f"OK {team_name}: {added} members")

        connection.commit()
        resp = {"message": "\n".join(results)}
        if failed:
            resp["failed"] = failed
        return jsonify(resp), 200
    except mysql.connector.Error as err:
        if connection: connection.rollback()
        return jsonify({"error": str(err)}), 500
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()


@app.route('/api/bingo/add_team_member', methods=['POST'])
def add_team_member():
    data = request.get_json()
    connection = None
    try:
        connection = mysql.connector.connect(**BINGO_DB_CONFIG)
        cursor = connection.cursor()
        # Get bingo_id from team's event
        cursor.execute("SELECT event_id FROM bingo_teams WHERE id = %s", (data['team_id'],))
        team = cursor.fetchone()
        if not team:
            return jsonify({"error": "Team not found"}), 404
        cursor.execute(
            "INSERT INTO bingo_team_members (team_id, user_id, bingo_id, rsn) VALUES (%s, %s, %s, %s)",
            (data['team_id'], data['user_id'], team[0], data.get('rsn') or None)
        )
        connection.commit()
        return jsonify({"message": "Member added"}), 201
    except mysql.connector.Error as err:
        if connection: connection.rollback()
        return jsonify({"error": str(err)}), 500
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()


@app.route('/api/bingo/remove_team_member', methods=['POST'])
def remove_team_member():
    data = request.get_json()
    connection = None
    try:
        connection = mysql.connector.connect(**BINGO_DB_CONFIG)
        cursor = connection.cursor()
        cursor.execute(
            "DELETE FROM bingo_team_members WHERE team_id = %s AND user_id = %s",
            (data['team_id'], data['user_id'])
        )
        connection.commit()
        return jsonify({"message": "Member removed"}), 200
    except mysql.connector.Error as err:
        if connection: connection.rollback()
        return jsonify({"error": str(err)}), 500
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()


@app.route('/api/bingo/update_member_rsn', methods=['POST'])
def update_member_rsn():
    """Update a team member's RSN."""
    data = request.get_json()
    connection = None
    try:
        connection = mysql.connector.connect(**BINGO_DB_CONFIG)
        cursor = connection.cursor()
        cursor.execute(
            "UPDATE bingo_team_members SET rsn = %s WHERE team_id = %s AND user_id = %s",
            (data.get('rsn') or None, data['team_id'], data['user_id'])
        )
        connection.commit()
        return jsonify({"message": "RSN updated"}), 200
    except mysql.connector.Error as err:
        if connection: connection.rollback()
        return jsonify({"error": str(err)}), 500
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()


# --- MASS UPDATE ITEMS & EHB ---
@app.route('/api/bingo/mass_update_items', methods=['POST'])
def mass_update_items():
    """Receives full JSON array of items and replaces all bingo_boss_items."""
    data = request.get_json()
    if not isinstance(data, list):
        return jsonify({"error": "Expected a JSON array of items"}), 400
    connection = None
    try:
        connection = mysql.connector.connect(**BINGO_DB_CONFIG)
        cursor = connection.cursor()
        cursor.execute("DELETE FROM bingo_boss_items")
        for item in data:
            cursor.execute(
                "INSERT INTO bingo_boss_items (bossName, item, itemPoints, droprate, hoursToGetDrop) VALUES (%s, %s, %s, %s, %s)",
                (item.get('bossName', ''), item.get('item', ''), item.get('itemPoints', 0),
                 item.get('droprate', 0), item.get('hoursToGetDrop', 0))
            )
        connection.commit()
        return jsonify({"message": f"{len(data)} items updated"}), 200
    except mysql.connector.Error as err:
        if connection: connection.rollback()
        return jsonify({"error": str(err)}), 500
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()


@app.route('/api/bingo/mass_update_ehb', methods=['POST'])
def mass_update_ehb():
    """Receives full JSON array and replaces ALL bingo_boss_ehb for the given event."""
    data = request.get_json()
    if not isinstance(data, list):
        return jsonify({"error": "Expected a JSON array"}), 400
    event_id = request.args.get('event_id', type=int)
    if not event_id:
        return jsonify({"error": "event_id query parameter is required"}), 400
    connection = None
    try:
        connection = mysql.connector.connect(**BINGO_DB_CONFIG)
        cursor = connection.cursor()
        # Delete all existing EHB entries, then insert fresh for this event
        cursor.execute("DELETE FROM bingo_boss_ehb")
        for e in data:
            cursor.execute(
                "INSERT INTO bingo_boss_ehb (event_id, boss, ehb) VALUES (%s, %s, %s)",
                (event_id, e.get('boss', ''), e.get('ehb', 0))
            )
        connection.commit()
        return jsonify({"message": f"{len(data)} EHB entries updated"}), 200
    except mysql.connector.Error as err:
        if connection: connection.rollback()
        return jsonify({"error": str(err)}), 500
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()


# --- DROP ASSIGNMENT ---
@app.route('/api/bingo/drop_assignments', methods=['GET'])
def get_drop_assignments():
    """Returns all manual drop→tile assignments for an event."""
    event_id = request.args.get('event_id', type=int)
    connection = None
    try:
        connection = mysql.connector.connect(**BINGO_DB_CONFIG)
        cursor = connection.cursor(dictionary=True)
        # Ensure the table exists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bingo_drop_assignments (
                id INT AUTO_INCREMENT PRIMARY KEY,
                submission_id INT NOT NULL,
                tile_id INT NOT NULL
            )
        """)
        if event_id:
            cursor.execute("""
                SELECT da.id, da.submission_id, da.tile_id, t.position, t.task_name, t.tileType
                FROM bingo_drop_assignments da
                JOIN bingo_tiles t ON da.tile_id = t.id
                JOIN bingo_boards b ON t.board_id = b.id
                WHERE b.event_id = %s
                ORDER BY t.position
            """, (event_id,))
        else:
            cursor.execute("""
                SELECT da.id, da.submission_id, da.tile_id, t.position, t.task_name, t.tileType
                FROM bingo_drop_assignments da
                JOIN bingo_tiles t ON da.tile_id = t.id
                JOIN bingo_boards b ON t.board_id = b.id
                JOIN bingo_events e ON b.event_id = e.id
                WHERE e.is_active = 1
                ORDER BY t.position
            """)
        return jsonify(cursor.fetchall())
    except mysql.connector.Error as err:
        return jsonify({"error": str(err)}), 500
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()


@app.route('/api/bingo/assign_drop_to_tile', methods=['POST'])
def assign_drop_to_tile():
    """Manually assign a submission to a tile."""
    data = request.get_json()
    if not data.get('submission_id') or not data.get('tile_id'):
        return jsonify({"error": "submission_id and tile_id required"}), 400
    connection = None
    try:
        connection = mysql.connector.connect(**BINGO_DB_CONFIG)
        cursor = connection.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bingo_drop_assignments (
                id INT AUTO_INCREMENT PRIMARY KEY,
                submission_id INT NOT NULL,
                tile_id INT NOT NULL
            )
        """)
        # Upsert: remove existing assignment for this submission, then insert
        cursor.execute("DELETE FROM bingo_drop_assignments WHERE submission_id = %s", (data['submission_id'],))
        cursor.execute("INSERT INTO bingo_drop_assignments (submission_id, tile_id) VALUES (%s, %s)",
                       (data['submission_id'], data['tile_id']))
        connection.commit()
        return jsonify({"message": "Drop assigned to tile"}), 200
    except mysql.connector.Error as err:
        if connection: connection.rollback()
        return jsonify({"error": str(err)}), 500
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()


@app.route('/api/bingo/unassign_drop', methods=['POST'])
def unassign_drop():
    """Remove a drop's tile assignment."""
    data = request.get_json()
    connection = None
    try:
        connection = mysql.connector.connect(**BINGO_DB_CONFIG)
        cursor = connection.cursor()
        cursor.execute("DELETE FROM bingo_drop_assignments WHERE submission_id = %s", (data['submission_id'],))
        connection.commit()
        return jsonify({"message": "Assignment removed"}), 200
    except mysql.connector.Error as err:
        if connection: connection.rollback()
        return jsonify({"error": str(err)}), 500
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()


# User recorded in the audit log for bingo-flag removals. The website has no
# authenticated session, but sanity2.auditlogs.userId is a NOT NULL FK to users.userId.
BINGO_AUDIT_USER_ID = 228143014168625153


@app.route('/api/bingo/remove_bingo_flag', methods=['POST'])
def remove_bingo_flag():
    """Remove the bingo flag (bingo = 0) from a submission and log the action."""
    data = request.get_json()
    submission_id = data.get('submission_id')
    if not submission_id:
        return jsonify({"error": "submission_id required"}), 400

    connection = None
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor()
        cursor.execute(
            "UPDATE sanity2.submissions SET bingo = 0 WHERE Id = %s",
            (submission_id,)
        )
        connection.commit()

        # Audit log (best-effort, doesn't fail the removal)
        try:
            action_note = f"Removed bingo flag from submission #{submission_id}"
            audit_query = """
                INSERT INTO sanity2.auditlogs (userId, affectedUsers, actionType, actionNote, actionDate)
                VALUES (%s, %s, %s, %s, NOW())
            """
            cursor.execute(audit_query, (BINGO_AUDIT_USER_ID, None, 10, action_note))
            connection.commit()
        except mysql.connector.Error as audit_err:
            print(f"Warning: Audit log failed: {audit_err}")

        return jsonify({"message": "Bingo flag removed"}), 200
    except mysql.connector.Error as err:
        if connection: connection.rollback()
        return jsonify({"error": str(err)}), 500
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()


# --- DROP NAMES (for Discord autocomplete) ---
@app.route('/api/bingo/drop_names', methods=['GET'])
def get_drop_names():
    connection = None
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT id, name, value FROM sanity2.bingodrops ORDER BY name;")
        return jsonify(cursor.fetchall())
    except mysql.connector.Error as err:
        return jsonify({"error": str(err)}), 500
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()


@app.route('/api/bingo/mass_update_drop_names', methods=['POST'])
def mass_update_drop_names():
    """Receives JSON array and replaces all bingodrops."""
    data = request.get_json()
    if not isinstance(data, list):
        return jsonify({"error": "Expected a JSON array"}), 400
    connection = None
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor()
        cursor.execute("DELETE FROM sanity2.bingodrops")
        for d in data:
            cursor.execute(
                "INSERT INTO sanity2.bingodrops (name, value) VALUES (%s, %s)",
                (d.get('name', ''), d.get('value', 0))
            )
        connection.commit()
        return jsonify({"message": f"{len(data)} drop names updated"}), 200
    except mysql.connector.Error as err:
        if connection: connection.rollback()
        return jsonify({"error": str(err)}), 500
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()


@app.route('/api/bingo/sync_drop_names', methods=['POST'])
def sync_drop_names():
    """Syncs sanity2.bingodrops with all tile items for an event."""
    data = request.get_json()
    event_id = data.get('event_id')
    if not event_id:
        return jsonify({"error": "event_id required"}), 400
    connection = None
    try:
        # Get all unique drop names from tile items for this event
        bingo_conn = mysql.connector.connect(**BINGO_DB_CONFIG)
        bingo_cursor = bingo_conn.cursor(dictionary=True)
        bingo_cursor.execute("SELECT DISTINCT LOWER(dropName) as name FROM bingo_tile_items WHERE eventId = %s", (event_id,))
        names = [row['name'] for row in bingo_cursor.fetchall()]
        bingo_cursor.close()
        bingo_conn.close()

        if not names:
            return jsonify({"message": "No tile items found for this event"}), 200

        # Get point values from bingo_boss_items
        bingo_conn2 = mysql.connector.connect(**BINGO_DB_CONFIG)
        bingo_cursor2 = bingo_conn2.cursor(dictionary=True)
        bingo_cursor2.execute("SELECT LOWER(item) as item, itemPoints FROM bingo_boss_items")
        points_map = {row['item']: row['itemPoints'] for row in bingo_cursor2.fetchall()}
        bingo_cursor2.close()
        bingo_conn2.close()

        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor()
        cursor.execute("DELETE FROM sanity2.bingodrops")
        for name in names:
            value = points_map.get(name, 0)
            cursor.execute("INSERT INTO sanity2.bingodrops (name, value) VALUES (%s, %s)", (name, value))
        connection.commit()
        return jsonify({"message": f"Synced {len(names)} drop names from tile items"}), 200
    except mysql.connector.Error as err:
        if connection: connection.rollback()
        return jsonify({"error": str(err)}), 500
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()


# --- BOSS NAME MAPPING (WiseOldMan metric -> tile boss name) ---
@app.route('/api/bingo/boss_mapping', methods=['GET'])
def get_boss_mapping():
    connection = None
    try:
        connection = mysql.connector.connect(**BINGO_DB_CONFIG)
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bingo_boss_mapping (
                wom_metric VARCHAR(64) PRIMARY KEY,
                boss_name VARCHAR(100) NOT NULL
            )
        """)
        cursor.execute("SELECT wom_metric, boss_name FROM bingo_boss_mapping ORDER BY wom_metric")
        return jsonify(cursor.fetchall())
    except mysql.connector.Error as err:
        return jsonify({"error": str(err)}), 500
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()


@app.route('/api/bingo/save_boss_mapping', methods=['POST'])
def save_boss_mapping():
    """Replaces the whole mapping table. Expects JSON array of {wom_metric, boss_name}."""
    data = request.get_json()
    if not isinstance(data, list):
        return jsonify({"error": "Expected a JSON array"}), 400
    connection = None
    try:
        connection = mysql.connector.connect(**BINGO_DB_CONFIG)
        cursor = connection.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bingo_boss_mapping (
                wom_metric VARCHAR(64) PRIMARY KEY,
                boss_name VARCHAR(100) NOT NULL
            )
        """)
        cursor.execute("DELETE FROM bingo_boss_mapping")
        for row in data:
            if row.get('wom_metric') and row.get('boss_name'):
                cursor.execute(
                    "INSERT INTO bingo_boss_mapping (wom_metric, boss_name) VALUES (%s, %s)",
                    (row['wom_metric'], row['boss_name'])
                )
        connection.commit()
        return jsonify({"message": f"{len(data)} boss mappings saved"}), 200
    except mysql.connector.Error as err:
        if connection: connection.rollback()
        return jsonify({"error": str(err)}), 500
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()


# Add other endpoints like /api/bingo/overview and /api/bingo/ehb here
# These can be complex and may require multiple queries similar to the /teams endpoint.
# For now, they will return mock data in the frontend.


@app.route('/')
def index():
    """
    Serves a simple message indicating the backend is running.
    The actual frontend will be served by your web server or opened directly.
    """
    return render_template("index.html")


"""if __name__ == '__main__':
    app.run(debug=True)"""


# ============================================================================
# MONEY GRAB EVENTS
# ============================================================================
# Weekend "money grab" events: a couple of bosses + a handful of specific drops.
# Each drop has a point value and a G.E. (money) value; teams submit drops and
# the leaderboard is ranked by total money made. Backed by the `sanitymoneygrab`
# schema; approved Discord submissions (sanity2.submissions) are linked to
# event drops on the setup page.

WIKI_PRICES_BASE = "https://prices.runescape.wiki/api/v1/osrs"
WIKI_MAPPING_TTL = 60 * 60      # 1 hour
WIKI_LATEST_TTL = 5 * 60        # 5 minutes

_wiki_mapping_cache = {"ts": 0, "data": None, "index": None}
_wiki_latest_cache = {"ts": 0, "data": None}


def _moneygrab_conn():
    return mysql.connector.connect(**MONEYGRAB_DB_CONFIG)


def _norm_item_name(s):
    return ' '.join((s or '').lower().replace('_', ' ').split())


def _fetch_wiki_mapping():
    """Fetch + cache the OSRS wiki item id -> name mapping."""
    now = time.time()
    if _wiki_mapping_cache["data"] is not None and (now - _wiki_mapping_cache["ts"]) < WIKI_MAPPING_TTL:
        return _wiki_mapping_cache
    try:
        resp = requests.get(
            f"{WIKI_PRICES_BASE}/mapping",
            headers={'User-Agent': 'Mozilla/5.0 (compatible; SanityMoneygrab/1.0)'},
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        index = {}
        for entry in data:
            n = _norm_item_name(entry.get('name'))
            if n:
                index.setdefault(n, entry)
        _wiki_mapping_cache["data"] = data
        _wiki_mapping_cache["index"] = index
        _wiki_mapping_cache["ts"] = now
    except Exception as err:
        print(f"[moneygrab] wiki mapping fetch failed: {err}")
    return _wiki_mapping_cache


def _fetch_wiki_latest():
    """Fetch + cache the OSRS wiki latest prices."""
    now = time.time()
    if _wiki_latest_cache["data"] is not None and (now - _wiki_latest_cache["ts"]) < WIKI_LATEST_TTL:
        return _wiki_latest_cache["data"]
    try:
        resp = requests.get(
            f"{WIKI_PRICES_BASE}/latest",
            headers={'User-Agent': 'Mozilla/5.0 (compatible; SanityMoneygrab/1.0)'},
            timeout=30,
        )
        resp.raise_for_status()
        _wiki_latest_cache["data"] = resp.json()
        _wiki_latest_cache["ts"] = now
    except Exception as err:
        print(f"[moneygrab] wiki latest fetch failed: {err}")
    return _wiki_latest_cache["data"]


def _wiki_icon_url(icon):
    """Build a stable image URL from a wiki icon filename (via Special:FilePath)."""
    if not icon:
        return None
    from urllib.parse import quote
    return "https://oldschool.runescape.wiki/w/Special:FilePath/" + quote(icon.replace(' ', '_'), safe='')


def _lookup_wiki_item(item_name):
    """Return (wiki_item_id, resolved_name, icon) best match, or (None, None, None)."""
    cache = _fetch_wiki_mapping()
    index = cache.get("index") or {}
    q = _norm_item_name(item_name)
    if not q:
        return None, None, None

    if q in index:
        e = index[q]
        return e.get('id'), e.get('name'), e.get('icon')

    # Fallback: substring match, preferring the shortest item name.
    best = None
    for entry in (cache.get("data") or []):
        n = _norm_item_name(entry.get('name'))
        if n and q in n:
            if best is None or len(n) < len(_norm_item_name(best.get('name'))):
                best = entry
    if best:
        return best.get('id'), best.get('name'), best.get('icon')
    return None, None, None


def _lookup_ge_price(item_name):
    """
    Look up a drop's G.E. price and image from the OSRS wiki. Returns a dict
    with wiki_item_id, name, image_url, ge_value, ge_low, ge_high, or None
    when no wiki match.
    """
    wiki_item_id, resolved_name, icon = _lookup_wiki_item(item_name)
    if not wiki_item_id:
        return None

    result = {
        "wiki_item_id": wiki_item_id,
        "name": resolved_name,
        "image_url": _wiki_icon_url(icon),
        "ge_value": None,
        "ge_low": None,
        "ge_high": None,
    }
    latest = _fetch_wiki_latest()
    data = (latest or {}).get("data", {})
    price = data.get(str(wiki_item_id))
    if price:
        high = price.get("high")
        low = price.get("low")
        result["ge_low"] = low
        result["ge_high"] = high
        # "GE value" defaults to the high (instant-buy) price.
        result["ge_value"] = high if high is not None else low
    return result


def _ensure_drop_image_column(conn):
    """Add moneygrab_event_drops.image_url on installs created before it existed."""
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT COUNT(*) FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA = 'sanitymoneygrab'
              AND TABLE_NAME = 'moneygrab_event_drops'
              AND COLUMN_NAME = 'image_url'
        """)
        if cur.fetchone()[0] == 0:
            cur.execute("ALTER TABLE moneygrab_event_drops ADD COLUMN image_url VARCHAR(500) DEFAULT NULL")
        conn.commit()
        cur.close()
    except mysql.connector.Error:
        pass


# --- Events ---

@app.route('/api/moneygrab/events', methods=['GET'])
def get_moneygrab_events():
    conn = None
    try:
        conn = _moneygrab_conn()
        cur = conn.cursor(dictionary=True)
        cur.execute(
            "SELECT id, name, start_date, end_date, is_active, wom_id "
            "FROM moneygrab_events ORDER BY start_date DESC"
        )
        return jsonify(cur.fetchall())
    except mysql.connector.Error as err:
        return jsonify({"error": str(err)}), 500
    finally:
        if conn and conn.is_connected():
            conn.close()


@app.route('/api/moneygrab/create_event', methods=['POST'])
def create_moneygrab_event():
    data = request.get_json()
    if not data.get('name'):
        return jsonify({"error": "name required"}), 400
    conn = None
    try:
        conn = _moneygrab_conn()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO moneygrab_events (name, start_date, end_date, is_active) VALUES (%s, %s, %s, 0)",
            (data.get('name'), data.get('start_date'), data.get('end_date')),
        )
        conn.commit()
        return jsonify({"message": "Event created successfully", "id": cur.lastrowid}), 201
    except mysql.connector.Error as err:
        if conn:
            conn.rollback()
        return jsonify({"error": str(err)}), 500
    finally:
        if conn and conn.is_connected():
            conn.close()


@app.route('/api/moneygrab/update_event', methods=['POST'])
def update_moneygrab_event():
    data = request.get_json()
    event_id = data.get('event_id')
    if not event_id:
        return jsonify({"error": "event_id required"}), 400

    sets = []
    params = []
    if 'name' in data and data['name']:
        sets.append("name = %s")
        params.append(data['name'])
    if 'start_date' in data and data['start_date']:
        sets.append("start_date = %s")
        params.append(data['start_date'])
    if 'end_date' in data and data['end_date']:
        sets.append("end_date = %s")
        params.append(data['end_date'])
    if 'is_active' in data:
        sets.append("is_active = %s")
        params.append(1 if data['is_active'] else 0)
    if 'wom_id' in data:
        sets.append("wom_id = %s")
        params.append(data['wom_id'] or None)

    if not sets:
        return jsonify({"error": "Nothing to update"}), 400

    params.append(event_id)
    conn = None
    try:
        conn = _moneygrab_conn()
        cur = conn.cursor()
        cur.execute(f"UPDATE moneygrab_events SET {', '.join(sets)} WHERE id = %s", tuple(params))
        conn.commit()
        return jsonify({"message": "Event updated"}), 200
    except mysql.connector.Error as err:
        if conn:
            conn.rollback()
        return jsonify({"error": str(err)}), 500
    finally:
        if conn and conn.is_connected():
            conn.close()


# --- Bosses ---

@app.route('/api/moneygrab/bosses', methods=['GET'])
def get_moneygrab_bosses():
    event_id = request.args.get('event_id', type=int)
    conn = None
    try:
        conn = _moneygrab_conn()
        cur = conn.cursor(dictionary=True)
        if event_id:
            cur.execute(
                "SELECT id, event_id, boss_name, wom_metric, sort_order "
                "FROM moneygrab_event_bosses WHERE event_id = %s ORDER BY sort_order, id",
                (event_id,),
            )
        else:
            cur.execute(
                "SELECT id, event_id, boss_name, wom_metric, sort_order "
                "FROM moneygrab_event_bosses ORDER BY event_id, sort_order, id"
            )
        return jsonify(cur.fetchall())
    except mysql.connector.Error as err:
        return jsonify({"error": str(err)}), 500
    finally:
        if conn and conn.is_connected():
            conn.close()


@app.route('/api/moneygrab/update_bosses', methods=['POST'])
def update_moneygrab_bosses():
    data = request.get_json()
    event_id = data.get('event_id')
    bosses = data.get('bosses') or []
    if not event_id:
        return jsonify({"error": "event_id required"}), 400

    conn = None
    try:
        conn = _moneygrab_conn()
        cur = conn.cursor()
        cur.execute("DELETE FROM moneygrab_event_bosses WHERE event_id = %s", (event_id,))
        saved = 0
        for i, b in enumerate(bosses):
            name = (b.get('boss_name') or '').strip()
            if not name:
                continue
            cur.execute(
                "INSERT INTO moneygrab_event_bosses (event_id, boss_name, wom_metric, sort_order) "
                "VALUES (%s, %s, %s, %s)",
                (event_id, name, b.get('wom_metric') or None, i),
            )
            saved += 1
        conn.commit()
        return jsonify({"message": f"{saved} boss(es) saved"}), 200
    except mysql.connector.Error as err:
        if conn:
            conn.rollback()
        return jsonify({"error": str(err)}), 500
    finally:
        if conn and conn.is_connected():
            conn.close()


# --- Drops ---

@app.route('/api/moneygrab/drops', methods=['GET'])
def get_moneygrab_drops():
    event_id = request.args.get('event_id', type=int)
    conn = None
    try:
        conn = _moneygrab_conn()
        _ensure_drop_image_column(conn)
        cur = conn.cursor(dictionary=True)
        if event_id:
            cur.execute(
                "SELECT id, event_id, boss_name, item_name, point_value, ge_value, ge_low, ge_high, "
                "wiki_item_id, ge_updated_at, image_url FROM moneygrab_event_drops WHERE event_id = %s "
                "ORDER BY boss_name, item_name",
                (event_id,),
            )
        else:
            cur.execute(
                "SELECT id, event_id, boss_name, item_name, point_value, ge_value, ge_low, ge_high, "
                "wiki_item_id, ge_updated_at, image_url FROM moneygrab_event_drops ORDER BY event_id, boss_name, item_name"
            )
        return jsonify(cur.fetchall())
    except mysql.connector.Error as err:
        return jsonify({"error": str(err)}), 500
    finally:
        if conn and conn.is_connected():
            conn.close()


@app.route('/api/moneygrab/update_drops', methods=['POST'])
def update_moneygrab_drops():
    """Upsert the drop list for an event (preserves fetched GE values)."""
    data = request.get_json()
    event_id = data.get('event_id')
    drops = data.get('drops') or []
    if not event_id:
        return jsonify({"error": "event_id required"}), 400

    conn = None
    try:
        conn = _moneygrab_conn()
        cur = conn.cursor(dictionary=True)

        cur.execute(
            "SELECT id, boss_name, item_name FROM moneygrab_event_drops WHERE event_id = %s",
            (event_id,),
        )
        existing = {(r['boss_name'], r['item_name']): r['id'] for r in cur.fetchall()}

        seen = set()
        for d in drops:
            boss = (d.get('boss_name') or '').strip()
            item = (d.get('item_name') or '').strip()
            if not boss or not item:
                continue
            key = (boss, item)
            seen.add(key)
            point_value = int(d.get('point_value') or 0)
            if key in existing:
                cur.execute(
                    "UPDATE moneygrab_event_drops SET point_value = %s WHERE id = %s",
                    (point_value, existing[key]),
                )
            else:
                cur.execute(
                    "INSERT INTO moneygrab_event_drops (event_id, boss_name, item_name, point_value) "
                    "VALUES (%s, %s, %s, %s)",
                    (event_id, boss, item, point_value),
                )

        # Remove drops (and their submission links) that are no longer present.
        for key, drop_id in existing.items():
            if key not in seen:
                cur.execute("DELETE FROM moneygrab_submission_links WHERE drop_id = %s", (drop_id,))
                cur.execute("DELETE FROM moneygrab_event_drops WHERE id = %s", (drop_id,))

        conn.commit()
        return jsonify({"message": f"{len(seen)} drop(s) saved"}), 200
    except mysql.connector.Error as err:
        if conn:
            conn.rollback()
        return jsonify({"error": str(err)}), 500
    finally:
        if conn and conn.is_connected():
            conn.close()


@app.route('/api/moneygrab/lookup_ge', methods=['POST'])
def lookup_moneygrab_ge():
    data = request.get_json()
    item_name = data.get('item_name')
    if not item_name:
        return jsonify({"error": "item_name required"}), 400
    result = _lookup_ge_price(item_name)
    if not result:
        return jsonify({"error": "No matching item found on the OSRS wiki", "item_name": item_name}), 404
    return jsonify(result)


@app.route('/api/moneygrab/refresh_ge', methods=['POST'])
def refresh_moneygrab_ge():
    data = request.get_json()
    event_id = data.get('event_id')
    if not event_id:
        return jsonify({"error": "event_id required"}), 400

    conn = None
    try:
        conn = _moneygrab_conn()
        _ensure_drop_image_column(conn)
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT id, item_name FROM moneygrab_event_drops WHERE event_id = %s", (event_id,))
        rows = cur.fetchall()

        updated = 0
        failed = []
        for r in rows:
            price = _lookup_ge_price(r['item_name'])
            if not price:
                failed.append(r['item_name'])
                continue
            cur.execute(
                "UPDATE moneygrab_event_drops SET ge_value = %s, ge_low = %s, ge_high = %s, "
                "wiki_item_id = %s, ge_updated_at = %s, image_url = %s WHERE id = %s",
                (
                    price.get('ge_value'),
                    price.get('ge_low'),
                    price.get('ge_high'),
                    price.get('wiki_item_id'),
                    datetime.datetime.now(),
                    price.get('image_url'),
                    r['id'],
                ),
            )
            updated += 1

        conn.commit()
        return jsonify({"message": f"Updated GE values for {updated} drop(s)", "updated": updated, "failed": failed})
    except mysql.connector.Error as err:
        if conn:
            conn.rollback()
        return jsonify({"error": str(err)}), 500
    finally:
        if conn and conn.is_connected():
            conn.close()


# --- Teams ---

@app.route('/api/moneygrab/teams', methods=['GET'])
def get_moneygrab_teams():
    event_id = request.args.get('event_id', type=int)
    conn = None
    try:
        conn = _moneygrab_conn()
        cur = conn.cursor(dictionary=True)
        base = """
            SELECT mt.id, mt.name, mt.captain_userid, u_cap.displayName AS captain_name,
                   mt.cocaptain_userid, u_cocap.displayName AS cocaptain_name,
                   mt.event_id, mt.image_url
            FROM moneygrab_teams mt
            LEFT JOIN sanity2.users u_cap ON u_cap.userId = mt.captain_userid
            LEFT JOIN sanity2.users u_cocap ON u_cocap.userId = mt.cocaptain_userid
        """
        if event_id:
            cur.execute(base + " WHERE mt.event_id = %s", (event_id,))
        else:
            cur.execute(base)
        return jsonify(cur.fetchall())
    except mysql.connector.Error as err:
        return jsonify({"error": str(err)}), 500
    finally:
        if conn and conn.is_connected():
            conn.close()


@app.route('/api/moneygrab/add_team', methods=['POST'])
def add_moneygrab_team():
    data = request.get_json()
    event_id = data.get('event_id')
    name = data.get('name')
    if not event_id or not name:
        return jsonify({"error": "event_id and name required"}), 400

    # Discord user IDs are 18-digit snowflakes; parse them in Python (exact),
    # never via JavaScript Number() which loses precision.
    def to_id(v):
        if v is None or v == '':
            return None
        return int(v)

    captain = to_id(data.get('captain_userid'))
    cocaptain = to_id(data.get('cocaptain_userid'))

    conn = None
    try:
        conn = _moneygrab_conn()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO moneygrab_teams (event_id, name, captain_userid, cocaptain_userid, image_url) "
            "VALUES (%s, %s, %s, %s, %s)",
            (event_id, name, captain, cocaptain, data.get('image_url')),
        )
        team_id = cur.lastrowid

        # Add captain and co-captain as team members.
        if captain is not None:
            cur.execute(
                "INSERT INTO moneygrab_team_members (team_id, user_id, event_id) VALUES (%s, %s, %s)",
                (team_id, captain, event_id),
            )
        if cocaptain is not None:
            cur.execute(
                "INSERT INTO moneygrab_team_members (team_id, user_id, event_id) VALUES (%s, %s, %s)",
                (team_id, cocaptain, event_id),
            )

        conn.commit()
        return jsonify({"message": "Team added", "id": team_id}), 201
    except mysql.connector.Error as err:
        if conn:
            conn.rollback()
        return jsonify({"error": str(err)}), 500
    finally:
        if conn and conn.is_connected():
            conn.close()


@app.route('/api/moneygrab/update_team', methods=['POST'])
def update_moneygrab_team():
    data = request.get_json()
    team_id = data.get('team_id')
    if not team_id:
        return jsonify({"error": "team_id required"}), 400

    sets = []
    params = []
    for key, col in [('name', 'name'), ('captain_userid', 'captain_userid'),
                     ('cocaptain_userid', 'cocaptain_userid'), ('image_url', 'image_url')]:
        if key in data:
            sets.append(f"{col} = %s")
            params.append(data[key])

    if not sets:
        return jsonify({"error": "Nothing to update"}), 400

    params.append(team_id)
    conn = None
    try:
        conn = _moneygrab_conn()
        cur = conn.cursor()
        cur.execute(f"UPDATE moneygrab_teams SET {', '.join(sets)} WHERE id = %s", tuple(params))
        conn.commit()
        return jsonify({"message": "Team updated"}), 200
    except mysql.connector.Error as err:
        if conn:
            conn.rollback()
        return jsonify({"error": str(err)}), 500
    finally:
        if conn and conn.is_connected():
            conn.close()


@app.route('/api/moneygrab/delete_team', methods=['POST'])
def delete_moneygrab_team():
    data = request.get_json()
    team_id = data.get('team_id')
    if not team_id:
        return jsonify({"error": "team_id required"}), 400
    conn = None
    try:
        conn = _moneygrab_conn()
        cur = conn.cursor()
        cur.execute("DELETE FROM moneygrab_team_members WHERE team_id = %s", (team_id,))
        cur.execute("DELETE FROM moneygrab_teams WHERE id = %s", (team_id,))
        conn.commit()
        return jsonify({"message": "Team deleted"}), 200
    except mysql.connector.Error as err:
        if conn:
            conn.rollback()
        return jsonify({"error": str(err)}), 500
    finally:
        if conn and conn.is_connected():
            conn.close()


@app.route('/api/moneygrab/import_teams', methods=['POST'])
def import_moneygrab_teams():
    data = request.get_json()
    event_id = data.get('event_id')
    lines = (data.get('lines') or '').strip().splitlines()
    if not event_id:
        return jsonify({"error": "event_id required"}), 400

    # Build displayName / RSN -> userId lookups from sanity2.users.
    conn = mysql.connector.connect(**DB_CONFIG)
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT userId, displayName, mainRSN, altRSN FROM sanity2.users")
    users = cur.fetchall()
    cur.close()
    conn.close()

    by_display = {}
    by_rsn = {}
    for u in users:
        if u.get('displayName'):
            by_display[u['displayName'].lower()] = u['userId']
        for rsn in (u.get('mainRSN'), u.get('altRSN')):
            if rsn:
                by_rsn[rsn.lower()] = u['userId']

    def resolve_user(name):
        n = (name or '').strip()
        if not n:
            return None
        return by_display.get(n.lower()) or by_rsn.get(n.lower())

    created = 0
    failed = []
    mg = _moneygrab_conn()
    mgcur = mg.cursor()
    try:
        for line in lines:
            parts = [p.strip() for p in line.split(',')]
            if not parts or not parts[0]:
                continue
            team_name = parts[0]
            member_entries = []
            for i in range(1, len(parts), 2):
                name = parts[i]
                rsn = parts[i + 1] if i + 1 < len(parts) else ''
                member_entries.append((name, rsn))

            resolved = []
            for name, rsn in member_entries:
                uid = resolve_user(name) or resolve_user(rsn)
                if uid:
                    resolved.append((uid, rsn))
                else:
                    failed.append(name or rsn)

            if not resolved:
                failed.append(team_name)
                continue

            captain = resolved[0][0]
            cocaptain = resolved[1][0] if len(resolved) > 1 else None
            mgcur.execute(
                "INSERT INTO moneygrab_teams (event_id, name, captain_userid, cocaptain_userid) "
                "VALUES (%s, %s, %s, %s)",
                (event_id, team_name, captain, cocaptain),
            )
            team_id = mgcur.lastrowid
            for uid, rsn in resolved:
                mgcur.execute(
                    "INSERT INTO moneygrab_team_members (team_id, user_id, event_id, rsn) "
                    "VALUES (%s, %s, %s, %s)",
                    (team_id, uid, event_id, rsn or None),
                )
            created += 1

        mg.commit()
    except mysql.connector.Error as err:
        mg.rollback()
        return jsonify({"error": str(err)}), 500
    finally:
        mgcur.close()
        mg.close()

    msg = f"Imported {created} team(s)"
    if failed:
        msg += f", failed: {', '.join(failed)}"
    return jsonify({"message": msg, "failed": failed})


@app.route('/api/moneygrab/teammembers', methods=['GET'])
def get_moneygrab_team_members():
    event_id = request.args.get('event_id', type=int)
    conn = None
    try:
        conn = _moneygrab_conn()
        cur = conn.cursor(dictionary=True)
        base = """
            SELECT tm.team_id, CAST(tm.user_id AS CHAR) AS user_id, tm.rsn,
                   u.displayName, u.mainRSN, u.altRSN
            FROM moneygrab_team_members tm
            LEFT JOIN sanity2.users u ON u.userId = tm.user_id
        """
        if event_id:
            cur.execute(base + " WHERE tm.event_id = %s", (event_id,))
        else:
            cur.execute(base)
        return jsonify(cur.fetchall())
    except mysql.connector.Error as err:
        return jsonify({"error": str(err)}), 500
    finally:
        if conn and conn.is_connected():
            conn.close()


@app.route('/api/moneygrab/add_team_member', methods=['POST'])
def add_moneygrab_team_member():
    data = request.get_json()
    team_id = data.get('team_id')
    user_id = data.get('user_id')
    if not team_id or not user_id:
        return jsonify({"error": "team_id and user_id required"}), 400

    team_id = int(team_id)
    user_id = int(user_id)

    conn = None
    try:
        conn = _moneygrab_conn()
        cur = conn.cursor()
        # Resolve event_id from the team.
        cur.execute("SELECT event_id FROM moneygrab_teams WHERE id = %s", (team_id,))
        row = cur.fetchone()
        if not row:
            return jsonify({"error": "Team not found"}), 404
        event_id = row[0]
        cur.execute(
            "INSERT INTO moneygrab_team_members (team_id, user_id, event_id, rsn) VALUES (%s, %s, %s, %s) "
            "ON DUPLICATE KEY UPDATE rsn = VALUES(rsn)",
            (team_id, user_id, event_id, data.get('rsn')),
        )
        conn.commit()
        return jsonify({"message": "Member added"}), 200
    except mysql.connector.Error as err:
        if conn:
            conn.rollback()
        return jsonify({"error": str(err)}), 500
    finally:
        if conn and conn.is_connected():
            conn.close()


@app.route('/api/moneygrab/remove_team_member', methods=['POST'])
def remove_moneygrab_team_member():
    data = request.get_json()
    team_id = data.get('team_id')
    user_id = data.get('user_id')
    if not team_id or not user_id:
        return jsonify({"error": "team_id and user_id required"}), 400

    team_id = int(team_id)
    user_id = int(user_id)

    conn = None
    try:
        conn = _moneygrab_conn()
        cur = conn.cursor()
        cur.execute("DELETE FROM moneygrab_team_members WHERE team_id = %s AND user_id = %s", (team_id, user_id))
        conn.commit()
        return jsonify({"message": "Member removed"}), 200
    except mysql.connector.Error as err:
        if conn:
            conn.rollback()
        return jsonify({"error": str(err)}), 500
    finally:
        if conn and conn.is_connected():
            conn.close()


@app.route('/api/moneygrab/update_member_rsn', methods=['POST'])
def update_moneygrab_member_rsn():
    data = request.get_json()
    team_id = data.get('team_id')
    user_id = data.get('user_id')
    if not team_id or not user_id:
        return jsonify({"error": "team_id and user_id required"}), 400

    team_id = int(team_id)
    user_id = int(user_id)

    conn = None
    try:
        conn = _moneygrab_conn()
        cur = conn.cursor()
        cur.execute(
            "UPDATE moneygrab_team_members SET rsn = %s WHERE team_id = %s AND user_id = %s",
            (data.get('rsn'), team_id, user_id),
        )
        conn.commit()
        return jsonify({"message": "RSN updated"}), 200
    except mysql.connector.Error as err:
        if conn:
            conn.rollback()
        return jsonify({"error": str(err)}), 500
    finally:
        if conn and conn.is_connected():
            conn.close()


@app.route('/api/moneygrab/team_images/<path:filename>')
def serve_moneygrab_team_image(filename):
    """Serve an uploaded team logo from disk."""
    return send_from_directory(TEAM_IMAGE_DIR, filename)


@app.route('/api/moneygrab/upload_team_image', methods=['POST'])
def upload_moneygrab_team_image():
    """Upload a team logo image, store it on disk, and save its URL to the team."""
    if request.content_length and request.content_length > MAX_UPLOAD_SIZE:
        return jsonify({"error": "File too large (max 5 MB)"}), 413

    team_id_raw = request.form.get('team_id')
    file = request.files.get('file')
    if not team_id_raw or file is None or file.filename == '':
        return jsonify({"error": "team_id and file are required"}), 400

    try:
        team_id = int(team_id_raw)
    except (TypeError, ValueError):
        return jsonify({"error": "team_id must be an integer"}), 400

    ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        return jsonify({"error": "Unsupported file type"}), 400

    os.makedirs(TEAM_IMAGE_DIR, exist_ok=True)
    filename = f"mg_team_{team_id}_{int(time.time())}.{ext}"
    file_path = os.path.join(TEAM_IMAGE_DIR, filename)

    conn = None
    try:
        conn = _moneygrab_conn()
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT image_url FROM moneygrab_teams WHERE id = %s", (team_id,))
        row = cur.fetchone()
        if not row:
            return jsonify({"error": "Team not found"}), 404
        old_url = row.get('image_url')

        file.save(file_path)

        image_url = f"/api/moneygrab/team_images/{filename}"
        cur.execute("UPDATE moneygrab_teams SET image_url = %s WHERE id = %s", (image_url, team_id))
        conn.commit()

        # Clean up the previous uploaded logo (only files this app manages).
        if old_url and old_url.startswith('/api/moneygrab/team_images/'):
            old_path = os.path.join(TEAM_IMAGE_DIR, os.path.basename(old_url))
            if os.path.exists(old_path) and old_path != file_path:
                try:
                    os.remove(old_path)
                except OSError:
                    pass

        return jsonify({"message": "Team image uploaded", "image_url": image_url}), 200
    except mysql.connector.Error as err:
        if conn:
            conn.rollback()
        return jsonify({"error": str(err)}), 500
    except OSError as err:
        return jsonify({"error": f"Failed to save file: {err}"}), 500
    finally:
        if conn and conn.is_connected():
            conn.close()


# --- Submissions & linking ---

@app.route('/api/moneygrab/submissions', methods=['GET'])
def get_moneygrab_submissions():
    """Approved Discord submissions (sanity2) available for linking, with link state."""
    event_id = request.args.get('event_id', type=int)

    conn = mysql.connector.connect(**DB_CONFIG)
    cur = conn.cursor(dictionary=True)
    try:
        date_filter = ""
        params = []
        if event_id:
            mg = _moneygrab_conn()
            mgcur = mg.cursor(dictionary=True)
            mgcur.execute("SELECT start_date, end_date FROM moneygrab_events WHERE id = %s", (event_id,))
            ev = mgcur.fetchone()
            mgcur.close()
            mg.close()
            if ev and ev.get('start_date') and ev.get('end_date'):
                date_filter = " AND s.reviewedDate >= DATE_SUB(%s, INTERVAL 12 HOUR) AND s.reviewedDate <= DATE_ADD(%s, INTERVAL 12 HOUR)"
                params = [ev['start_date'], ev['end_date']]

        query = f"""
            SELECT s.Id, s.userId, u.displayName AS submitter, s.notes, s.value, s.imageUrl,
                   s.reviewedDate, s.participants, s2.name AS status_name
            FROM sanity2.submissions s
            LEFT JOIN sanity2.users u ON u.userId = s.userId
            LEFT JOIN sanity2.submissionstatus s2 ON s2.id = s.status
            WHERE s.status = 2{date_filter}
            ORDER BY s.Id DESC
            LIMIT 500
        """
        cur.execute(query, params)
        submissions = cur.fetchall()
    finally:
        cur.close()
        conn.close()

    mg = _moneygrab_conn()
    mgcur = mg.cursor(dictionary=True)
    try:
        if event_id:
            mgcur.execute(
                "SELECT submission_id, drop_id, id AS link_id FROM moneygrab_submission_links WHERE event_id = %s",
                (event_id,),
            )
        else:
            mgcur.execute("SELECT submission_id, drop_id, id AS link_id FROM moneygrab_submission_links")
        links = {r['submission_id']: r for r in mgcur.fetchall()}
    finally:
        mgcur.close()
        mg.close()

    for s in submissions:
        lk = links.get(s['Id'])
        s['linked'] = bool(lk)
        s['link_id'] = lk['link_id'] if lk else None
        s['drop_id'] = lk['drop_id'] if lk else None
    return jsonify(submissions)


@app.route('/api/moneygrab/link_submission', methods=['POST'])
def link_moneygrab_submission():
    data = request.get_json()
    event_id = data.get('event_id')
    submission_id = data.get('submission_id')
    drop_id = data.get('drop_id')
    if not all([event_id, submission_id, drop_id]):
        return jsonify({"error": "event_id, submission_id and drop_id required"}), 400

    conn = None
    try:
        conn = _moneygrab_conn()
        cur = conn.cursor()
        cur.execute("SELECT id FROM moneygrab_event_drops WHERE id = %s AND event_id = %s", (drop_id, event_id))
        if not cur.fetchone():
            return jsonify({"error": "Drop not found for this event"}), 404
        cur.execute(
            "INSERT INTO moneygrab_submission_links (event_id, submission_id, drop_id) VALUES (%s, %s, %s) "
            "ON DUPLICATE KEY UPDATE drop_id = %s, event_id = %s",
            (event_id, submission_id, drop_id, drop_id, event_id),
        )
        conn.commit()
        return jsonify({"message": "Submission linked"}), 200
    except mysql.connector.Error as err:
        if conn:
            conn.rollback()
        return jsonify({"error": str(err)}), 500
    finally:
        if conn and conn.is_connected():
            conn.close()


@app.route('/api/moneygrab/unlink_submission', methods=['POST'])
def unlink_moneygrab_submission():
    data = request.get_json()
    submission_id = data.get('submission_id')
    if not submission_id:
        return jsonify({"error": "submission_id required"}), 400
    conn = None
    try:
        conn = _moneygrab_conn()
        cur = conn.cursor()
        cur.execute("DELETE FROM moneygrab_submission_links WHERE submission_id = %s", (submission_id,))
        conn.commit()
        return jsonify({"message": "Submission unlinked"}), 200
    except mysql.connector.Error as err:
        if conn:
            conn.rollback()
        return jsonify({"error": str(err)}), 500
    finally:
        if conn and conn.is_connected():
            conn.close()


@app.route('/api/moneygrab/linked', methods=['GET'])
def get_moneygrab_linked():
    """Resolved linked drops (event drop + submission + team)."""
    event_id = request.args.get('event_id', type=int)

    mg = _moneygrab_conn()
    _ensure_drop_image_column(mg)
    mgcur = mg.cursor(dictionary=True)
    try:
        if event_id:
            mgcur.execute(
                "SELECT l.id AS link_id, l.submission_id, l.drop_id, l.event_id, "
                "d.boss_name, d.item_name, d.point_value, d.ge_value, d.ge_low, d.ge_high, d.image_url "
                "FROM moneygrab_submission_links l "
                "JOIN moneygrab_event_drops d ON d.id = l.drop_id "
                "WHERE l.event_id = %s ORDER BY l.id DESC",
                (event_id,),
            )
        else:
            mgcur.execute(
                "SELECT l.id AS link_id, l.submission_id, l.drop_id, l.event_id, "
                "d.boss_name, d.item_name, d.point_value, d.ge_value, d.ge_low, d.ge_high, d.image_url "
                "FROM moneygrab_submission_links l "
                "JOIN moneygrab_event_drops d ON d.id = l.drop_id ORDER BY l.id DESC"
            )
        links = mgcur.fetchall()
    finally:
        mgcur.close()
        mg.close()

    if not links:
        return jsonify([])

    sub_ids = [l['submission_id'] for l in links]
    placeholders = ','.join(['%s'] * len(sub_ids))

    conn = mysql.connector.connect(**DB_CONFIG)
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute(f"""
            SELECT s.Id, s.userId, s.participants, s.value, s.imageUrl, s.reviewedDate,
                   u.displayName AS submitter
            FROM sanity2.submissions s
            LEFT JOIN sanity2.users u ON u.userId = s.userId
            WHERE s.Id IN ({placeholders})
        """, tuple(sub_ids))
        subs = {r['Id']: r for r in cur.fetchall()}
    finally:
        cur.close()
        conn.close()

    mg2 = _moneygrab_conn()
    mgcur2 = mg2.cursor(dictionary=True)
    try:
        base = """
            SELECT tm.user_id, tm.team_id, t.name AS team_name, t.image_url
            FROM moneygrab_team_members tm
            JOIN moneygrab_teams t ON t.id = tm.team_id
        """
        if event_id:
            mgcur2.execute(base + " WHERE tm.event_id = %s", (event_id,))
        else:
            mgcur2.execute(base)
        user_to_team = {r['user_id']: r for r in mgcur2.fetchall()}
    finally:
        mgcur2.close()
        mg2.close()

    result = []
    for l in links:
        s = subs.get(l['submission_id'])
        team = user_to_team.get(s['userId']) if s else None
        result.append({
            "link_id": l['link_id'],
            "submission_id": l['submission_id'],
            "drop_id": l['drop_id'],
            "event_id": l['event_id'],
            "boss_name": l['boss_name'],
            "item_name": l['item_name'],
            "point_value": l['point_value'],
            "ge_value": l['ge_value'],
            "ge_low": l['ge_low'],
            "ge_high": l['ge_high'],
            "image_url": l['image_url'],
            "submitter": s['submitter'] if s else None,
            "member_names": (s['participants'] or '') if s else None,
            "value": s['value'] if s else None,
            "imageUrl": s['imageUrl'] if s else None,
            "reviewedDate": s['reviewedDate'] if s else None,
            "team_id": team['team_id'] if team else None,
            "team_name": team['team_name'] if team else None,
            "team_image_url": team['image_url'] if team else None,
        })
    return jsonify(result)


# --- Boss images & EHB ---

@app.route('/api/moneygrab/boss_images', methods=['GET'])
def get_moneygrab_boss_images():
    conn = None
    try:
        conn = _moneygrab_conn()
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT id, boss_name, image_url FROM moneygrab_boss_images ORDER BY boss_name")
        return jsonify(cur.fetchall())
    except mysql.connector.Error as err:
        return jsonify({"error": str(err)}), 500
    finally:
        if conn and conn.is_connected():
            conn.close()


@app.route('/api/moneygrab/update_boss_image', methods=['POST'])
def update_moneygrab_boss_image():
    data = request.get_json()
    boss_name = (data.get('boss_name') or '').strip()
    if not boss_name:
        return jsonify({"error": "boss_name required"}), 400
    conn = None
    try:
        conn = _moneygrab_conn()
        cur = conn.cursor()
        if data.get('id'):
            cur.execute(
                "UPDATE moneygrab_boss_images SET boss_name = %s, image_url = %s WHERE id = %s",
                (boss_name, data.get('image_url'), data.get('id')),
            )
        else:
            cur.execute(
                "INSERT INTO moneygrab_boss_images (boss_name, image_url) VALUES (%s, %s) "
                "ON DUPLICATE KEY UPDATE image_url = VALUES(image_url)",
                (boss_name, data.get('image_url')),
            )
        conn.commit()
        return jsonify({"message": "Boss image saved"}), 200
    except mysql.connector.Error as err:
        if conn:
            conn.rollback()
        return jsonify({"error": str(err)}), 500
    finally:
        if conn and conn.is_connected():
            conn.close()


@app.route('/api/moneygrab/delete_boss_image', methods=['POST'])
def delete_moneygrab_boss_image():
    data = request.get_json()
    if not data.get('id'):
        return jsonify({"error": "id required"}), 400
    conn = None
    try:
        conn = _moneygrab_conn()
        cur = conn.cursor()
        cur.execute("DELETE FROM moneygrab_boss_images WHERE id = %s", (data.get('id'),))
        conn.commit()
        return jsonify({"message": "Boss image deleted"}), 200
    except mysql.connector.Error as err:
        if conn:
            conn.rollback()
        return jsonify({"error": str(err)}), 500
    finally:
        if conn and conn.is_connected():
            conn.close()


@app.route('/api/moneygrab/boss_ehb', methods=['GET'])
def get_moneygrab_boss_ehb():
    event_id = request.args.get('event_id', type=int)
    conn = None
    try:
        conn = _moneygrab_conn()
        cur = conn.cursor(dictionary=True)
        if event_id:
            cur.execute("SELECT id, event_id, boss, ehb FROM moneygrab_boss_ehb WHERE event_id = %s ORDER BY boss", (event_id,))
        else:
            cur.execute("SELECT id, event_id, boss, ehb FROM moneygrab_boss_ehb ORDER BY boss")
        return jsonify(cur.fetchall())
    except mysql.connector.Error as err:
        return jsonify({"error": str(err)}), 500
    finally:
        if conn and conn.is_connected():
            conn.close()


@app.route('/api/moneygrab/update_boss_ehb', methods=['POST'])
def update_moneygrab_boss_ehb():
    data = request.get_json()
    boss = (data.get('boss') or '').strip()
    if not boss:
        return jsonify({"error": "boss required"}), 400
    conn = None
    try:
        conn = _moneygrab_conn()
        cur = conn.cursor()
        if data.get('id'):
            cur.execute(
                "UPDATE moneygrab_boss_ehb SET boss = %s, ehb = %s WHERE id = %s",
                (boss, data.get('ehb'), data.get('id')),
            )
        else:
            event_id = data.get('event_id')
            if not event_id:
                return jsonify({"error": "event_id required for new EHB rate"}), 400
            cur.execute(
                "INSERT INTO moneygrab_boss_ehb (event_id, boss, ehb) VALUES (%s, %s, %s) "
                "ON DUPLICATE KEY UPDATE ehb = VALUES(ehb)",
                (event_id, boss, data.get('ehb')),
            )
        conn.commit()
        return jsonify({"message": "EHB saved"}), 200
    except mysql.connector.Error as err:
        if conn:
            conn.rollback()
        return jsonify({"error": str(err)}), 500
    finally:
        if conn and conn.is_connected():
            conn.close()


@app.route('/api/moneygrab/delete_boss_ehb', methods=['POST'])
def delete_moneygrab_boss_ehb():
    data = request.get_json()
    if not data.get('id'):
        return jsonify({"error": "id required"}), 400
    conn = None
    try:
        conn = _moneygrab_conn()
        cur = conn.cursor()
        cur.execute("DELETE FROM moneygrab_boss_ehb WHERE id = %s", (data.get('id'),))
        conn.commit()
        return jsonify({"message": "EHB deleted"}), 200
    except mysql.connector.Error as err:
        if conn:
            conn.rollback()
        return jsonify({"error": str(err)}), 500
    finally:
        if conn and conn.is_connected():
            conn.close()