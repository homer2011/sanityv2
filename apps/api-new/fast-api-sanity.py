import os
import pathlib
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic_settings import BaseSettings
import mysql.connector
from mysql.connector import Error


# --- Configuration & Environment ---
class Settings(BaseSettings):
    flaskuser: str
    flaskpassword: str

    class Config:
        # Resolving path to the .env file
        env_file = str(pathlib.Path(__file__).parent / "flask.env")


settings = Settings()

app = FastAPI(title="Sanity API", description="FastAPI port of the Sanity Bingo Backend")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database Configurations
DB_CONFIG = {
    'host': 'localhost',
    'user': settings.flaskuser,
    'password': settings.flaskpassword,
    'database': 'sanity2'
}

BINGO_DB_CONFIG = {
    'host': 'localhost',
    'user': settings.flaskuser,
    'password': settings.flaskpassword,
    'database': 'sanitybingo'
}


# --- Helper for DB Connections ---
def get_db_connection(config: dict):
    try:
        connection = mysql.connector.connect(**config)
        return connection
    except Error as err:
        print(f"Database connection error: {err}")
        raise HTTPException(status_code=500, detail="Database connection failed")


# --- API ENDPOINTS ---

@app.get("/api/rankChanges")
def get_rank_changes():
    conn = get_db_connection(DB_CONFIG)
    cursor = conn.cursor(dictionary=True)
    try:
        query = """
            SELECT a.actionDate, u.userid, u.displayName, r_before.name AS rank_before, 
                   r_after.name AS rank_after, r_before.id as rankId_before, r_after.id as rankId_after
            FROM sanity2.auditlogs a
            JOIN sanity2.users u ON u.userid = SUBSTRING_INDEX(SUBSTRING_INDEX(a.actionNote, ' ', 2), ' ', -1)
            JOIN sanity2.ranks r_before ON r_before.id = SUBSTRING_INDEX(SUBSTRING_INDEX(a.actionNote, ' from ', -1), ' to ', 1)
            JOIN sanity2.ranks r_after ON r_after.id = SUBSTRING_INDEX(a.actionNote, ' to ', -1)
            WHERE a.actionNote LIKE 'UPDATED % RANK from % to %' 
              AND r_before.name NOT IN ('quit', 'retired') 
              AND r_after.name NOT IN ('quit', 'retired')
            ORDER BY a.actionDate DESC 
        """
        cursor.execute(query)
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


@app.get("/api/points")
def get_points_data(
        page: int = Query(1, ge=1),
        per_page: int = Query(100, ge=1)
):
    offset = (page - 1) * per_page
    conn = get_db_connection(DB_CONFIG)
    cursor = conn.cursor(dictionary=True)
    try:
        # Main data
        query = """
            SELECT p.Id, u.displayName, p.points, p.notes, s.messageUrl, p.`date` 
            FROM sanity2.pointtracker p 
            INNER JOIN sanity2.users u ON u.userId = p.userId 
            LEFT JOIN sanity2.submissions s ON s.Id = p.dropId 
            ORDER BY p.Id DESC LIMIT %s OFFSET %s
        """
        cursor.execute(query, (per_page, offset))
        points_data = cursor.fetchall()

        # Total count
        cursor.execute("SELECT COUNT(*) as total FROM sanity2.pointtracker")
        total_count = cursor.fetchone()['total']

        return {
            "metadata": {
                "total_points_records": total_count,
                "page": page,
                "per_page": per_page,
                "total_pages": (total_count + per_page - 1) // per_page
            },
            "data": points_data
        }
    finally:
        cursor.close()
        conn.close()


@app.get("/api/bingo/board_details/{event_id}")
def get_board_details(event_id: int):
    conn = get_db_connection(BINGO_DB_CONFIG)
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id FROM bingo_boards WHERE event_id = %s", (event_id,))
        board_result = cursor.fetchone()
        if not board_result:
            return []

        board_id = board_result['id']
        tile_query = """
            SELECT bt.id, bt.position, bt.task_name, bt.description, bt.tileType, 
                   bt.dropOrPointReq, bt.points, bbi.bossImageUrl as image_url
            FROM bingo_tiles bt 
            LEFT JOIN sanitybingo.bingo_bossImages bbi ON bbi.bossName = bt.task_name
            WHERE board_id = %s ORDER BY position
        """
        cursor.execute(tile_query, (board_id,))
        tiles = cursor.fetchall()

        if not tiles:
            return []

        # Fetch items for all tiles
        tile_ids = [tile['id'] for tile in tiles]
        format_strings = ','.join(['%s'] * len(tile_ids))
        item_query = f"SELECT tileId, dropName FROM bingo_tile_items WHERE tileId IN ({format_strings})"
        cursor.execute(item_query, tuple(tile_ids))
        items = cursor.fetchall()

        # Map items to tiles
        items_map = {}
        for item in items:
            items_map.setdefault(item['tileId'], []).append(item['dropName'])

        for tile in tiles:
            tile['items'] = items_map.get(tile['id'], [])

        return tiles
    finally:
        cursor.close()
        conn.close()


# Example POST route conversion
@app.post("/api/bingo/create_event", status_code=201)
def create_new_event(data: dict):
    conn = get_db_connection(BINGO_DB_CONFIG)
    cursor = conn.cursor()
    try:
        event_query = "INSERT INTO bingo_events (name, start_date, end_date, is_active) VALUES (%s, %s, %s, 0)"
        cursor.execute(event_query, (data['name'], data['start_date'], data['end_date']))
        event_id = cursor.lastrowid

        board_query = "INSERT INTO bingo_boards (event_id, name) VALUES (%s, %s)"
        cursor.execute(board_query, (event_id, f"{data['name']} Board"))

        conn.commit()
        return {"message": "Event created successfully", "id": event_id}
    except Error as err:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(err))
    finally:
        cursor.close()
        conn.close()


@app.get("/")
def index():
    return {"message": "FastAPI Data API is running."}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)