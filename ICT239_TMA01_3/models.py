from pymongo import MongoClient
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
from books_data import BOOKS # Used for initial data seeding
from config import MONGODB_URI, DATABASE_NAME, COLLECTION_NAME, USER_COLLECTION_NAME
from bson.objectid import ObjectId
from datetime import datetime, timedelta
import random

# --- Common MongoDB Client Setup ---
client = MongoClient(MONGODB_URI)
db = client[DATABASE_NAME]

# --- Q4(c) NEW HELPER FUNCTION: Capped Random Date Generation ---

def get_capped_new_loan_date(original_date):
    """
    Calculates a new date for renewal or return. The date is a random time 
    between the original date and up to 3 days later, but is capped by 
    the current time (datetime.now()).
    
    This function is used to simulate a random, yet realistic, time delay 
    between the loan event and the actual update in the system.
    
    :param original_date: The starting datetime object (e.g., borrow_date).
    :return: A capped, randomized datetime object.
    """
    MAX_DELAY_DAYS = 3
    
    # 1. Calculate the maximum potential date (original date + 3 days)
    max_potential_date = original_date + timedelta(days=MAX_DELAY_DAYS)

    # 2. Determine the latest allowed date: The minimum of the max potential 
    # date and the current time (the cap).
    cap_date = datetime.now()
    latest_allowed_date = min(max_potential_date, cap_date)
    
    # 3. If the allowed range is non-positive (e.g., original_date is now 
    # or later than the cap), return the current time to ensure validity.
    if latest_allowed_date.timestamp() <= original_date.timestamp():
        return cap_date 

    # 4. Convert the range [original_date, latest_allowed_date] to timestamps.
    start_timestamp = original_date.timestamp()
    end_timestamp = latest_allowed_date.timestamp()
    
    # 5. Pick a random timestamp within this valid range.
    random_timestamp = random.uniform(start_timestamp, end_timestamp)
    
    # 6. Convert the random timestamp back to a datetime object.
    return datetime.fromtimestamp(random_timestamp)

# --- Q2(b) Book Model ---

