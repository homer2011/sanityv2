import os
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template
import mysql.connector
from flask_cors import CORS # To allow cross-origin requests from your HTML file
import pathlib

# Load environment variables from .env file
current_dir = pathlib.Path(__file__).parent
dotenv_path = current_dir / 'flask.env'
# Resolve to an absolute path for robustness
dotenv_path = dotenv_path.resolve()

if dotenv_path.exists():
    load_dotenv(dotenv_path)
    #print(f"Loaded .env from: {dotenv_path}")


flaskuser = os.getenv("flaskuser")
flaskpassword = os.getenv("flaskpassword")

#print(flaskuser)
#print(flaskpassword)

app = Flask(__name__)
CORS(app) # Enable CORS for all routes

# MySQL Database Configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': f'{flaskuser}',
    'password': f'{flaskpassword}',
    'database': 'sanity2'
}

@app.route('/api/users', methods=['GET'])
def get_users_data():
    """
    Connects to the MySQL database, executes the user query,
    and returns the data as JSON.
    """
    connection = None
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor(dictionary=True) # dictionary=True makes rows accessible by column name

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
            -- This subquery calculates the points for the last 3 months for each user
            COALESCE((
                SELECT SUM(pt.points) 
                FROM sanity2.pointtracker pt
                WHERE pt.userId = u.userId 
                  AND pt.date >= DATE_SUB(CURDATE(), INTERVAL 3 MONTH)
            ), 0) AS points_past_3_months
        FROM 
            sanity2.users u
        left JOIN 
            sanity2.ranks r ON r.id = u.rankId
        left JOIN 
            sanity2.diarytypes d ON d.difficulty = u.diaryTierClaimed
        WHERE 
            u.isActive = 1
        ORDER BY 
            u.rankId DESC, 
            points DESC
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
                p.submittedDate
            FROM
                sanity2.personalbests p
            JOIN
                sanity2.users u ON FIND_IN_SET(u.userId, p.members) > 0
            JOIN
                sanity2.bosses b ON b.id = p.bossId 
            where p.status = 2 and p.bossId not in (38,39,42)
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


@app.route('/')
def index():
    """
    Serves a simple message indicating the backend is running.
    The actual frontend will be served by your web server or opened directly.
    """
    return "MySQL Data API is running."

"""if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
"""