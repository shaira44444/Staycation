import math
from flask import Flask, render_template, request, abort, session, redirect, url_for, flash, redirect, url_for
# This import is necessary for the CATEGORY_CHOICES in NewBookForm
from books_data import ALL_CATEGORIES 
# RESTORED: Import book_model, user_model, and loan_model instance/module
from models import book_model, user_model, loan_model
from flask_wtf import FlaskForm
from wtforms import (
    StringField, TextAreaField, IntegerField, SelectMultipleField, SubmitField, 
    FieldList, FormField, SelectField
)
from wtforms.validators import DataRequired, URL, NumberRange, Optional, Length
from functools import wraps
import re # Import regex for number validation
# CORRECTED: Only one combined import line for datetime and timedelta, and one for random.
# We are importing the 'datetime' class from the 'datetime' module here.
from datetime import datetime, timedelta 
import random 

app = Flask(__name__)
# Secret key is REQUIRED for Flask sessions to work.
app.secret_key = 'your_hard-to-guess_secret_key_for_suss_library'

def get_description_paragraphs(description):
    """
    Splits the description and returns the first and last non-empty paragraphs.
    """
    paragraphs = [p.strip() + "." for p in description.split('.') if p.strip()]

    first_paragraph = paragraphs[0] if paragraphs else ""
    last_paragraph = ""

    if len(paragraphs) > 1 and first_paragraph != paragraphs[-1]:
        last_paragraph = paragraphs[-1]
    elif len(paragraphs) == 1:
        last_paragraph = ""

    return first_paragraph, last_paragraph

# --- Q3(c) Restored Helper Function for Frontend Logic (Using loan_model instance) ---
def check_active_loan(book_id, user_id):
    """
    Checks if the given user has an active, unreturned loan for the specified book 
    by querying the dedicated loans collection via loan_model.
    """
    if not user_id:
        return False
        
    # Access the loans collection directly through the loan_model instance
    # NOTE: Since the real model.py is using the loan_model instance for this check,
    # we must update this helper to use the method provided in the user's model.py.
    # The user's model.py provides: loan_model.has_active_loan(book_id, user_id)
    return loan_model.has_active_loan(book_id, user_id)
# --- END HELPER FUNCTION ---


# --- Q2(a) & Q2(b) Book Routes (UNCHANGED) ---

@app.route('/', methods=['GET', 'POST'])
@app.route('/books_titles', methods=['GET', 'POST'])
def books_titles():
    """Renders the Book Titles page, handling category search."""

    # Retrieve current user info from session for potential display/logic
    user_name = session.get('name')

    selected_category = 'All'

    if request.method == 'POST':
        selected_category = request.form.get('category_select', 'All')
    elif request.args.get('category'):
        selected_category = request.args.get('category')

    # Fetch data from MongoDB via the Book model
    filtered_books_from_db = book_model.get_all_books(category=selected_category)

    display_books = []
    for book in filtered_books_from_db:
        # Handling the potential change from 'author' string to 'authors' list
        if 'authors' in book and book['authors']:
            display_author = book['authors'][0]
        else:
            display_author = book.get('author', 'N/A')
            
        first_para, last_para = get_description_paragraphs(book.get('description', '')) # Added safety for missing description

        display_books.append({
            'id': book['id'],
            'title': book['title'],
            'author': display_author, # Display the primary author
            'category': book.get('category', 'General'), # Safely retrieve category
            'genres': book.get('genres', []),
            'pages': book.get('pages'),
            'first_para': first_para,
            'last_para': last_para,
            'image_file': book['image_file'],
            'num_copies': book.get('copies', 0),
            'available_copies': book.get('available', 0) # Mapped to {{ book.available_copies }}
        })

    return render_template(
        'books_titles.html',
        books=display_books,
        num_titles=len(display_books),
        categories=ALL_CATEGORIES,
        selected_category=selected_category,
        active_page='titles',
        user_name=user_name
    )