class Book:
    """
    Represents the Book document structure and handles interaction with 
    the MongoDB 'books' collection.
    """
    
    def __init__(self):
        self.collection = db[COLLECTION_NAME] # This is the 'books' collection
        self.loans_collection = db['loans'] # Collection for tracking loans (though now primarily managed by Loan class)
        self._seed_data_if_empty()

    def _seed_data_if_empty(self):
        """
        Reads initial data from BOOKS if the collection is empty and populates MongoDB.
        """
        if self.collection.count_documents({}) == 0:
            print("Book collection is empty. Seeding initial data...")
            
            # Prepare books for insertion, ensuring we use correct fields
            books_to_insert = []
            for book in BOOKS:
                book_doc = book.copy()
                book_doc['author'] = book_doc['authors'][0] if book_doc.get('authors') else 'Unknown'
                
                # Ensure new book documents have default copies/available counts
                book_doc['copies'] = book_doc.get('copies', 1) 
                book_doc['available'] = book_doc.get('available', 1)
                
                books_to_insert.append(book_doc)
                
            self.collection.insert_many(books_to_insert)
            print(f"Seeded {len(books_to_insert)} books.")

    def get_all_books(self, category='All'):
        """
        Retrieves all books, optionally filtered by category, sorted by title.
        """
        query = {}
        if category != 'All':
            # Use regex to search for the category name case-insensitively
            query['category'] = {'$regex': f'^{category}$', '$options': 'i'}
            
        # MongoDB query: Find all matching documents, sort by 'title' ascending (1)
        books_cursor = self.collection.find(query).sort('title', 1)
        
        # Convert cursor to list of dictionaries and ensure 'id' field is a string
        books_list = []
        for book in books_cursor:
            book['id'] = str(book['_id'])
            books_list.append(book)
            
        return books_list

    def get_book_by_id(self, book_id):
        """
        Retrieves a single book document by its string ID (MongoDB ObjectId).
        """
        try:
            object_id = ObjectId(book_id)
        except Exception as e:
            print(f"Invalid ObjectId format: {e}")
            return None
            
        book = self.collection.find_one({'_id': object_id})
        
        if book:
            book['id'] = str(book['_id'])
        return book
    
    def add_new_book(self, title, authors, cover_image, isbn, publication_year, 
                     genres, publisher, description, page_count, # Existing 9 fields
                     category, copies, available): # NEW 3 fields
        """
        Adds a new book document to the MongoDB collection.
        """
        
        # Prepare the document for insertion
        book_data = {
            'title': title,
            'authors': authors,
            'image_file': cover_image or 'default_cover.jpg', 
            'isbn': isbn,
            'publication_year': int(publication_year) if publication_year else None,
            'publisher': publisher,
            'genres': genres or [],
            'description': description,
            'pages': int(page_count) if page_count else None, # Using 'pages' to match existing schema
            
            # --- NEW FIELDS INCLUDED IN DATABASE INSERTION ---
            'category': category or 'General', 
            'copies': int(copies) if copies else 1,
            'available': int(available) if available else 1,
            'author': authors[0] if authors else 'Unknown' 
        }
        
        try:
            result = self.collection.insert_one(book_data)
            return True, f"Book '{title}' added successfully with ID {result.inserted_id}!"
        except Exception as e:
            return False, f"Database error occurred: {str(e)}"

    # --- Q3(c) NEW HELPERS: Decoupled Availability Count Updates ---

    def decrease_available_count(self, book_id):
        """
        Decrements the available count for a book. Atomic check ensures count > 0.
        """
        try:
            book_obj_id = ObjectId(book_id)
            # Find the book and ensure available > 0 before decreasing 
            result = self.collection.update_one(
                {"_id": book_obj_id, "available": {"$gt": 0}},
                {"$inc": {"available": -1}}
            )
            
            if result.modified_count == 0:
                # Check if the book exists but its count is 0
                book = self.collection.find_one({"_id": book_obj_id})
                if book and book.get('available', 0) <= 0:
                    return False, "Book is not available for loan."
                return False, "Book not found or no change made."
            
            return True, "Available count decreased."
        except Exception as e:
            return False, f"Error decreasing count: {str(e)}"

    def increase_available_count(self, book_id):
        """Increments the available count for a book."""
        try:
            book_obj_id = ObjectId(book_id)
            self.collection.update_one(
                {"_id": book_obj_id},
                {"$inc": {"available": 1}}
            )
            return True, "Available count increased."
        except Exception as e:
            return False, f"Error increasing count: {str(e)}"

# Global instance of the Book model for use in app.py
book_model = Book() 


# --- Q3(c)(i) Loan Model ---

# Constants for Loan management
DEFAULT_LOAN_DURATION_DAYS = 14
MAX_RENEWS = 2 

