import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import gradio as gr
from chatbot import chatbot_interface
from database import report_seat_availability, get_showtimes, get_movies, get_multiplexes_for_movie
from datetime import datetime, timedelta

def get_dates():
    """Generate the next 7 days starting from the current date."""
    today = datetime.now().date()
    dates = [(today + timedelta(days=i)).strftime("%a %d %b").upper() for i in range(7)]
    return dates

def parse_date(date_str):
    """Convert date string (e.g., 'SAT 03 MAY') to YYYY-MM-DD format."""
    date_obj = datetime.strptime(date_str, "%a %d %b")
    date_obj = date_obj.replace(year=2025)
    return date_obj.strftime("%Y-%m-%d")

def validate_booking(movie, multiplex, showtime, category, quantity):
    """Validate booking parameters and return error message if any."""
    if not movie:
        return "Please select a movie."
    if not multiplex:
        return "Please select a multiplex."
    if not showtime or showtime == "No showtimes available":
        return "Please select a valid showtime."
    if not category:
        return "Please select a seat category."
    if quantity < 1:
        return "Please select at least one ticket."
    if quantity > 10:
        return "Maximum 10 tickets can be booked at once."
    return None

def book_with_selections(movie, multiplex, date, showtime, category, quantity):
    """Handle booking through the UI form."""
    print("\n=== UI Booking Details ===")
    print(f"Movie: {movie}")
    print(f"Multiplex: {multiplex}")
    print(f"Date: {date}")
    print(f"Showtime: {showtime}")
    print(f"Category: {category}")
    print(f"Quantity: {quantity}")
    print("==============================\n")

    error = validate_booking(movie, multiplex, showtime, category, quantity)
    if error:
        print(f"Validation error: {error}")
        return error

    try:
        formatted_time = showtime
        print(f"Using showtime: {formatted_time}")
        input_text = f"book {quantity} {category} tickets for {movie} at {multiplex} at {formatted_time} on {date}"
        print(f"UI Booking request: {input_text}")
        result = chatbot_interface(input_text, reset_state=True)
        print(f"Chatbot response: {result}")
        if "Successfully booked" in result:
            response = f"✅ {result}"
        elif "No showtime found" in result:
            response = f"❌ {result}\n\nPlease try a different showtime."
        elif "Not enough seats available" in result:
            response = f"❌ {result}\n\nPlease try with fewer tickets or a different showtime."
        else:
            response = f"❌ {result}"
        print(f"Final response: {response}")
        return response
    except Exception as e:
        error_msg = f"❌ An error occurred while processing your booking. Please try again.\nError: {str(e)}"
        print(f"Error during booking: {error_msg}")
        return error_msg

def get_summary():
    """Return the summary of booked seats."""
    return report_seat_availability()

def update_multiplexes(movie):
    """Update multiplex options based on selected movie."""
    multiplexes = get_multiplexes_for_movie(movie)
    return gr.update(choices=multiplexes, value=multiplexes[0] if multiplexes else None)

def update_showtimes(movie, multiplex, category):
    """Update showtime options based on selected movie, multiplex, and category."""
    showtimes = get_showtimes(multiplex, movie, category)
    if not showtimes:
        return gr.update(choices=["No showtimes available"], value=None, interactive=False)
    return gr.update(choices=showtimes, value=showtimes[0], interactive=True)

def chat_with_bot(message):
    """Handle chat with the bot and clear the input."""
    print("\n=== Chatbot Message ===")
    print(f"User message: {message}")
    response = chatbot_interface(message, reset_state=False)
    print(f"Bot response: {response}")
    print("==============================\n")
    return response, ""

with gr.Blocks(css="styles.css") as demo:
    gr.Markdown("# Movie Booking Chatbot")
    with gr.Column():
        gr.Markdown("## Book Tickets")
        movies = get_movies()
        movie_input = gr.Dropdown(choices=movies, label="Select Movie", value=movies[0])
        dates = get_dates()
        with gr.Row():
            date_input = gr.Radio(choices=dates, value=dates[0], label="Select Date")
        with gr.Row():
            with gr.Column():
                initial_multiplexes = get_multiplexes_for_movie(movies[0])
                multiplex_input = gr.Dropdown(choices=initial_multiplexes, label="Select Multiplex", value=initial_multiplexes[0] if initial_multiplexes else None)
                category_input = gr.Dropdown(choices=["Elite", "Economy"], label="Select Category", value="Elite")
                quantity_input = gr.Slider(minimum=1, maximum=10, step=1, value=1, label="Number of Tickets")
                gr.Markdown("### Showtimes")
                with gr.Row():
                    initial_showtimes = get_showtimes(initial_multiplexes[0], movies[0], "Elite") if initial_multiplexes else []
                    showtime_input = gr.Radio(choices=initial_showtimes, value=initial_showtimes[0] if initial_showtimes else None, label="", interactive=True)
        submit_btn = gr.Button("Book Tickets", variant="primary")
        output = gr.Textbox(label="Booking Result")
    with gr.Column():
        gr.Markdown("## Chat with the Booking Assistant")
        gr.Markdown("You can type commands like:\n- 'Book 2 Elite tickets for Interstellar at Inox at 6:45 PM'\n- 'Show me available movies'\n- 'What can you do?'")
        chatbot_input = gr.Textbox(label="Your message", placeholder="Type your booking request here...")
        chatbot_output = gr.Textbox(label="Assistant Response")
        chat_btn = gr.Button("Send")
    summary_btn = gr.Button("Show Summary of Booked Seats")
    summary_output = gr.Textbox(label="Summary of Booked Seats")
    movie_input.change(fn=update_multiplexes, inputs=movie_input, outputs=multiplex_input).then(fn=update_showtimes, inputs=[movie_input, multiplex_input, category_input], outputs=showtime_input)
    multiplex_input.change(fn=update_showtimes, inputs=[movie_input, multiplex_input, category_input], outputs=showtime_input)
    category_input.change(fn=update_showtimes, inputs=[movie_input, multiplex_input, category_input], outputs=showtime_input)
    submit_btn.click(fn=book_with_selections, inputs=[movie_input, multiplex_input, date_input, showtime_input, category_input, quantity_input], outputs=output)
    chat_btn.click(fn=chat_with_bot, inputs=chatbot_input, outputs=[chatbot_output, chatbot_input])
    summary_btn.click(fn=get_summary, inputs=None, outputs=summary_output)

if __name__ == "__main__":
    demo.launch(server_name="localhost", server_port=7860)