@app.route('/book/<string:book_id>')
def book_detail(book_id):
    """
    Displays the details of a single book. 
    Includes logic to determine if the book is currently borrowed by the user.
    """

    # Fetch book details from MongoDB
    selected_book = book_model.get_book_by_id(book_id)

    if selected_book is None:
        return abort(404)
    
    # Determine author(s) for display
    authors = selected_book.get('authors')
    if authors and isinstance(authors, list):
        display_author = ", ".join(authors) # Join all authors for detail page
    else:
        display_author = selected_book.get('author', 'Unknown')
    
    # LOGIC FOR Q3(c): Check loan status for the currently logged-in user
    user_id = session.get('user_id')
    # Use the corrected helper function
    has_active_loan = check_active_loan(book_id, user_id) 
    # END NEW LOGIC

    all_paragraphs = [p.strip() + "." for p in selected_book.get('description', '').split('.') if p.strip()]

    display_data = {
        'id': book_id, # Add book ID to display data for button links
        'title': selected_book['title'],
        'author': display_author,
        'category': selected_book.get('category', 'General'),
        'genres': selected_book.get('genres', []),
        'pages': selected_book.get('pages'),
        'image_file': selected_book['image_file'],
        'description_paragraphs': all_paragraphs,
        'copies': selected_book.get('copies', 1),
        'available': selected_book.get('available', 1)
    }

    return render_template('book_detail.html', 
                             book=display_data, 
                             active_page='detail',
                             has_active_loan=has_active_loan # Pass status to template
                          )


def login_required(f):
    """Decorator to restrict access to authenticated users."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """Decorator to restrict access to admin users only."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('is_admin'):
            flash('Access denied. Only administrators can use this function.', 'danger')
            return redirect(url_for('books_titles'))
        return f(*args, **kwargs)
    return decorated_function


# --- Q3(c) Borrowing a book (FIX APPLIED HERE) ---
@app.route('/make_loan/<string:book_id>')
@login_required 
def make_loan(book_id):
    """
    Handles the process of a user borrowing a book.
    Calculates the random past borrow date and passes it to the model.
    """
    user_id = session.get('user_id')
    
    # --- FIX: Calculate the borrow date 10 to 20 days before today ---
    random_days = random.randint(10, 20)
    # The 'datetime' used here now correctly refers to the class imported at the top.
    borrow_date_in_past = datetime.now() - timedelta(days=random_days)
    
    # Pass the calculated date to create_loan so models.py doesn't default to today
    success, message = loan_model.create_loan(book_id, user_id, borrow_date=borrow_date_in_past)

    if success:
        flash(message, 'success')
    else:
        flash(f"Loan failed: {message}", 'danger') 
        
    return redirect(url_for('book_detail', book_id=book_id))


# --- Q3(c) Returning a book (ROUTE ACCEPTS POST) ---
@app.route('/return_loan/<string:loan_id>', methods=['POST'])
@login_required 
def return_loan(loan_id):
    """
    Handles the process of a user returning a book. 
    Uses the loan_id from the my_loans page.
    """
    success, message = loan_model.return_loan(loan_id)

    if success:
        flash(message, 'success')
    else:
        # Debugging message if the model function fails
        print(f"DEBUG: loan_model.return_loan('{loan_id}') failed. Message: {message}")
        flash(f"Return failed: {message}", 'danger') 
        
    return redirect(url_for('my_loans'))


# --- Q3(c) Loan-related Functions for non-admin users (my_loans) ---

@app.route('/my_loans')
@login_required
def my_loans():
    """
    Retrieves and displays all loans (active and returned) for the current user.
    Includes date formatting fix from previous steps.
    """
    user_id = session.get('user_id')
    
    # Retrieve all loans for the user
    all_loans = loan_model.get_user_loans(user_id)
    
    # Format dates and determine status for template display
    for loan in all_loans:
        
        # Ensure that old or corrupted loan records have a default renew_count of 0.
        if 'renew_count' not in loan:
            loan['renew_count'] = 0
        
        try:
            # Ensure the key exists before attempting to access/format it
            borrow_date = loan.get('borrow_date')
            due_date = loan.get('due_date')
            return_date = loan.get('return_date')

            # --- Date format fix: 'dd Mon YYYY' (e.g., '19 Aug 2025') ---
            loan['borrow_date_formatted'] = borrow_date.strftime('%d %b %Y') if borrow_date else 'N/A'
            loan['due_date_formatted'] = due_date.strftime('%d %b %Y') if due_date else 'N/A'
            loan['return_date_formatted'] = return_date.strftime('%d %b %Y') if return_date else 'N/A'
            # ----------------------------------------------------------------------
            
        except AttributeError:
             # Fallback if dates are strings or other non-datetime types
            loan['borrow_date_formatted'] = str(loan.get('borrow_date', 'N/A'))
            loan['due_date_formatted'] = str(loan.get('due_date', 'N/A'))
            loan['return_date_formatted'] = str(loan.get('return_date', 'N/A'))

        # Standard status checks
        loan['is_active'] = loan.get('return_date') is None
        loan['is_overdue'] = loan['is_active'] and loan.get('due_date') and loan['due_date'] < datetime.now()
        loan['can_renew'] = loan['is_active'] and loan.get('renew_count', 0) < 2
        loan['can_return'] = loan['is_active'] 
        # --- FIX: Only allow deletion if the loan is NOT active (i.e., it has been returned) ---
        loan['can_delete'] = not loan['is_active']


    return render_template('my_loans.html', 
                            loans=all_loans, 
                            active_page='my_loans', 
                            user_name=session.get('name'))


