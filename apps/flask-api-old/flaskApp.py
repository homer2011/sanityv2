import os
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request, session, redirect, url_for
import requests
from functools import wraps
from datetime import timedelta
import mysql.connector
from flask_cors import CORS  # To allow cross-origin requests from your HTML file
import pathlib

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
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor(dictionary=True)
        query = "SELECT id, bossName, item, itemPoints, droprate, hoursToGetDrop FROM sanity2.bingo_all_items ORDER BY bossName, item"
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
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor()
        query = "UPDATE sanity2.bingo_all_items SET bossName=%s, item=%s, itemPoints=%s, droprate=%s, hoursToGetDrop=%s WHERE id=%s"
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
            WHERE s.status IN (2,3,1,4) and s.bingo = 1
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

        query = """
            SELECT RSN, abyssal_sire, alchemical_hydra, artio, barrows_chests, bryophyta, callisto, calvarion, cerberus, chambers_of_xeric, chambers_of_xeric_challenge_mode, chaos_elemental, chaos_fanatic, commander_zilyana, corporeal_beast, crazy_archaeologist, dagannoth_prime, dagannoth_rex, dagannoth_supreme, deranged_archaeologist, duke_sucellus, general_graardor, giant_mole, grotesque_guardians, hespori, kalphite_queen, king_black_dragon, kraken, kreearra, kril_tsutsaroth, lunar_chests, mimic, nex, nightmare, phosanis_nightmare, obor, phantom_muspah, sarachnis, scorpia, scurrius, skotizo, sol_heredit, spindel, tempoross, the_gauntlet, the_corrupted_gauntlet, the_leviathan, the_whisperer, theatre_of_blood, theatre_of_blood_hard_mode, thermonuclear_smoke_devil, tombs_of_amascut, tombs_of_amascut_expert, tzkal_zuk, tztok_jad, vardorvis, venenatis, vetion, vorkath, wintertodt, zalcano, zulrah, yama            FROM sanity2.bingobosskc;
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
                LEFT JOIN sanity2.uss u ON u.userId = a.userId
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
    Fetches all tiles for the currently active bingo board.
    """
    connection = None
    try:
        connection = mysql.connector.connect(**BINGO_DB_CONFIG)
        cursor = connection.cursor(dictionary=True)

        query = """
            SELECT btm.team_id, u.displayName, u.mainRSN , u.altRSN 
            FROM bingo_team_members btm
            JOIN sanity2.users u ON btm.user_id = u.userId
        """
        cursor.execute(query)
        board_data = cursor.fetchall()
        return jsonify(board_data)

    except mysql.connector.Error as err:
        print(f"Error fetching bingo board: {err}")
        return jsonify({"error": str(err)}), 500
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()


@app.route('/api/bingo/board', methods=['GET'])
def get_bingo_board():
    """
    Fetches all tiles for the currently active bingo board.
    """
    connection = None
    try:
        connection = mysql.connector.connect(**BINGO_DB_CONFIG)
        cursor = connection.cursor(dictionary=True)

        query = """
            SELECT 
                t.id as tile_id, 
                t.task_name as text,
                t.description as sub_text, 
                t.points, 
                t.tileType,
                t.dropOrPointReq,
                bbi.bossImageUrl as image_url,
                (CASE WHEN t.id IS NOT NULL THEN 1 ELSE 0 END) as completed
            FROM bingo_tiles t
            JOIN bingo_boards b ON t.board_id = b.id
            JOIN bingo_events e ON b.event_id = e.id
            LEFT JOIN (
                SELECT DISTINCT tile_id FROM bingo_tile_completion
            ) c ON t.id = c.tile_id
            left join sanitybingo.bingo_bossImages bbi on bbi.bossName = t.task_name 
            WHERE e.is_active = 1
            ORDER BY t.position;
        """
        cursor.execute(query)
        board_data = cursor.fetchall()
        return jsonify(board_data)

    except mysql.connector.Error as err:
        print(f"Error fetching bingo board: {err}")
        return jsonify({"error": str(err)}), 500
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()


@app.route('/api/bingo/events', methods=['GET'])
def get_bingo_events():
    """
    Fetches all tiles for the currently active bingo board.
    """
    connection = None
    try:
        connection = mysql.connector.connect(**BINGO_DB_CONFIG)
        cursor = connection.cursor(dictionary=True)

        query = """
            select id,name,start_date,end_date,is_active
            from sanitybingo.bingo_events
            where is_active = 1
        """
        cursor.execute(query)
        board_data = cursor.fetchall()
        return jsonify(board_data)

    except mysql.connector.Error as err:
        print(f"Error fetching bingo board: {err}")
        return jsonify({"error": str(err)}), 500
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()


