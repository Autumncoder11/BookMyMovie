import sqlite3
import os
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")
os.makedirs(DATA_DIR, exist_ok=True)
DB_PATH = os.path.join(DATA_DIR, "movie_booking.db")

def init_db():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys = ON")
        cursor.execute('''CREATE TABLE IF NOT EXISTS Showtime (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            multiplex TEXT,
            screen TEXT,
            time TEXT,
            movie TEXT,
            category TEXT,
            price INTEGER
        )''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS Seat_Availability (
            show_id INTEGER,
            seat_number TEXT,
            is_available INTEGER,
            FOREIGN KEY(show_id) REFERENCES Showtime(id)
        )''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS Booking (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            show_id INTEGER,
            seat_number TEXT,
            user_id TEXT,
            booking_date TEXT,
            FOREIGN KEY(show_id) REFERENCES Showtime(id)
        )''')
        cursor.executescript('''
            INSERT OR IGNORE INTO Showtime (multiplex, screen, time, movie, category, price) VALUES
            ('Inox', 'screen1', '10:30:00', 'Interstellar', 'Elite', 250),
            ('Inox', 'screen4', '10:30:00', 'Interstellar', 'Economy', 120),
            ('Inox', 'screen1', '18:45:00', 'Interstellar', 'Elite', 250),
            ('Inox', 'screen4', '18:45:00', 'Interstellar', 'Economy', 120),
            ('Broadway', 'screen1', '14:30:00', 'Interstellar', 'Elite', 250),
            ('Broadway', 'screen3', '14:30:00', 'Interstellar', 'Economy', 120),
            ('Inox', 'screen2', '14:30:00', 'The Matrix', 'Elite', 250),
            ('Inox', 'screen5', '14:30:00', 'The Matrix', 'Economy', 120),
            ('Inox', 'screen2', '20:00:00', 'The Matrix', 'Elite', 250),
            ('Inox', 'screen5', '20:00:00', 'The Matrix', 'Economy', 120),
            ('Broadway', 'screen1', '16:00:00', 'The Matrix', 'Elite', 250),
            ('Broadway', 'screen3', '16:00:00', 'The Matrix', 'Economy', 120),
            ('Inox', 'screen3', '12:00:00', 'Inception', 'Elite', 250),
            ('Inox', 'screen6', '12:00:00', 'Inception', 'Economy', 120),
            ('Broadway', 'screen2', '18:00:00', 'Inception', 'Elite', 250),
            ('Broadway', 'screen4', '18:00:00', 'Inception', 'Economy', 120),
            ('Inox', 'screen1', '15:00:00', 'Dune', 'Elite', 250),
            ('Inox', 'screen4', '15:00:00', 'Dune', 'Economy', 120),
            ('Broadway', 'screen2', '11:00:00', 'Dune', 'Elite', 250),
            ('Broadway', 'screen4', '11:00:00', 'Dune', 'Economy', 120),
            ('Inox', 'screen2', '17:00:00', 'Avatar', 'Elite', 250),
            ('Inox', 'screen5', '17:00:00', 'Avatar', 'Economy', 120),
            ('Broadway', 'screen1', '19:00:00', 'Avatar', 'Elite', 250),
            ('Broadway', 'screen3', '19:00:00', 'Avatar', 'Economy', 120);
        ''')
        cursor.execute('''
            INSERT OR IGNORE INTO Seat_Availability (show_id, seat_number, is_available)
            SELECT s.id, row || printf('%02d', seat_num), 1
            FROM Showtime s
            CROSS JOIN (
                SELECT char(64 + row_num) AS row
                FROM (SELECT row_num FROM (SELECT 1 AS row_num UNION SELECT 2 UNION SELECT 3 UNION SELECT 4 UNION SELECT 5 UNION SELECT 6 UNION SELECT 7 UNION SELECT 8 UNION SELECT 9 UNION SELECT 10 UNION SELECT 11 UNION SELECT 12) rows) numbers
                WHERE row BETWEEN 'A' AND 'L'
            ) rows
            CROSS JOIN (
                SELECT seat_num
                FROM (SELECT seat_num FROM (SELECT 1 AS seat_num UNION SELECT 2 UNION SELECT 3 UNION SELECT 4 UNION SELECT 5 UNION SELECT 6 UNION SELECT 7 UNION SELECT 8 UNION SELECT 9 UNION SELECT 10 UNION SELECT 11 UNION SELECT 12 UNION SELECT 13 UNION SELECT 14 UNION SELECT 15 UNION SELECT 16 UNION SELECT 17) seats) numbers
                WHERE seat_num BETWEEN 1 AND 17
            ) seats
            WHERE s.category = 'Elite';
        ''')
        cursor.execute('''
            INSERT OR IGNORE INTO Seat_Availability (show_id, seat_number, is_available)
            SELECT s.id, row || printf('%02d', seat_num), 1
            FROM Showtime s
            CROSS JOIN (
                SELECT char(64 + row_num) AS row
                FROM (SELECT row_num FROM (SELECT 13 AS row_num UNION SELECT 14) rows) numbers
                WHERE row BETWEEN 'M' AND 'N'
            ) rows
            CROSS JOIN (
                SELECT seat_num
                FROM (SELECT seat_num FROM (SELECT 1 AS seat_num UNION SELECT 2 UNION SELECT 3 UNION SELECT 4 UNION SELECT 5 UNION SELECT 6 UNION SELECT 7 UNION SELECT 8 UNION SELECT 9 UNION SELECT 10 UNION SELECT 11 UNION SELECT 12 UNION SELECT 13 UNION SELECT 14 UNION SELECT 15 UNION SELECT 16 UNION SELECT 17) seats) numbers
                WHERE seat_num BETWEEN 1 AND 17
            ) seats
            WHERE s.category = 'Economy';
        ''')
        conn.commit()
        print("Database initialized successfully")
    except sqlite3.Error as e:
        print(f"Database error during initialization: {e}")
        raise
    finally:
        if 'conn' in locals():
            conn.close()

