## Staycation — E-Library Management System (Flask + MongoDB)


## Overview

**Staycation** is a full-stack web application for managing an e-library system.  
It supports **book browsing, category-based search, authentication, role-based access control, and end-to-end loan management**, with data persistence in **MongoDB**.

The system enforces real-world constraints:
- A book title may have **multiple copies**
- **Loans cannot exceed available copies**
- Users cannot borrow the same book twice without returning it

This project demonstrates practical implementation of **MVC architecture**, **Flask Blueprints**, **WTForms**, **Jinja templating**, and **MongoDB document modeling**.

## Key Features

### Book Browsing & Search
- View all book titles sorted alphabetically  
- Filter by category: **Children, Teens, Adult**  
- View detailed information for each book  
- Fully responsive UI (desktop, tablet, mobile)

### Database Integration (MongoDB)
- Book records stored as MongoDB documents  
- Auto-populate database from source dataset if the collection is empty  
- Pages rendered dynamically from live database queries


### Authentication & Roles
- User registration, login, and logout  
- Two user roles:
  - **Admin** (catalog management)
  - **User** (borrowing and loan management)

**Pre-configured accounts**
Admin:
- Email: admin@lib.sg
- Password: 12345

User:
- Email: poh@lib.sg
- Password: 12345


### Admin Capabilities
- Add new books via a structured form
- Support for:
  - Multiple authors
  - Multiple genres
  - Custom metadata
- Immediate persistence to MongoDB

### Loan Management System
- Users can:
  - Borrow books (only if copies are available)
  - Renew loans (maximum 2 times)
  - Return books
  - Delete returned loan records
- Business rules enforced:
  - No duplicate active loan for the same book
  - Borrow blocked when no copies remain
  - Due dates auto-calculated (2 weeks from borrow date)
  - Overdue loans cannot be renewed


## System Architecture

This application follows **Model–View–Controller (MVC)** principles.

### Model
- **Book**
  - Encapsulates book metadata and availability logic
  - Handles borrow/return with data-integrity checks
- **Loan**
  - Manages the loan lifecycle: create, retrieve, renew, return, delete
  - Enforces one active loan per user per book

### View
- **HTML + CSS + Bootstrap**
- **Jinja2** with:
  - Template inheritance
  - Macros and filters
  - Dynamic data binding

### Controller
- **Flask routes organized with Blueprints**
- Handles:
  - Authentication
  - Book operations
  - Loan transactions
  - Role-based access control

## Frontend–Backend Interaction

- User actions (search, login, borrow, renew, return) trigger Flask routes  
- Routes interact with MongoDB via model methods  
- Updated state is rendered using Jinja variables  
- **Flash messages** provide user feedback  

**Outcome:** clean separation of concerns, maintainable logic, and scalable design.

## Tech Stack

- **Backend:** Python, Flask  
- **Database:** MongoDB  
- **Frontend:** HTML, CSS, Bootstrap  
- **Templating:** Jinja2  
- **Forms & Validation:** WTForms  
- **Architecture:** MVC, Blueprints  

## Setup & Run

### Clone the Repository
```bash
git clone https://github.com/shaira44444/Staycation.git
cd Staycation