@app.route('/api/bingo/raiditemvalues', methods=[
    'GET'])  # WORKS#WORKS#WORKS#WORKS#WORKS#WORKS#WORKS#WORKS#WORKS#WORKS#WORKS#WORKS#WORKS#WORKS#WORKS#WORKS#WORKS
def get_raid_item_values():
    """
    Fetches raid item point values for the active bingo event.
    """
    connection = None
    try:
        connection = mysql.connector.connect(**BINGO_DB_CONFIG)
        cursor = connection.cursor(dictionary=True)
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
    Fetches all boss EHB values.
    """
    connection = None
    try:
        connection = mysql.connector.connect(**BINGO_DB_CONFIG)
        cursor = connection.cursor(dictionary=True)
        query = "SELECT id, boss, ehb, event_id FROM bingo_boss_ehb ORDER BY boss;"
        cursor.execute(query)
        data = cursor.fetchall()
        return jsonify(data)
    except mysql.connector.Error as err:
        print(f"Error fetching boss ehb values: {err}")
        return jsonify({"error": str(err)}), 500
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()


@app.route('/api/bingo/tileitems', methods=['GET'])  # EHHHHHHHHHHHHHHHHHHHHH
def get_bingo_tileitems():
    """
    Fetches detailed information for all teams in the active bingo event.
    """
    connection = None
    try:
        connection = mysql.connector.connect(**BINGO_DB_CONFIG)
        cursor = connection.cursor(dictionary=True)
        query = """SELECT 
                        id,eventId,dropName,tileId 
                    from 
                        bingo_tile_items bti;"""
        cursor.execute(query)
        data = cursor.fetchall()
        return jsonify(data)
    except mysql.connector.Error as err:
        print(f"Error fetching boss ehb values: {err}")
        return jsonify({"error": str(err)}), 500
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()


@app.route('/api/bingo/teams', methods=['GET'])  # EHHHHHHHHHHHHHHHHHHHHH
def get_bingo_teams():
    """
    Fetches detailed information for all teams in the active bingo event.
    """
    connection = None
    try:
        connection = mysql.connector.connect(**BINGO_DB_CONFIG)
        cursor = connection.cursor(dictionary=True)
        query = """SELECT
                    bt.id,
                    bt.name,
                    bt.captain_userid,
                    u_cap.displayName AS captain_name,
                    bt.cocaptain_userid,
                    u_cocap.displayName AS cocaptain_name
                FROM
                    sanitybingo.bingo_teams bt
                LEFT JOIN
                    sanity2.users u_cap ON u_cap.userId = bt.captain_userid
                LEFT JOIN
                    sanity2.users u_cocap ON u_cocap.userId = bt.cocaptain_userid;"""
        cursor.execute(query)
        data = cursor.fetchall()
        return jsonify(data)
    except mysql.connector.Error as err:
        print(f"Error fetching boss ehb values: {err}")
        return jsonify({"error": str(err)}), 500
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()


@app.route('/api/bingo/bossitems', methods=['GET'])  # EHHHHHHHHHHHHHHHHHHHHH
def get_bingo_boss_items():
    """
    Fetches detailed information for all teams in the active bingo event.
    """
    connection = None
    try:
        connection = mysql.connector.connect(**BINGO_DB_CONFIG)
        cursor = connection.cursor(dictionary=True)
        query = """
            SELECT 
                id, bossName, item, itemPoints, droprate, hoursToGetDrop
            FROM 
                sanitybingo.bingo_boss_items;
                    """
        cursor.execute(query)
        data = cursor.fetchall()
        return jsonify(data)
    except mysql.connector.Error as err:
        print(f"Error fetching boss ehb values: {err}")
        return jsonify({"error": str(err)}), 500
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()


@app.route('/api/bingo/overview', methods=['GET'])
def get_bingo_overview():
    """
    Fetches all aggregated data needed for the bingo overview page.
    """
    connection = None
    try:
        connection = mysql.connector.connect(**BINGO_DB_CONFIG)
        cursor = connection.cursor(dictionary=True)

        # Get active event and board ID
        cursor.execute("""
            SELECT e.id as event_id, b.id as board_id 
            FROM bingo_events e 
            JOIN bingo_boards b ON e.id = b.event_id 
            WHERE e.is_active = 1 
            LIMIT 1
        """)
        event_info = cursor.fetchone()
        if not event_info:
            return jsonify({"error": "No active bingo event found"}), 404
        active_event_id = event_info['event_id']
        active_board_id = event_info['board_id']

        # Query for Top Individual Points ########## DOES NOT WORK
        top_ind_points_query = """
            SELECT u.displayName, SUM(ti.points) as points
            FROM bingo_tile_completion c
            JOIN bingo_tiles ti ON c.tile_id = ti.id
            JOIN sanity2.users u ON c.user_id = u.userId
            JOIN bingo_teams t ON c.team_id = t.id
            WHERE t.event_id = %s
            GROUP BY c.user_id, u.displayName
            ORDER BY points DESC
            LIMIT 1;
        """
        cursor.execute(top_ind_points_query, (active_event_id,))
        top_individual_points = cursor.fetchone()

        # Calculate Board Completion Percentage
        # 1. Get total tiles for the active board
        cursor.execute("SELECT COUNT(*) as total FROM bingo_tiles WHERE board_id = %s", (active_board_id,))
        total_tiles_result = cursor.fetchone()
        total_tiles = total_tiles_result['total'] if total_tiles_result and total_tiles_result['total'] > 0 else 1

        # 2. Get count of distinct completed tiles for the active event
        cursor.execute("""
            SELECT COUNT(DISTINCT tile_id) as completed 
            FROM bingo_tile_completion c
            JOIN bingo_teams t ON c.team_id = t.id
            WHERE t.event_id = %s
        """, (active_event_id,))
        completed_tiles_result = cursor.fetchone()
        completed_tiles = completed_tiles_result['completed'] if completed_tiles_result else 0

        board_completion_percentage = (completed_tiles / total_tiles) * 100

        # Query for Team Leaderboard
        leaderboard_query = """
            SELECT 
                t.name as team_name,
                capt.displayName as captain,
                cocapt.displayName as co_captain,
                COALESCE(SUM(ti.points), 0) as team_points,
                COUNT(DISTINCT c.tile_id) as tiles_done,
                0 as team_ehb, -- Placeholder for EHB
                (COUNT(DISTINCT c.tile_id) / %s) * 100 as completion_percentage
            FROM bingo_teams t
            LEFT JOIN bingo_tile_completion c ON t.id = c.team_id
            LEFT JOIN bingo_tiles ti ON c.tile_id = ti.id
            LEFT JOIN sanity2.users capt ON t.captain_userid = capt.userId
            LEFT JOIN sanity2.users cocapt ON t.cocaptain_userid = cocapt.userId
            WHERE t.event_id = %s
            GROUP BY t.id, t.name, capt.displayName, cocapt.displayName
            ORDER BY team_points DESC;
        """
        cursor.execute(leaderboard_query, (total_tiles, active_event_id,))
        team_leaderboard = cursor.fetchall()

        # Explicitly cast decimal values to float for JSON compatibility
        for team in team_leaderboard:
            team['completion_percentage'] = float(team['completion_percentage'])

        overview_data = {
            "top_individual_ehb": top_individual_points,  # Using points as a stand-in for now
            "top_individual_points": top_individual_points,
            "board_completion_percentage": float(board_completion_percentage),
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
    """ Fetches a list of all bingo events. """
    connection = None
    try:
        connection = mysql.connector.connect(**BINGO_DB_CONFIG, autocommit=True)
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT id, name, start_date, end_date, is_active FROM bingo_events ORDER BY start_date DESC;")
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


@app.route('/api/bingo/update_board', methods=['POST'])
def update_bingo_board():
    """
    Updates an existing bingo board. Deletes old tiles and inserts new ones in a transaction.
    """
    data = request.get_json()
    event_id = data.get('eventId')
    tiles_data = data.get('tiles')

    if not event_id:
        return jsonify({"error": "Missing eventId"}), 400

    if not tiles_data:
        return jsonify({"error": "Missing tiles data"}), 400

    connection = None
    try:
        connection = mysql.connector.connect(**BINGO_DB_CONFIG)
        cursor = connection.cursor()

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
        query = "select u.mainRSN, orm.osrsName from sanity2.users u inner join sanity2.osrsRankMapping orm on orm.id = u.rankId ;"
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
def get_boss_items_for_generator():
    """
    Fetches all items with their boss and points for the auto-generator.
    This now reflects the user's provided JSON structure.
    """
    connection = None
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor(dictionary=True)
        # This query should match the structure of the user-provided JSON
        query = "SELECT bossName, droprate, id, item, itemPoints FROM sanity2.bingo_all_items;"
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