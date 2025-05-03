import re
from datetime import datetime, timedelta
import sqlite3
import database
from difflib import get_close_matches

class Chatbot:
    def __init__(self):
        self.context = {
            'movie': None,
            'multiplex': None,
            'time': None,
            'quantity': None,
            'category': None,
            'seats': None,
            'booking_date': None,
            'is_cancel': False
        }
        self.state = 'start'
        self.available_movies = database.get_movies()
        self.multiplex_map = {'inox': 'Inox', 'broadway': 'Broadway', 'kg': 'KG'}
        self.seat_categories = ['elite', 'economy']
        self.command_keywords = ['book', 'bok', 'reserve', 'tickets', 'tckets', 'ticket']

    def reset_context(self):
        """Fully reset context and state."""
        print("Resetting chatbot context and state")
        self.context = {
            'movie': None,
            'multiplex': None,
            'time': None,
            'quantity': None,
            'category': None,
            'seats': None,
            'booking_date': None,
            'is_cancel': False
        }
        self.state = 'start'

    def get_dates(self):
        """Generate the next 7 days starting from the current date."""
        today = datetime.now().date()
        dates = [(today + timedelta(days=i)).strftime("%a %d %b").upper() for i in range(7)]
        return dates

    def parse_date(self, date_str):
        """Convert date string (e.g., 'SAT 03 MAY') to YYYY-MM-DD format."""
        try:
            date_obj = datetime.strptime(date_str, "%a %d %b")
            date_obj = date_obj.replace(year=2025)
            return date_obj.strftime("%Y-%m-%d")
        except ValueError:
            print(f"Date parsing failed for: {date_str}")
            return None

    def get_multiplexes_for_movie(self, movie):
        return database.get_multiplexes_for_movie(movie)

    def get_showtimes(self, multiplex, movie, category):
        return database.get_showtimes(multiplex, movie, category)

    def fuzzy_match_movie(self, text):
        """Find the closest matching movie name."""
        text = text.lower().strip()
        matches = get_close_matches(text, [m.lower() for m in self.available_movies], n=1, cutoff=0.6)
        if matches:
            for movie in self.available_movies:
                if movie.lower() == matches[0]:
                    print(f"Fuzzy matched movie: {text} -> {movie}")
                    return movie
        print(f"No movie match for: {text}")
        return None

    def fuzzy_match_multiplex(self, text):
        """Find the closest matching multiplex name."""
        text = text.lower().strip()
        options = list(self.multiplex_map.keys()) + list(self.multiplex_map.values())
        matches = get_close_matches(text, options, n=1, cutoff=0.4)
        if matches:
            matched = matches[0]
            for key, value in self.multiplex_map.items():
                if matched.lower() == key.lower() or matched.lower() == value.lower():
                    print(f"Fuzzy matched multiplex: {text} -> {value}")
                    return value
        print(f"No multiplex match for: {text}")
        return None

    def fuzzy_match_category(self, text):
        """Find the closest matching seat category."""
        text = text.lower().strip()
        matches = get_close_matches(text, self.seat_categories, n=1, cutoff=0.6)
        if matches:
            category = 'Elite' if matches[0] == 'elite' else 'Economy'
            print(f"Fuzzy matched category: {text} -> {category}")
            return category
        print(f"No category match for: {text}")
        return None

    def extract_entities(self, text):
        """Extract booking entities from text."""
        text_lower = text.lower().strip()
        print(f"Extracting entities from: {text_lower}")
        cancel_keywords = ['cancel', 'delete', 'remove']
        is_cancel = any(keyword in text_lower for keyword in cancel_keywords)
        
        movie = None
        multiplex = None
        quantity = None
        seat_category = None
        seat_prefs = None
        time = None
        booking_date = None
        
        is_booking = any(keyword in text_lower for keyword in self.command_keywords)
        
        for m in self.available_movies:
            if m.lower() in text_lower:
                movie = m
                print(f"Extracted movie: {movie}")
                break
        if not movie:
            movie = self.fuzzy_match_movie(text_lower)
        
        for mx_key, mx_value in self.multiplex_map.items():
            if mx_key.lower() in text_lower or mx_value.lower() in text_lower:
                multiplex = mx_value
                print(f"Extracted multiplex: {multiplex}")
                break
        if not multiplex:
            multiplex = self.fuzzy_match_multiplex(text_lower)
        
        # Extract quantity, avoiding time and date formats (e.g., '06:45', '04 MAY')
        quantity_match = re.search(r'\b(\d+)\s*(?:ticket|tickets|tckets)?\b(?!\s*(?:am|pm|:|\d+\s*(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)))', text_lower, re.IGNORECASE)
        if quantity_match:
            quantity = int(quantity_match.group(1))
            print(f"Extracted quantity: {quantity}")
        
        if 'elite' in text_lower:
            seat_category = 'Elite'
            print(f"Extracted category: {seat_category}")
        elif 'economy' in text_lower:
            seat_category = 'Economy'
            print(f"Extracted category: {seat_category}")
        else:
            seat_category = self.fuzzy_match_category(text_lower)
        
        seat_pattern = r'\b([a-n])([1-9][0-7]?)\b'
        seat_matches = re.findall(seat_pattern, text_lower)
        if seat_matches:
            seat_prefs = [(row.upper(), f'{row.upper()}{col}') for row, col in seat_matches]
        else:
            seat_prefs = []
        
        time_match = re.search(r'(\d{1,2}:\d{2}\s*(?:AM|PM|am|pm)|(?:\d{1,2}:\d{2}:\d{2}))', text_lower, re.IGNORECASE)
        if time_match:
            time_str = time_match.group(0)
            time = self.parse_time(time_str)
        
        dates = self.get_dates()
        for date in dates:
            if date.lower() in text_lower:
                booking_date = self.parse_date(date)
                print(f"Extracted booking date: {booking_date}")
                break
        
        print(f"Extracted entities: movie={movie}, multiplex={multiplex}, quantity={quantity}, category={seat_category}, seats={seat_prefs}, time={time}, booking_date={booking_date}, is_cancel={is_cancel}, is_booking={is_booking}")
        
        return movie, multiplex, quantity, seat_category, seat_prefs, time, is_cancel, booking_date, is_booking

    def parse_time(self, time_str):
        """Parse time string into HH:MM:SS format."""
        print(f"Parsing time: {time_str}")
        try:
            time_str = time_str.strip()
            if time_str.isdigit():
                hour = int(time_str)
                if 0 <= hour <= 12:
                    time_str = f"{hour}:00 PM" if hour < 12 else "12:00 PM"
                elif 13 <= hour <= 23:
                    time_str = f"{hour-12}:00 PM"
                else:
                    print(f"Invalid hour: {time_str}")
                    return None
            try:
                time_obj = datetime.strptime(time_str, '%I:%M %p')
                parsed_time = time_obj.strftime('%H:%M:%S')
                print(f"Parsed to 24-hour (12-hour input): {parsed_time}")
                return parsed_time
            except ValueError:
                try:
                    time_obj = datetime.strptime(time_str, '%I %p')
                    parsed_time = time_obj.strftime('%H:%M:%S')
                    print(f"Parsed to 24-hour (hour-only 12-hour input): {parsed_time}")
                    return parsed_time
                except ValueError:
                    try:
                        time_obj = datetime.strptime(time_str, '%H:%M:%S')
                        parsed_time = time_obj.strftime('%H:%M:%S')
                        print(f"Parsed to 24-hour (24-hour input): {parsed_time}")
                        return parsed_time
                    except ValueError:
                        print(f"Time parsing failed for: {time_str}")
                        return None
        except ValueError:
            print(f"Time parsing failed for: {time_str}")
            return None

    def find_closest_time(self, target_time, showtimes):
        """Find the closest showtime to the target time within 2 hours."""
        if not showtimes:
            print("No showtimes available for closest time search")
            return None
        try:
            target = datetime.strptime(target_time, '%H:%M:%S')
            min_diff = float('inf')
            closest_time = None
            for showtime in showtimes:
                showtime_24hr = datetime.strptime(showtime, '%I:%M %p').strftime('%H:%M:%S')
                showtime_obj = datetime.strptime(showtime_24hr, '%H:%M:%S')
                diff = abs((showtime_obj - target).total_seconds())
                if diff < 7200 and diff < min_diff:
                    min_diff = diff
                    closest_time = showtime_24hr
            if closest_time:
                print(f"Closest showtime to {target_time}: {closest_time}")
                return closest_time
            print(f"No showtime within 2 hours of {target_time}")
            return None
        except ValueError as e:
            print(f"Error finding closest time for {target_time}: {str(e)}")
            return None

    def process_booking(self):
        """Process the booking request and update the database."""
        print(f"\n=== Processing Booking ===")
        print(f"Context: {self.context}")
        
        try:
            conn = sqlite3.connect(database.DB_PATH)
            cursor = conn.cursor()
            
            print(f"Querying Showtime: multiplex={self.context['multiplex']}, movie={self.context['movie']}, category={self.context['category']}, time={self.context['time']}")
            cursor.execute("""
                SELECT id FROM Showtime 
                WHERE multiplex = ? AND movie = ? AND category = ? AND time = ?
            """, (self.context['multiplex'], self.context['movie'], self.context['category'], self.context['time']))
            
            show_id = cursor.fetchone()
            print(f"Show ID result: {show_id}")
            
            if not show_id:
                available_showtimes = database.get_showtimes(self.context['multiplex'], self.context['movie'], self.context['category'])
                if not available_showtimes:
                    conn.close()
                    print("No showtimes available for the given movie, multiplex, and category")
                    return f"No showtime found for the specified details. Available showtimes: None"
                
                closest_time = self.find_closest_time(self.context['time'], available_showtimes)
                if closest_time:
                    cursor.execute("""
                        SELECT id FROM Showtime 
                        WHERE multiplex = ? AND movie = ? AND category = ? AND time = ?
                    """, (self.context['multiplex'], self.context['movie'], self.context['category'], closest_time))
                    show_id = cursor.fetchone()
                    if show_id:
                        print(f"Using closest time: {closest_time}")
                        self.context['time'] = closest_time
                    else:
                        conn.close()
                        print(f"No show ID found for closest time: {closest_time}")
                        return f"No showtime found for the specified details. Available showtimes: {', '.join(available_showtimes)}"
                else:
                    conn.close()
                    print("No close showtime found")
                    return f"No showtime found for the specified details. Available showtimes: {', '.join(available_showtimes)}"
            
            show_id = show_id[0]
            
            cursor.execute("""
                SELECT seat_number FROM Seat_Availability 
                WHERE show_id = ? AND is_available = 1 
                LIMIT ?
            """, (show_id, self.context['quantity']))
            
            available_seats = [row[0] for row in cursor.fetchall()]
            print(f"Available seats: {available_seats}")
            
            if len(available_seats) < self.context['quantity']:
                conn.close()
                return f"Not enough seats available. Only {len(available_seats)} seats left."
            
            user_id = "user123"
            booking_date = self.context['booking_date'] or datetime.now().strftime('%Y-%m-%d')
            
            for seat in available_seats:
                cursor.execute("""
                    INSERT INTO Booking (show_id, seat_number, user_id, booking_date) 
                    VALUES (?, ?, ?, ?)
                """, (show_id, seat, user_id, booking_date))
                cursor.execute("""
                    UPDATE Seat_Availability 
                    SET is_available = 0 
                    WHERE show_id = ? AND seat_number = ?
                """, (show_id, seat))
            
            conn.commit()
            conn.close()
            
            time_obj = datetime.strptime(self.context['time'], '%H:%M:%S')
            formatted_time = time_obj.strftime('%I:%M %p')
            display_seats = [seat[0] + str(int(seat[1:])) for seat in available_seats]
            return f"Successfully booked {self.context['quantity']} {self.context['category']} tickets for {self.context['movie']} at {self.context['multiplex']} on {booking_date} {formatted_time}: {', '.join(display_seats)}"
        
        except Exception as e:
            print(f"Booking error: {str(e)}")
            if 'conn' in locals():
                conn.close()
            return f"Error processing booking: {str(e)}"

    def handle_message(self, message, reset_state=False):
        """Handle incoming messages and process bookings."""
        message = message.strip().lower()
        print(f"\n=== Handling Message ===")
        print(f"Message: {message}")
        
        if reset_state:
            self.reset_context()
        
        if 'book' in message and 'tickets for' in message and 'at' in message and 'on' in message:
            movie, multiplex, quantity, category, seats, time, is_cancel, booking_date, is_booking = self.extract_entities(message)
            print(f"Complete booking check: movie={movie}, multiplex={multiplex}, quantity={quantity}, category={category}, time={time}, booking_date={booking_date}")
            if movie and multiplex and quantity and category and time and booking_date:
                self.context.update({
                    'movie': movie,
                    'multiplex': multiplex,
                    'quantity': quantity,
                    'category': category,
                    'seats': seats,
                    'time': time,
                    'booking_date': booking_date,
                    'is_cancel': is_cancel
                })
                return self.process_booking()
            else:
                print("Incomplete booking data, falling back to conversational flow")
        
        if any(word in message for word in ['help', 'what can you do', 'options']):
            return "I can help you with:\n1. Viewing available movies\n2. Booking tickets\n3. Cancelling bookings\n4. Checking showtimes\nWhat would you like to do?"
        
        if any(word in message for word in ['movies', 'what movies', 'list movies']):
            return f"Available movies: {', '.join(self.available_movies)}"
        
        movie, multiplex, quantity, category, seats, time, is_cancel, booking_date, is_booking = self.extract_entities(message)
        
        # Clear time, category, booking_date if movie changes
        if movie and movie != self.context['movie']:
            print(f"Movie changed from {self.context['movie']} to {movie}, clearing time, category, booking_date")
            self.context['time'] = None
            self.context['category'] = None
            self.context['booking_date'] = None
        
        if movie:
            self.context['movie'] = movie
        if multiplex:
            self.context['multiplex'] = multiplex
        if quantity:
            self.context['quantity'] = quantity
        if category:
            self.context['category'] = category
        if seats:
            self.context['seats'] = seats
        if time:
            self.context['time'] = time
        if is_cancel:
            self.context['is_cancel'] = is_cancel
        if booking_date:
            self.context['booking_date'] = booking_date
        
        print(f"Updated context: {self.context}")
        
        if is_cancel:
            self.reset_context()
            return "Cancellation is not fully implemented yet. Please provide more details to cancel a booking."
        
        if self.state == 'confirm_booking':
            if 'yes' in message:
                result = self.process_booking()
                self.reset_context()
                return result
            elif 'no' in message:
                self.reset_context()
                return "Booking cancelled. How can I help you?"
            else:
                return "Please type 'yes' to confirm or 'no' to cancel the booking."
        
        # Handle state-specific inputs
        if self.state == 'ask_movie' and (movie or quantity):
            if movie:
                self.context['movie'] = movie
            if quantity:
                self.context['quantity'] = quantity
            if self.context['movie'] and self.context['multiplex'] and self.context['quantity']:
                showtimes = self.get_showtimes(self.context['multiplex'], self.context['movie'], 'Elite')
                if showtimes:
                    self.state = 'ask_time'
                    return f"Got it, you want {self.context['quantity']} tickets for {self.context['movie']} at {self.context['multiplex']}. What time would you like? Available showtimes: {', '.join(showtimes)}"
                else:
                    self.reset_context()
                    return f"No showtimes available for {self.context['movie']} at {self.context['multiplex']}. Try another multiplex or movie."
            elif self.context['movie']:
                multiplexes = self.get_multiplexes_for_movie(self.context['movie'])
                if multiplexes:
                    self.state = 'ask_multiplex'
                    return f"Got it, you want tickets for {self.context['movie']}. Which multiplex would you like? Available: {', '.join(multiplexes)}"
                else:
                    self.reset_context()
                    return f"Sorry, {self.context['movie']} is not playing at any multiplex. Available movies: {', '.join(self.available_movies)}"
        
        if self.state == 'ask_time' and time:
            self.context['time'] = time
            showtimes = self.get_showtimes(self.context['multiplex'], self.context['movie'], 'Elite')
            showtime_24hr = [datetime.strptime(t, '%I:%M %p').strftime('%H:%M:%S') for t in showtimes]
            if self.context['time'] in showtime_24hr:
                self.state = 'ask_category'
                time_obj = datetime.strptime(self.context['time'], '%H:%M:%S')
                formatted_time = time_obj.strftime('%I:%M %p')
                return f"Got it, you want {self.context['quantity']} tickets for {self.context['movie']} at {self.context['multiplex']} at {formatted_time}. Which category would you like? Options: Elite, Economy"
            else:
                closest_time = self.find_closest_time(self.context['time'], showtimes)
                if closest_time:
                    self.context['time'] = closest_time
                    self.state = 'ask_category'
                    time_obj = datetime.strptime(closest_time, '%H:%M:%S')
                    formatted_time = time_obj.strftime('%I:%M %p')
                    return f"No exact showtime at {message}. Closest is {formatted_time}. Which category would you like for {self.context['quantity']} tickets for {self.context['movie']} at {self.context['multiplex']}? Options: Elite, Economy"
                else:
                    return f"Please specify a valid showtime. Available: {', '.join(showtimes)}"
        
        if self.state == 'ask_category' and category:
            self.context['category'] = category
            if self.context['movie'] and self.context['multiplex'] and self.context['time'] and self.context['quantity'] and self.context['category']:
                self.state = 'ask_date'
                dates = self.get_dates()
                time_obj = datetime.strptime(self.context['time'], '%H:%M:%S')
                formatted_time = time_obj.strftime('%I:%M %p')
                return f"Got it, you want {self.context['quantity']} {self.context['category']} tickets for {self.context['movie']} at {self.context['multiplex']} at {formatted_time}. On which date? Available: {', '.join(dates)}"
            else:
                return f"Please provide all booking details. Current context: {self.context}"
        
        if self.state == 'ask_date' and booking_date:
            self.context['booking_date'] = booking_date
            if self.context['movie'] and self.context['multiplex'] and self.context['time'] and self.context['quantity'] and self.context['category'] and self.context['booking_date']:
                self.state = 'confirm_booking'
                time_obj = datetime.strptime(self.context['time'], '%H:%M:%S')
                formatted_time = time_obj.strftime('%I:%M %p')
                date_display = datetime.strptime(self.context['booking_date'], '%Y-%m-%d').strftime('%a %d %b').upper()
                return f"Please confirm your booking:\nMovie: {self.context['movie']}\nMultiplex: {self.context['multiplex']}\nTime: {formatted_time}\nDate: {date_display}\nCategory: {self.context['category']}\nQuantity: {self.context['quantity']}\nType 'yes' to confirm or 'no' to cancel."
            else:
                return f"Please provide all booking details. Current context: {self.context}"
        
        if is_booking:
            if self.context['movie'] and self.context['quantity']:
                if not self.context['multiplex']:
                    multiplexes = self.get_multiplexes_for_movie(self.context['movie'])
                    if multiplexes:
                        self.state = 'ask_multiplex'
                        return f"Got it, you want {self.context['quantity']} tickets for {self.context['movie']}. Which multiplex would you like? Available: {', '.join(multiplexes)}"
                    else:
                        self.reset_context()
                        return f"Sorry, {self.context['movie']} is not playing at any multiplex. Available movies: {', '.join(self.available_movies)}"
                elif self.context['multiplex'] and not self.context['time']:
                    showtimes = self.get_showtimes(self.context['multiplex'], self.context['movie'], 'Elite')
                    if showtimes:
                        self.state = 'ask_time'
                        return f"Got it, you want {self.context['quantity']} tickets for {self.context['movie']} at {self.context['multiplex']}. What time would you like? Available showtimes: {', '.join(showtimes)}"
                    else:
                        self.reset_context()
                        return f"No showtimes available for {self.context['movie']} at {self.context['multiplex']}. Try another multiplex or movie."
                elif self.context['multiplex'] and self.context['time'] and not self.context['category']:
                    showtimes = self.get_showtimes(self.context['multiplex'], self.context['movie'], 'Elite')
                    showtime_24hr = [datetime.strptime(t, '%I:%M %p').strftime('%H:%M:%S') for t in showtimes]
                    if self.context['time'] in showtime_24hr:
                        self.state = 'ask_category'
                        time_obj = datetime.strptime(self.context['time'], '%H:%M:%S')
                        formatted_time = time_obj.strftime('%I:%M %p')
                        return f"Got it, you want {self.context['quantity']} tickets for {self.context['movie']} at {self.context['multiplex']} at {formatted_time}. Which category would you like? Options: Elite, Economy"
                    else:
                        closest_time = self.find_closest_time(self.context['time'], showtimes)
                        if closest_time:
                            self.context['time'] = closest_time
                            self.state = 'ask_category'
                            time_obj = datetime.strptime(closest_time, '%H:%M:%S')
                            formatted_time = time_obj.strftime('%I:%M %p')
                            return f"No exact showtime at {message}. Closest is {formatted_time}. Which category would you like for {self.context['quantity']} tickets for {self.context['movie']} at {self.context['multiplex']}? Options: Elite, Economy"
                        else:
                            return f"Please specify a valid showtime. Available: {', '.join(showtimes)}"
                elif self.context['multiplex'] and self.context['time'] and self.context['category'] and not self.context['booking_date']:
                    self.state = 'ask_date'
                    dates = self.get_dates()
                    time_obj = datetime.strptime(self.context['time'], '%H:%M:%S')
                    formatted_time = time_obj.strftime('%I:%M %p')
                    return f"Got it, you want {self.context['quantity']} {self.context['category']} tickets for {self.context['movie']} at {self.context['multiplex']} at {formatted_time}. On which date? Available: {', '.join(dates)}"
                elif self.context['multiplex'] and self.context['time'] and self.context['category'] and self.context['booking_date']:
                    self.state = 'confirm_booking'
                    time_obj = datetime.strptime(self.context['time'], '%H:%M:%S')
                    formatted_time = time_obj.strftime('%I:%M %p')
                    date_display = datetime.strptime(self.context['booking_date'], '%Y-%m-%d').strftime('%a %d %b').upper()
                    return f"Please confirm your booking:\nMovie: {self.context['movie']}\nMultiplex: {self.context['multiplex']}\nTime: {formatted_time}\nDate: {date_display}\nCategory: {self.context['category']}\nQuantity: {self.context['quantity']}\nType 'yes' to confirm or 'no' to cancel."
            elif self.context['multiplex'] and self.context['quantity']:
                self.state = 'ask_movie'
                return f"Got it, you want {self.context['quantity']} tickets at {self.context['multiplex']}. Which movie would you like? Available: {', '.join(self.available_movies)}"
            elif self.context['quantity']:
                self.state = 'ask_movie'
                return f"Got it, you want {self.context['quantity']} tickets. Which movie would you like? Available: {', '.join(self.available_movies)}"
            elif self.context['movie']:
                multiplexes = self.get_multiplexes_for_movie(self.context['movie'])
                if multiplexes:
                    self.state = 'ask_multiplex'
                    return f"Got it, you want tickets for {self.context['movie']}. Which multiplex would you like? Available: {', '.join(multiplexes)}"
                else:
                    self.reset_context()
                    return f"Sorry, {self.context['movie']} is not playing at any multiplex. Available movies: {', '.join(self.available_movies)}"
            else:
                return f"Please specify a movie or number of tickets to start booking. Available movies: {', '.join(self.available_movies)}"
        
        # Handle non-booking inputs with context
        if self.context['movie'] and self.context['multiplex'] and self.context['quantity'] and self.context['time'] and self.context['category']:
            if booking_date:
                self.context['booking_date'] = booking_date
                self.state = 'confirm_booking'
                time_obj = datetime.strptime(self.context['time'], '%H:%M:%S')
                formatted_time = time_obj.strftime('%I:%M %p')
                date_display = datetime.strptime(self.context['booking_date'], '%Y-%m-%d').strftime('%a %d %b').upper()
                return f"Please confirm your booking:\nMovie: {self.context['movie']}\nMultiplex: {self.context['multiplex']}\nTime: {formatted_time}\nDate: {date_display}\nCategory: {self.context['category']}\nQuantity: {self.context['quantity']}\nType 'yes' to confirm or 'no' to cancel."
            elif category:
                self.context['category'] = category
                self.state = 'ask_date'
                dates = self.get_dates()
                time_obj = datetime.strptime(self.context['time'], '%H:%M:%S')
                formatted_time = time_obj.strftime('%I:%M %p')
                return f"Got it, you want {self.context['quantity']} {self.context['category']} tickets for {self.context['movie']} at {self.context['multiplex']} at {formatted_time}. On which date? Available: {', '.join(dates)}"
        
        if self.context['movie'] and self.context['multiplex'] and self.context['quantity'] and self.context['time']:
            if category:
                self.context['category'] = category
                self.state = 'ask_date'
                dates = self.get_dates()
                time_obj = datetime.strptime(self.context['time'], '%H:%M:%S')
                formatted_time = time_obj.strftime('%I:%M %p')
                return f"Got it, you want {self.context['quantity']} {self.context['category']} tickets for {self.context['movie']} at {self.context['multiplex']} at {formatted_time}. On which date? Available: {', '.join(dates)}"
            elif time:
                self.context['time'] = time
                showtimes = self.get_showtimes(self.context['multiplex'], self.context['movie'], 'Elite')
                showtime_24hr = [datetime.strptime(t, '%I:%M %p').strftime('%H:%M:%S') for t in showtimes]
                if self.context['time'] in showtime_24hr:
                    self.state = 'ask_category'
                    time_obj = datetime.strptime(self.context['time'], '%H:%M:%S')
                    formatted_time = time_obj.strftime('%I:%M %p')
                    return f"Got it, you want {self.context['quantity']} tickets for {self.context['movie']} at {self.context['multiplex']} at {formatted_time}. Which category would you like? Options: Elite, Economy"
                else:
                    closest_time = self.find_closest_time(self.context['time'], showtimes)
                    if closest_time:
                        self.context['time'] = closest_time
                        self.state = 'ask_category'
                        time_obj = datetime.strptime(closest_time, '%H:%M:%S')
                        formatted_time = time_obj.strftime('%I:%M %p')
                        return f"No exact showtime at {message}. Closest is {formatted_time}. Which category would you like for {self.context['quantity']} tickets for {self.context['movie']} at {self.context['multiplex']}? Options: Elite, Economy"
                    else:
                        return f"Please specify a valid showtime. Available: {', '.join(showtimes)}"
        
        if self.context['movie'] and self.context['multiplex'] and self.context['quantity']:
            if movie:
                self.context['movie'] = movie
                showtimes = self.get_showtimes(self.context['multiplex'], self.context['movie'], 'Elite')
                if showtimes:
                    self.state = 'ask_time'
                    return f"Got it, you want {self.context['quantity']} tickets for {self.context['movie']} at {self.context['multiplex']}. What time would you like? Available showtimes: {', '.join(showtimes)}"
                else:
                    self.reset_context()
                    return f"No showtimes available for {self.context['movie']} at {self.context['multiplex']}. Try another multiplex or movie."
            elif quantity:
                self.context['quantity'] = quantity
                return f"Got it, you want {self.context['quantity']} tickets for {self.context['movie']} at {self.context['multiplex']}. What time would you like? Available showtimes: {', '.join(self.get_showtimes(self.context['multiplex'], self.context['movie'], 'Elite'))}"
        
        if self.context['multiplex'] and self.context['quantity']:
            if movie:
                self.context['movie'] = movie
                showtimes = self.get_showtimes(self.context['multiplex'], self.context['movie'], 'Elite')
                if showtimes:
                    self.state = 'ask_time'
                    return f"Got it, you want {self.context['quantity']} tickets for {self.context['movie']} at {self.context['multiplex']}. What time would you like? Available showtimes: {', '.join(showtimes)}"
                else:
                    self.reset_context()
                    return f"No showtimes available for {self.context['movie']} at {self.context['multiplex']}. Try another multiplex or movie."
            elif quantity:
                self.context['quantity'] = quantity
                return f"Got it, you want {self.context['quantity']} tickets at {self.context['multiplex']}. Which movie would you like? Available: {', '.join(self.available_movies)}"
        
        return f"I'm not sure I understand. Please specify a movie or number of tickets to start booking. Available movies: {', '.join(self.available_movies)}"

def chatbot_interface(message, reset_state=False):
    """Interface to interact with the chatbot."""
    if not hasattr(chatbot_interface, 'bot'):
        chatbot_interface.bot = Chatbot()
    return chatbot_interface.bot.handle_message(message, reset_state)

def report_booked_seats():
    """Report booked seats from the database."""
    return database.report_seat_availability()