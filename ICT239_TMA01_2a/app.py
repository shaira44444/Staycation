import math
from flask import Flask, render_template, request, abort 
from books_data import BOOKS, ALL_CATEGORIES

app = Flask(__name__)

def get_description_paragraphs(description):
    """
    Splits the description and returns the first and last non-empty paragraphs,
    as required by the prompt's visual style. (Used for the main list page)
    """
    # Split the description by periods, filtering out empty strings, and re-adding the period
    # Note: This is an imperfect way to split into display paragraphs, but matches the requirement for first/last block.
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
    # --- Handle Category Search/Filter ---
    selected_category = 'All'
    
    # 1. Get category from the POST form submission (when Search button is clicked)
    if request.method == 'POST':
        selected_category = request.form.get('category_select', 'All')
    
    # 2. Get category from URL query parameter (for persistence/testing)
    elif request.args.get('category'):
        selected_category = request.args.get('category')
        
    # --- Sorting and Filtering ---
    
    # Start with all books
    filtered_books = BOOKS
    
    # Sort all books by title (Requirement: sorted by their titles)
    filtered_books = sorted(filtered_books, key=lambda book: book['title'])

    # Apply the category filter
    if selected_category != 'All':
        filtered_books = [book for book in filtered_books if book['category'] == selected_category]

    display_books = []
    for book in filtered_books:
        first_para, last_para = get_description_paragraphs(book['description'])
        
        display_books.append({
            'id': book['id'], 
            'title': book['title'],
            'author': book['author'],
            'category': book['category'],
            'genres': ", ".join(book['genres']),
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


@app.route('/book/<int:book_id>') 
def book_detail(book_id):
    """Displays the details of a single book based on its ID."""
    
    # Find the book by its ID
    # 'next' iterates through the BOOKS list until it finds a match.
    selected_book = next((book for book in BOOKS if book.get('id') == book_id), None)
    
    # If the book is not found (ID doesn't exist), return a 404 error
    if selected_book is None:
        return abort(404)

    # Process all description paragraphs for the detail template
    # Splits the description into paragraphs based on periods
    all_paragraphs = [p.strip() + "." for p in selected_book['description'].split('.') if p.strip()]

    # Prepare data structure for the book_detail.html template
    display_data = {
        'title': selected_book['title'],
        'author': selected_book['author'],
        'category': selected_book['category'],
        'genres': ", ".join(selected_book['genres']),
        'pages': selected_book['pages'],
        'image_file': selected_book['image_file'],
        'description_paragraphs': all_paragraphs,
        # Hardcoding copies based on the image: "Copies: 1 Available: 1"
        'copies': 1,  
        'available': 1
    }
    
    # Render the new detail template
    return render_template('book_detail.html', book=display_data)


if __name__ == '__main__':
    app.run(debug=True)