# books_data.py

BOOKS = [
    {
        # Added ID for 'More details' linking (must be unique)
        "id": 1, 
        "title": "Accomplice to the Villain",
        "author": "Hannah Nicole Maehrer",
        "category": "Adult",
        "genres": ["Fantasy", "Romance", "Fiction", "Magic"],
        "pages": 482,
        "description": (
            "Once Upon a Time meets The Office in Hannah Nicole Maehrer's laugh-out-loud viral TikTok series "
            "turned novel, about the sunshine assistant to an Evil Villain...and their unexpected romance. "
            "A magical office comedy with grumpy bosses, snarky frogs, and definitely-not-feelings. "
            "As a third-generation villain's assistant, Evie Sage's life is…fine. She works for the most "
            "irresistible evil boss in the history of the world, manages a team of (mostly) competent minions, "
            "and only occasionally has to duck out of the way of some magical menace, so things could be worse. "
            "But when her boss, the Villain with no name, is slain by the handsome and infuriating Hero, "
            "Anya, Evie finds herself without a job—and without the one person she never thought she’d lose. "
            "Determined to find the next great evil, Evie embarks on a quest that leads her to a place she "
            "never expected: the heart of a war between two rival kingdoms, one good and one evil. "
            "There, she discovers a world of magic, intrigue, and a love that just might be worth turning "
            "to the dark side for."
        ),
        "image_file": "cover1.jpg"
    },
    {
        # Added ID
        "id": 2,
        "title": "Atomic Habits: An Easy & Proven Way to Build Good Habits & Break Bad Ones",
        "author": "James Clear",
        "category": "Adult",
        "genres": ["Nonfiction", "Self Help", "Psychology", "Personal Development", "Productivity", "Business"],
        "pages": 319,
        "description": (
            "No matter your goals, Atomic Habits offers a proven framework for improving—every day. "
            "James Clear, one of the world's leading experts on habit formation, reveals practical strategies "
            "that will teach you exactly how to form good habits, break bad ones, and master the tiny "
            "behaviors that lead to remarkable results. "
            "If you're having trouble changing your habits, the problem isn't you. The problem is your system. "
            "Bad habits repeat themselves again and again not because you don't want to change, but because "
            "you have the wrong system for change. You do not rise to the level of your goals. You fall "
            "to the level of your systems. Here, you'll get a proven system that can take you to new heights. "
            "Clear is known for his ability to distill complex topics into simple behaviors that can be "
            "easily applied to daily life and work. Here, he draws on the most proven ideas from biology, "
            "psychology, and neuroscience to create an easy-to-understand guide for making good habits "
            "inevitable and bad habits impossible. "
            "Along the way, readers will be inspired and entertained with true stories from Olympic gold "
            "medalists, award-winning artists, business leaders, life-saving physicians, and star comedians "
            "who have used the science of small habits to master their craft and vault to the top of their field."
        ),
        "image_file": "cover2.jpg"
    },
    # =============================================================
    # CORRECTED ENTRY: "Borders" (Matches image details)
    # =============================================================
    {
        # Added ID
        "id": 3,
        "title": "Borders",
        "author": "Thomas King, Natasha Donovan (Illustrator)",
        "category": "Teens",
        "genres": ["Graphic Novels", "Indigenous", "Fiction", "Comics"],
        "pages": 192,
        "description": (
            "A stunning graphic-novel adaptation based on the work of one of Canada's most revered and "
            "bestselling authors. "
            "A powerful graphic-novel adaptation of one of Thomas King’s most celebrated short stories, "
            "Borders explores themes of identity and belonging, and is a poignant depiction of the "
            "significance of a nation’s physical borders from an Indigenous perspective. This timeless story "
            "is brought to vibrant, piercing life by the singular vision of artist Natasha Donovan."
        ),
        "image_file": "cover3.jpg" # Assuming this is the correct image file name
    },
    # =============================================================
    # NEW ENTRY: "The Door of No Return"
    # =============================================================
    {
        # Added ID
        "id": 4,
        "title": "The Door of No Return",
        "author": "Kwame Alexander",
        "category": "Teens",
        "genres": ["Historical Fiction", "Poetry", "Fiction"],
        "pages": 432,
        "description": (
            "The first book in a trilogy that tells the story of a boy, a village, and the epic odyssey of an "
            "African youth whose world is shattered by the Atlantic slave trade. "
            "This beautifully written novel-in-verse follows 11-year-old Kofi Offin as he navigates life in "
            "his Ghanaian village in the 1800s. He enjoys time with his family and friends, but one shocking "
            "event changes everything, thrusting him into a treacherous journey that leads to the infamous "
            "‘door of no return.’ "
            "The book explores themes of identity, belonging, and the resilience of the human spirit. "
            "It is a powerful and unforgettable story that brings a vital piece of history to life."
        ),
        "image_file": "cover4.jpg" # Assuming a new image file for this book
    }
]

ALL_CATEGORIES = ["All", "Children", "Teens", "Adult"]