@app.route('/renew_loan/<string:loan_id>')
@login_required
def renew_loan(loan_id):
    """
    Handles loan renewal, updating the renew count and borrow date.
    """
    success, message = loan_model.renew_loan(loan_id)

    if success:
        flash(message, 'success')
    else:
        flash(f"Renewal failed: {message}", 'danger')
        
    return redirect(url_for('my_loans'))


# --- FIX: Added methods=['POST'] to accept form submission ---
@app.route('/delete_loan/<string:loan_id>', methods=['POST'])
@login_required
def delete_loan(loan_id):
    """
    Handles loan deletion.
    - Only loans that have been returned can be deleted.
    """
    success, message = loan_model.delete_loan(loan_id)

    if success:
        flash(message, 'success')
    else:
        # Debugging message if the model function fails
        print(f"DEBUG: loan_model.delete_loan('{loan_id}') failed. Message: {message}")
        flash(f"Deletion failed: {message}", 'danger')
        
    return redirect(url_for('my_loans'))

# --- Q2(c) Authentication Routes (UNCHANGED) ---

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Handles user registration."""
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        name = request.form.get('name')

        if not all([email, password, name]):
            flash('All fields are required.', 'error')
            return render_template('register.html', active_page='register')

        # Attempt to register the user via the User model
        user_id = user_model.register_user(email, password, name)

        if user_id:
            session['user_id'] = user_id
            session['name'] = name

            # Check if this seeded user is the admin (a quick fix for this TMA structure)
            is_admin = (email == 'admin@lib.sg')
            session['is_admin'] = is_admin
            
            flash(f'Registration successful! Welcome, {name}.', 'success')
            return redirect(url_for('books_titles'))
        else:
            flash('Registration failed: Email already in use.', 'error')

    return render_template('register.html', active_page='register')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handles user login."""
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user_doc = user_model.find_user_by_email(email)

        if user_doc and user_model.check_password(user_doc, password):
            session['user_id'] = user_doc['id']
            session['name'] = user_doc['name']

            is_admin = (user_doc['email'] == 'admin@lib.sg')
            session['is_admin'] = is_admin

            flash(f'Login successful! Welcome back, {user_doc["name"]}.', 'success')
            return redirect(url_for('books_titles'))
        else:
            flash('Login failed. Check your email and password.', 'error')

    return render_template('login.html', active_page='login')


@app.route('/logout')
def logout():
    """Logs out the user by clearing the session."""
    session.pop('user_id', None)
    session.pop('name', None)
    session.pop('is_admin', None)
    flash('You have been logged out.', 'info')

    return redirect(url_for('books_titles'))


GENRE_CHOICES = [
    ("Animals", "Animals"), ("Business", "Business"), ("Comics", "Comics"),
    ("Communication", "Communication"), ("Dark Academia", "Dark Academia"),
    ("Emotion", "Emotion"), ("Fantasy", "Fantasy"), ("Fiction", "Fiction"),
    ("Friendship", "Friendship"), ("Graphic Novels", "Graphic Novels"),
    ("Grief", "Grief"), ("Historical Fiction", "Historical Fiction"),
    ("Indigenous", "Indigenous"), ("Inspirational", "Inspirational"),
    ("Magic", "Magic"), ("Mental Health", "Mental Health"),
    ("Nonfiction", "Nonfiction"), ("Personal Development", "Personal Development"),
    ("Philosophy", "Philosophy"), ("Picture Books", "Picture Books"),
    ("Poetry", "Poetry"), ("Productivity", "Productivity"),
    ("Psychology", "Psychology"), ("Romance", "Romance"),
    ("School", "School"), ("Self Help", "Self Help")
]

