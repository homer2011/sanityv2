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


@app.route('/api/rankChanges', methods=['GET'])
def get_rank_changes():
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
                a.actionDate,
                u.userid,
                u.displayName,
                r_before.name AS rank_before, -- Changed from r_before.rank_name
                r_after.name AS rank_after,   -- Changed from r_after.rank_name
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
            order BY 
                a.actionDate desc 
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
        cursor = connection.cursor(dictionary=True) # dictionary=True makes rows accessible by column name

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


@app.route('/api/discordProfileUrl', methods=['GET'])
def get_discord_profile_url():
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


@app.route('/api/getUserEhb', methods=['GET'])
def get_user_ehb():
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
                GROUP_CONCAT(DISTINCT s.displayName SEPARATOR ', ') AS associated_rsns,
                SUM(s.ehbWeeklyEhb) AS total_weekly_ehb,
                SUM(s.chambers_of_xericWeeklyEHB) as 'chambers_of_xericWeeklyEHB', 
                SUM(s.chambers_of_xeric_challenge_modeWeeklyEHB) as 'chambers_of_xeric_challenge_modeWeeklyEHB',
                sum(s.the_corrupted_gauntletWeeklyEHB) as 'the_corrupted_gauntletWeeklyEHB',
                sum(s.sol_hereditWeeklyEHB) as 'sol_hereditWeeklyEHB',
                sum(s.theatre_of_bloodWeeklyEHB) as 'theatre_of_bloodWeeklyEHB',
                sum(s.theatre_of_blood_hard_modeWeeklyEHB) as 'theatre_of_blood_hard_modeWeeklyEHB',
                sum(s.tzkal_zukWeeklyEHB) as 'tzkal_zukWeeklyEHB',
                sum(s.tztok_jadWeeklyEHB) as 'tztok_jadWeeklyEHB'
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


@app.route('/api/discordmsgssentyearly', methods=['GET'])
def get_yearly_discord_msgs():
    """
    Connects to the MySQL database, executes the user query,
    and returns the data as JSON.
    """
    connection = None
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor(dictionary=True) # dictionary=True makes rows accessible by column name

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
        cursor = connection.cursor(dictionary=True) # dictionary=True makes rows accessible by column name

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
        cursor = connection.cursor(dictionary=True) # dictionary=True makes rows accessible by column name

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
                GROUP_CONCAT(participant_u.displayName ORDER BY sp.id SEPARATOR ', ') AS member_names,
                s.notes,
                s.value,
                s2.name AS status_name,
                s.imageUrl,
                s.reviewedDate,
                reviewer_u.displayName AS reviewer
            FROM
                sanity2.submissions s
            -- Replaced the old FIND_IN_SET join with these two efficient joins
            LEFT JOIN
                sanity2.submission_participants sp ON s.Id = sp.dropId
            LEFT JOIN
                sanity2.users participant_u ON sp.userId = participant_u.userId
            -- The rest of your original joins
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
                s.imageUrl,
                s.reviewedDate,
                s2.name,
                reviewer_u.displayName
            ORDER BY
                Id DESC;
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