class Loan:
    """
    Manages interactions with the 'loans' collection, handling creation, 
    retrieval, renewal, return, and deletion of loan documents.
    """
    def __init__(self):
        self.collection = db['loans']
        # Use the global book_model instance for count updates
        self.book_model = book_model 

    def create_loan(self, book_id, user_id, borrow_date=None):
        """
        Creates a new Loan document.
        - Checks if user already has an unreturned loan for the book.
        - Updates the available count for the book.
        """
        if borrow_date is None:
            borrow_date = datetime.now()
        
        # Sanity Check 1: A Loan document can be created for a user if he does not already
        # have an unreturned loan for the same book title. (Logic remains here for enforcement)
        active_loan = self.collection.find_one({
            "book_id": book_id,
            "user_id": user_id,
            "return_date": None # Unreturned loan
        })
        if active_loan:
            return False, "You already have an active, unreturned loan for this book."
            
        # Calculate due date
        due_date = borrow_date + timedelta(days=DEFAULT_LOAN_DURATION_DAYS)

        loan_data = {
            "book_id": book_id,
            "user_id": user_id,
            "borrow_date": borrow_date,
            "due_date": due_date,
            "return_date": None, # Null indicates unreturned/active loan
            "renew_count": 0
        }
        
        try:
            # Update the available count for the book should be updated (decreased).
            success, message = self.book_model.decrease_available_count(book_id)
            if not success:
                return False, message # Return error if not available or book not found

            # Create the Loan document
            result = self.collection.insert_one(loan_data)
            return True, f"Loan created successfully! ID: {str(result.inserted_id)}"
        except Exception as e:
            return False, f"Database error creating loan: {str(e)}"
    
    # --- FIX: ADDED has_active_loan method ---
    def has_active_loan(self, book_id, user_id):
        """
        Checks if a specific user currently has an unreturned loan for a specific book.
        This is used to determine if the 'Borrow' button should be disabled.
        """
        active_loan = self.collection.find_one({
            "book_id": book_id,
            "user_id": user_id,
            "return_date": None  # Indicates an unreturned/active loan
        })
        return active_loan is not None
    # --- END FIX ---

    def get_loan_by_id(self, loan_id):
        """
        Retrieves a specific loan document by its string ID.
        """
        try:
            object_id = ObjectId(loan_id)
        except:
            return None
        
        loan_doc = self.collection.find_one({'_id': object_id})
        if loan_doc:
            loan_doc['id'] = str(loan_doc['_id'])
        return loan_doc

    def get_user_loans(self, user_id, is_active=None):
        """
        Retrieves all loans for a specific user (active, returned, or all).
        """
        query = {"user_id": user_id}
        if is_active is True:
            query["return_date"] = None
        elif is_active is False:
            query["return_date"] = {"$ne": None}
            
        loans_cursor = self.collection.find(query).sort('borrow_date', -1)
        
        loans_list = []
        for loan in loans_cursor:
            loan['id'] = str(loan['_id'])
            
            # Helper: Attach book title for easier display
            book = self.book_model.get_book_by_id(loan['book_id'])
            loan['book_title'] = book['title'] if book else 'Unknown Title'
            loan['book_image'] = book.get('image_file', 'default.jpg') if book else 'default.jpg'
            
            loans_list.append(loan)
            
        return loans_list

    def renew_loan(self, loan_id):
        """
        A loan renew updates the renew count and the borrow date for the loan.
        """
        loan = self.get_loan_by_id(loan_id)
        
        if not loan:
            return False, "Loan not found."
        
        if loan.get('return_date'):
            return False, "Cannot renew a loan that has already been returned."

        # Helper Sanity Check: Renewal limit
        if loan.get('renew_count', 0) >= MAX_RENEWS:
            return False, f"Renewal limit reached ({MAX_RENEWS}). Please return the book."
            
        try:
            # Get the original borrow date to calculate the new capped borrow date
            original_borrow_date = loan['borrow_date']
            
            # --- FIX 1: Use the capped randomized date for the new borrow_date ---
            new_borrow_date = get_capped_new_loan_date(original_borrow_date)
            
            # Calculate new due date (14 days from the new borrow date)
            new_due_date = new_borrow_date + timedelta(days=DEFAULT_LOAN_DURATION_DAYS)
            
            # Update the Loan document
            self.collection.update_one(
                {"_id": ObjectId(loan_id)},
                {
                    "$set": {
                        "due_date": new_due_date,
                        # Update the borrow date with the new random, capped date
                        "borrow_date": new_borrow_date 
                    },
                    # Update the renew count
                    "$inc": {"renew_count": 1}
                }
            )
            return True, f"Loan successfully renewed. New due date: {new_due_date.strftime('%Y-%m-%d')}"
        except Exception as e:
            return False, f"Database error during renewal: {str(e)}"



    def return_loan(self, loan_id):
        """
        A loan return updates the return date. In addition, the available count
        for the book should be updated (increased).
        """
        loan = self.get_loan_by_id(loan_id)
        
        if not loan:
            return False, "Loan not found."
            
        if loan.get('return_date'):
            return False, "This loan has already been marked as returned."
            
        book_id = loan['book_id']
        
        try:
            # Get the original borrow date to calculate the new capped return date
            original_borrow_date = loan['borrow_date']
            
            # --- FIX 2: Use the capped randomized date for the return_date ---
            new_return_date = get_capped_new_loan_date(original_borrow_date)
            
            # 1. Update the Loan document with the new return date
            self.collection.update_one(
                {"_id": ObjectId(loan_id)},
                {"$set": {"return_date": new_return_date}}
            )
            
            # 2. Update book available count (increase)
            success, message = self.book_model.increase_available_count(book_id)
            if not success:
                print(f"ERROR: Failed to update book count upon return: {message}")
                
            return True, "Book successfully returned!"
        except Exception as e:
            return False, f"Database error during return: {str(e)}"
            
    def delete_loan(self, loan_id):
        """
        Deletes a Loan document.
        - Only loans that have been returned can be deleted (Sanity Check).
        """
        loan = self.get_loan_by_id(loan_id)
        
        if not loan:
            return False, "Loan not found."

        # Sanity Check: Only loans that have been returned can be deleted
        if loan.get('return_date') is None:
            return False, "Cannot delete an active (unreturned) loan."
            
        try:
            self.collection.delete_one({"_id": ObjectId(loan_id)})
            return True, "Loan record successfully deleted."
        except Exception as e:
            return False, f"Database error during deletion: {str(e)}"