# Create choices list for the Category SelectField
from books_data import ALL_CATEGORIES # Re-imported to ensure it's available
CATEGORY_CHOICES = [(c, c) for c in ALL_CATEGORIES]


# --- Dynamic Author Form for FieldList ---
class SimpleAuthorForm(FlaskForm):
    # This field name must match the one used in the HTML: author_field.author_name
    author_name = StringField('Author Name', validators=[Optional(), Length(max=100)])


class NewBookForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(max=255)])
    
    # REPLACED: FieldList for dynamic author input (Bonus Implementation)
    authors_text = FieldList(
        FormField(SimpleAuthorForm),
        min_entries=1, # Ensures at least one author field is always displayed
        label='Book Authors'
    ) 

    cover_image = StringField('Cover Image Filename (e.g., cover1.jpg)', validators=[DataRequired(), Length(max=255)])
    isbn = StringField('ISBN', validators=[Optional(), Length(max=20)])
    publication_year = IntegerField('Publication Year',
                                     validators=[Optional(), NumberRange(min=1000, max=2025)],
                                     render_kw={"placeholder": "e.g., 2024"})
    genres = SelectMultipleField('Genres (Hold Ctrl/Cmd to select multiple)',
                                     choices=GENRE_CHOICES,
                                     validators=[Optional()])
    publisher = StringField('Publisher', validators=[Optional(), Length(max=100)])
    description = TextAreaField('Description', validators=[DataRequired()])
    page_count = IntegerField('Page Count', validators=[Optional(), NumberRange(min=1)])
    
    # NEW FIELDS FOR Q2(b)
    category = SelectField('Category', choices=CATEGORY_CHOICES, validators=[DataRequired()])
    copies = IntegerField('Total Copies', validators=[DataRequired(), NumberRange(min=1)], default=1)
    available = IntegerField('Available Copies', validators=[DataRequired(), NumberRange(min=0)], default=1)
    # END NEW FIELDS
    
    submit = SubmitField('Submit Book')


@app.route('/new_book', methods=['GET', 'POST'])
@login_required
@admin_required
def new_book():
    """Handles the display and submission of the Add New Book form, including dynamic author fields."""
    form = NewBookForm()

    # ----------------------------------------------------------------------
    # STEP 1: Handle dynamic 'Add Author' button press
    # ----------------------------------------------------------------------
    if request.method == 'POST' and 'add_author' in request.form:
        form.authors_text.append_entry()
        # Ensure the current form data is loaded back before rendering the template
        form.process()
        return render_template('new_book.html', form=form, active_page='new_book')

    # ----------------------------------------------------------------------
    # STEP 2: Handle form submission (validation and database insert)
    # ----------------------------------------------------------------------
    if form.validate_on_submit():
        # 1. Extract authors from the FieldList, filtering out empty entries
        authors = [
            field.author_name.data.strip() 
            for field in form.authors_text.entries 
            if field.author_name.data and field.author_name.data.strip()
        ]
        
        if not authors:
            flash('At least one author name is required.', 'danger')
            return render_template('new_book.html', form=form, active_page='new_book')
            
        # 2. Call the Book model method to add the new book
        success, message = book_model.add_new_book(
            title=form.title.data,
            authors=authors,
            cover_image=form.cover_image.data,
            isbn=form.isbn.data,
            publication_year=form.publication_year.data,
            genres=form.genres.data,
            publisher=form.publisher.data,
            description=form.description.data,
            page_count=form.page_count.data,
            # NEW fields
            category=form.category.data, 
            copies=form.copies.data, 
            available=form.available.data 
        )
        
        if success:
            flash(message, 'success')
            return redirect(url_for('books_titles'))
        else:
            flash(f'Failed to add book: {message}', 'danger')


    # ----------------------------------------------------------------------
    # STEP 3: Initial GET request or validation failure
    # ----------------------------------------------------------------------
    return render_template('new_book.html', form=form, active_page='new_book')