def get_movies():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT movie FROM Showtime")
    movies = [row[0] for row in cursor.fetchall()]
    conn.close()
    return sorted(movies)

def get_multiplexes_for_movie(movie):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT multiplex FROM Showtime WHERE movie = ?", (movie,))
    multiplexes = [row[0] for row in cursor.fetchall()]
    conn.close()
    return sorted(multiplexes)

def get_showtimes(multiplex, movie, category):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT time FROM Showtime WHERE multiplex = ? AND movie = ? AND category = ?", (multiplex, movie, category))
    showtimes = [row[0] for row in cursor.fetchall()]
    formatted_showtimes = []
    for time in showtimes:
        time_obj = datetime.strptime(time, "%H:%M:%S")
        formatted_showtimes.append(time_obj.strftime("%I:%M %p"))
    conn.close()
    return sorted(formatted_showtimes)

def report_seat_availability():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''SELECT s.multiplex, s.screen, s.time, s.movie, b.seat_number, s.category, b.booking_date
                      FROM Booking b
                      JOIN Showtime s ON b.show_id = s.id
                      ORDER BY b.booking_date, s.multiplex, s.time, b.seat_number''')
    rows = cursor.fetchall()
    if not rows:
        return "No bookings found."
    headers = ["Multiplex", "Screen", "Showtime", "Movie", "Seat", "Category", "Date"]
    col_widths = [10, 8, 10, 12, 6, 10, 10]
    header_row = " | ".join(f"{header:<{width}}" for header, width in zip(headers, col_widths))
    separator = "-+-".join("-" * width for width in col_widths)
    formatted_rows = []
    for row in rows:
        multiplex, screen, time, movie, seat_number, category, date = row
        display_seat = seat_number[0] + str(int(seat_number[1:]))
        formatted_row = " | ".join(f"{str(item):<{width}}" for item, width in zip([multiplex, screen, time, movie, display_seat, category, date], col_widths))
        formatted_rows.append(formatted_row)
    report = ["Booked Seats Report:", header_row, separator] + formatted_rows
    conn.close()
    return "\n".join(report)