# Global instance of the Loan model for use in app.py
loan_model = Loan() 

# --- Q2(c) User Model ---

class User:
    """
    Represents the User document structure and handles interaction with 
    the MongoDB 'users' collection.
    """
    
    def __init__(self):
        """Initializes connection to the Users collection."""
        self.collection = db[USER_COLLECTION_NAME]
        
        # Ensure an index on 'email' for fast lookup and uniqueness
        self.collection.create_index("email", unique=True)
        
        # Seed required users for Q2(c)
        self._seed_required_users()

    def _seed_required_users(self):
        """
        Registers the admin and non-admin users required by Q2(c) if they 
        haven't been created yet.
        """
        users_to_seed = [
            {'email': 'admin@lib.sg', 'password': '12345', 'name': 'Admin'},
            {'email': 'poh@lib.sg', 'password': '12345', 'name': 'Peter Oh'}
        ]
        
        for user_data in users_to_seed:
            # Check if user already exists
            if self.collection.find_one({'email': user_data['email']}) is None:
                print(f"Seeding user: {user_data['email']}...")
                self.register_user(
                    email=user_data['email'], 
                    password=user_data['password'], 
                    name=user_data['name']
                )
    
    def register_user(self, email, password, name):
        """
        Registers a new user by hashing the password and inserting the document.
        """
        if self.collection.find_one({'email': email}):
            return None # Email already in use

        # Hash the password for secure storage
        hashed_password = generate_password_hash(password)
        
        user_document = {
            'email': email,
            'password': hashed_password, 
            'name': name
        }
        
        try:
            result = self.collection.insert_one(user_document)
            return str(result.inserted_id)
        except:
            return None

    def find_user_by_email(self, email):
        """
        Retrieves a user document by email address.
        """
        user_doc = self.collection.find_one({'email': email})
        if user_doc:
            # Add string ID for Flask session use
            user_doc['id'] = str(user_doc['_id']) 
        return user_doc

    def check_password(self, user_doc, password):
        """
        Checks a plaintext password against the stored hashed password.
        """
        if user_doc and 'password' in user_doc:
            return check_password_hash(user_doc['password'], password)
        return False
    
    def get_user_by_id(self, user_id):
        """Retrieves a user document by its string ID (MongoDB ObjectId)."""
        try:
            object_id = ObjectId(user_id)
        except:
            return None
        
        user_doc = self.collection.find_one({'_id': object_id})
        if user_doc:
            user_doc['id'] = str(user_doc['_id'])
        return user_doc

# Global instance of the User model for use in app.py
user_model = User()

