# app.py (Modified)

import math
# --- CHANGES: Import the Book model instance instead of the raw data ---
from flask import Flask, render_template, request, abort 
from books_data import ALL_CATEGORIES # Still use categories list
from models import book_model          # <-- NEW: Import the MongoDB model instance
# --- END CHANGES ---

app = Flask(__name__)

def get_description_paragraphs(description):
    # ... (Keep this function as is from Q2(a) for description formatting) ...
    """
    Splits the description and returns the first and last non-empty paragraphs,
    as required by the prompt's visual style. (Used for the main list page)
    """
    # Split the description by periods, filtering out empty strings, and re-adding the period
    paragraphs = [p.strip() + "." for p in description.split('.') if p.strip()]

    first_paragraph = paragraphs[0] if paragraphs else ""
    last_paragraph = ""

    # Check if there's more than one paragraph, and if the last is different from the first
    if len(paragraphs) > 1 and first_paragraph != paragraphs[-1]:
        # NOTE: Using the last paragraph for the second description block
        last_paragraph = paragraphs[-1] 
    # If the first and last are the same (only one short paragraph), we don't repeat it
    elif len(paragraphs) == 1:
        last_paragraph = ""

    return first_paragraph, last_paragraph


# Set the homepage and the explicit Book Titles link to this function
@app.route('/', methods=['GET', 'POST'])
@app.route('/books_titles', methods=['GET', 'POST'])
def books_titles():
    # --- Handle Category Search/Filter (Category logic remains the same) ---
    selected_category = 'All'
    
    if request.method == 'POST':
        selected_category = request.form.get('category_select', 'All')
    elif request.args.get('category'):
        selected_category = request.args.get('category')
        
    # --- CHANGES: Fetch data from MongoDB via the Book model ---
    # Call the model method to get all books, sorted and filtered
    filtered_books_from_db = book_model.get_all_books(category=selected_category) 
    # --- END CHANGES ---

    display_books = []
    for book in filtered_books_from_db: # Loop over the data from MongoDB
        # book['description'] is now a string from the DB document
        first_para, last_para = get_description_paragraphs(book['description'])
        
        display_books.append({
            # book['id'] is now the string representation of MongoDB's _id
            'id': book['id'], 
            'title': book['title'],
            # 'author' and 'genres' are already formatted as strings in the model's get_all_books()
            'author': book['author'], 
            'category': book['category'],
            'genres': book['genres'], 
            'pages': book['pages'],
            'first_para': first_para,
            'last_para': last_para,
            'image_file': book['image_file']
        })

    # Render the list template
    return render_template(
        'books_titles.html',
        books=display_books,
        num_titles=len(display_books),
        categories=ALL_CATEGORIES,
        selected_category=selected_category
    )


# --- CHANGES: Change the route parameter type from <int:book_id> to <string:book_id> ---
# MongoDB uses a string-based ObjectId, so the URL must now accept a string.
@app.route('/book/<string:book_id>') 
def book_detail(book_id):
    """Displays the details of a single book based on its ID (MongoDB ObjectId string)."""
    
    # --- CHANGES: Find the book by its string ID using the Book model ---
    selected_book = book_model.get_book_by_id(book_id)
    # --- END CHANGES ---
    
    # If the book is not found (ID doesn't exist or is invalid), return a 404 error
    if selected_book is None:
        # NOTE: The model handles converting the string to ObjectId and searching
        return abort(404)

    # Process all description paragraphs for the detail template
    # selected_book['description'] is a string from the DB
    all_paragraphs = [p.strip() + "." for p in selected_book['description'].split('.') if p.strip()]

    # Prepare data structure for the book_detail.html template
    display_data = {
        'title': selected_book['title'],
        # 'author' and 'genres' are already formatted as strings in the model's get_book_by_id()
        'author': selected_book['author'], 
        'category': selected_book['category'],
        'genres': selected_book['genres'], 
        'pages': selected_book['pages'],
        'image_file': selected_book['image_file'],
        'description_paragraphs': all_paragraphs,
        # 'copies' and 'available' are stored directly in the DB document
        'copies': selected_book.get('copies', 1),  
        'available': selected_book.get('available', 1)
    }
    
    # Render the new detail template
    return render_template('book_detail.html', book=display_data)


if __name__ == '__main__':
    # Initialize the model to ensure data seeding happens when the app runs
    book_model
    app.run(debug=True)