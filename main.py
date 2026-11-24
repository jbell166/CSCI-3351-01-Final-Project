# from IPython.core import events #NOTE i don't know how this got here. vwhat is this
# ==============================================================================================================
# Jessica Belle, Jason Calogine, Syed Rahman, Noah Shinar -- Group 'Too'
# Professor Sukhavasi
# CSCI-3351-01
# 18 November 2026
# ==============================================================================================================
# Final Project - Musical Practice Tracker
# ==============================================================================================================
import sqlite3
import threading
import calendar
import time
from datetime import datetime, timedelta

# ==============================================================================================================
# Opens a connection with the .db file (or creates it if it doesn't exist (probably what Colab is doing))
# check_same_thread = False prevents errors from occuring if some other service tried connecting with the .db file while program is in execution
userCalendar = sqlite3.connect("personalCalendar.db", check_same_thread=False)
sqliteCursor = userCalendar.cursor()  # Allows sqliteCursor to cycle through the .db file userCalendar is connected to, allowing us to execute queries using personalCalendar.db
# ==============================================================================================================
# Creates the table bookings if it does not exist in the .db file already
# NOTE the three quotes allow for multi-line strings (""")
sqliteCursor.execute(""" CREATE TABLE IF NOT EXISTS events (
                         eventID INTEGER PRIMARY KEY,
                         organizerName TEXT,
                         eventDate TEXT,
                         eventTime TEXT,
                         eventStatus TEXT DEFAULT 'Pending',
                         eventNotification INTEGER DEFAULT 0 )""")

userCalendar.commit()  # "Commits" the created events table to the .db file connected at userCalendar (yes, like Github)
db_lock = threading.Lock()  # Prevents two threads from writing to the .db file at the same time (This is usually enabled, but was disabled when check_same_thread was made False)
# ^^ SO, by calling it each time you try modyfing/do anything to the .db file, it prevents anything else from doing anything in that moment, so it has to be called variously throughout the program
# ==============================================================================================================
# Creates repertoire table in personalCalendar.db
sqliteCursor.execute(""" CREATE TABLE IF NOT EXISTS repertoire (
                         repID INTEGER PRIMARY KEY,
                         title TEXT,
                         composer TEXT,
                         grade REAL,
                         ensemble TEXT,
                         performanceDate TEXT )""")
userCalendar.commit()


class Repertoire:
    def __init__(self, title, composer, grade, ensemble, performanceDate, repID=None):
        self.repID = repID
        self.title = title
        self.composer = composer
        self.grade = grade
        self.ensemble = ensemble
        self.performanceDate = performanceDate

    def print(self):
        print("---< ", self.title, " >---")
        print("By ", self.composer)
        print("Grade: ", self.grade)
        print("Being performed on ", self.performanceDate, " by ", self.ensemble)


repertoireList = []


def loadRepertoire():
    repertoireList.clear()
    with db_lock:
        sqliteCursor.execute("SELECT repID, title, composer, grade, ensemble, performanceDate FROM repertoire")
        for repID, title, composer, grade, ensemble, perfDate in sqliteCursor.fetchall():
            repertoireList.append(Repertoire(title, composer, grade, ensemble, perfDate, repID))


# Load saved pieces immediately when the program starts
loadRepertoire()


# ==============================================================================================================
def viewCalendar():
    with db_lock:
        sqliteCursor.execute(
            "SELECT eventDate, eventTime, organizerName, eventStatus FROM events ORDER BY eventDate, eventTime")
        rows = sqliteCursor.fetchall()

    items_by_date = {}
    months_to_show = set()

    # Always include current month
    now = datetime.now()
    months_to_show.add((now.year, now.month))

    # 1. Load Events from SQLite database
    for eventDate, eventTime, name, status in rows:
        short_status = "C" if status == "Confirmed" else "P"
        entry = f"{eventTime} {name[:7]}({short_status})"
        items_by_date.setdefault(eventDate, []).append(entry)

        try:
            dt = datetime.strptime(eventDate, "%Y-%m-%d")
            months_to_show.add((dt.year, dt.month))
        except ValueError:
            pass

    # 2. Load Performances from repertoireList onto calendar
    for piece in repertoireList:
        try:
            dt = datetime.strptime(piece.performanceDate, "%Y-%m-%d")
            months_to_show.add((dt.year, dt.month))
            entry = f"[PERF] {piece.title[:9]}"
            items_by_date.setdefault(piece.performanceDate, []).append(entry)
        except ValueError:
            pass

    # 3. Draw the Calendar Grid
    BOX_WIDTH = 17
    DAYS_HEADER = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
    calendar.setfirstweekday(calendar.SUNDAY)

    for year, month in sorted(months_to_show):
        month_name = calendar.month_name[month]
        print(f"\n{'=' * 40} {month_name.upper()} {year} {'=' * 40}")

        header_row = "|" + "|".join(day.center(BOX_WIDTH) for day in DAYS_HEADER) + "|"
        border_line = "+" + "+".join("-" * BOX_WIDTH for _ in range(7)) + "+"
        print(border_line)
        print(header_row)
        print(border_line)

        for week in calendar.monthcalendar(year, month):
            max_items = 2
            for day in week:
                if day != 0:
                    date_key = f"{year:04d}-{month:02d}-{day:02d}"
                    max_items = max(max_items, len(items_by_date.get(date_key, [])))

            # Print Day Nums
            day_num_cells = []
            for day in week:
                if day == 0:
                    day_num_cells.append(" " * BOX_WIDTH)
                else:
                    day_num_cells.append(f" {day:02d}".ljust(BOX_WIDTH))
            print("|" + "|".join(day_num_cells) + "|")

            # Print Events & Performances inside each day's box
            for line_idx in range(max_items):
                cells = []
                for day in week:
                    if day == 0:
                        cells.append(" " * BOX_WIDTH)
                    else:
                        date_key = f"{year:04d}-{month:02d}-{day:02d}"
                        day_items = items_by_date.get(date_key, [])
                        if line_idx < len(day_items):
                            text = f" {day_items[line_idx]}"[:BOX_WIDTH]
                            cells.append(text.ljust(BOX_WIDTH))
                        else:
                            cells.append(" " * BOX_WIDTH)
                print("|" + "|".join(cells) + "|")

            print(border_line)

    print("Legend: (P) = Pending Event | (C) = Confirmed Event | [PERF] = Repertoire Performance")


# ==============================================================================================================
def practiceMenu():
    practiceMenuLoop = True
    while practiceMenuLoop:
        print("\n-----< Create Practice Session >-----")
        print(
            "G: Generate a Practice Session")  # This wording WILL change. I REFUSE to use the word generate in AI class (unless it'll give me brownie points with supar? hmm?)
        print("D: Delete a Practice Session")
        print("V: View a Practice Session")
        print("M: Return to Menu")

        practiceMenuChoice = input("What would you like to do? ")
        if practiceMenuChoice.upper() == 'G':
            print("im generating a practice session")
        elif practiceMenuChoice.upper() == 'V':
            print("im viewing a practice session")
        elif practiceMenuChoice.upper() == 'D':
            print("im deleting a practice session")
        elif practiceMenuChoice.upper() == 'M':
            practiceMenuLoop = False
        else:
            print("\nInvalid Character")


def suggestPracticePlan():
    if not repertoireList:
        print("\nNo repertoire pieces found! Add a piece in 'Modify Repertoire' first.")
        return

    print("\n--- Select a Piece to Prepare For ---")
    for idx, piece in enumerate(repertoireList):
        print(f"{idx + 1}. {piece.title} (Grade {piece.grade}) - Performance: {piece.performanceDate}")

    try:
        choice = int(input("\nEnter piece number: ")) - 1
        if choice < 0 or choice >= len(repertoireList):
            print("Invalid selection.")
            return
    except ValueError:
        print("Please enter a valid number.")
        return

    selected_piece = repertoireList[choice]

    try:
        perf_date = datetime.strptime(selected_piece.performanceDate, "%Y-%m-%d").date()
    except ValueError:
        print("Error: This piece does not have a valid YYYY-MM-DD performance date.")
        return

    today = datetime.now().date()
    days_until_perf = (perf_date - today).days

    if days_until_perf <= 0:
        print("This performance date has already passed or is today!")
        return

    # 1. Determine sessions & duration based on difficulty grade
    grade = float(selected_piece.grade)
    target_sessions = max(2, int(grade * 2))  # Ex: Grade 0.5 -> 2 sessions, Grade 5 -> 10 sessions
    session_minutes = int(30 + (grade * 10))  # Ex: Grade 1 -> 40 mins, Grade 5 -> 80 mins

    # 2. Check SQLite schedule for every day between tomorrow and performance
    with db_lock:
        sqliteCursor.execute("SELECT eventDate, COUNT(*) FROM events GROUP BY eventDate")
        busy_counts = dict(sqliteCursor.fetchall())  # e.g., {'2026-11-26': 2}

    open_days = []
    light_days = []

    for offset in range(1, days_until_perf):
        candidate_date = today + timedelta(days=offset)
        date_str = candidate_date.strftime("%Y-%m-%d")
        event_count = busy_counts.get(date_str, 0)

        if event_count == 0:
            open_days.append(date_str)
        elif event_count == 1:
            light_days.append(date_str)

    # Combine free days first then lightly booked days if more time is needed
    candidate_pool = open_days + light_days

    if not candidate_pool:
        print("\nYour schedule is completely packed before this performance!")
        return

    # 3. Space out suggested sessions evenly across available days
    num_to_pick = min(target_sessions, len(candidate_pool))
    if num_to_pick == len(candidate_pool):
        suggested_dates = sorted(candidate_pool)
    else:
        step = len(candidate_pool) / num_to_pick
        suggested_dates = sorted([candidate_pool[int(i * step)] for i in range(num_to_pick)])

    # 4. Display recommendation
    print(f"\n===== Recommended Study Plan for '{selected_piece.title}' =====")
    print(f"Difficulty Grade: {grade} | Days Remaining: {days_until_perf}")
    print(f"Recommended Load: {num_to_pick} sessions ({session_minutes} mins each)\n")

    for d in suggested_dates:
        status_note = "Completely Free" if d in open_days else "1 Existing Event"
        print(f"  -> {d} ({status_note})")

    # 5. Optional: Automatically add study sessions to the calendar
    save_choice = input("\nWould you like to add these study sessions to your calendar? (Y/N): ")
    if save_choice.upper() == 'Y':
        default_time = input("What default time should these be scheduled for (HH:MM, e.g., 16:00)? ")
        try:
            datetime.strptime(default_time, "%H:%M")
        except ValueError:
            print("Invalid time format. Defaulting to 16:00.")
            default_time = "16:00"

        with db_lock:
            for d in suggested_dates:
                # Avoid exact time collision if a light day already has an event at default_time
                sqliteCursor.execute("SELECT * FROM events WHERE eventDate = ? AND eventTime = ?", (d, default_time))
                if not sqliteCursor.fetchone():
                    label = f"Study:{selected_piece.title[:8]}"
                    sqliteCursor.execute(
                        "INSERT INTO events (organizerName, eventDate, eventTime, eventStatus) VALUES (?, ?, ?, ?)",
                        (label, d, default_time, "Confirmed")
                    )
            userCalendar.commit()
        print("Study sessions added! Select 'View Calendar' in the main menu to see them.")


# ==============================================================================================================
def eventMenu():
    eventMenuLoop = True
    while eventMenuLoop:
        print("\n-----< Modify Events >-----")
        print("A: Add New Event")
        print("D: Delete Event")
        print("V: View Events")
        print("M: Return to Menu")

        eventMenuChoice = input("What would you like to do? ")
        if eventMenuChoice.upper() == 'A':
            print("im adding a new event")
        elif eventMenuChoice.upper() == 'D':
            print("im deleteing a new event")
        elif eventMenuChoice.upper() == 'V':
            print("im viewing the events")
        elif eventMenuChoice.upper() == 'M':
            eventMenuLoop = False
        else:
            print("\nInvalid Character")


# ==============================================================================================================
class Repertoire:
    def __init__(self, title, composer, grade, ensemble, performanceDate):
        self.title = title
        self.composer = composer
        self.grade = grade
        self.ensemble = ensemble
        self.performanceDate = performanceDate

    def print(self):
        print("---< ", self.title, " >---")
        print("By ", self.composer)
        print("Grade: ", self.grade)
        print("Being performed on ", self.performanceDate, " by ", self.ensemble)


# ==============================================================================================================
def repertoireMenu():
    repertoireMenuLoop = True
    while repertoireMenuLoop:
        print("\n-----< Modify Repertoire >-----")
        print("A: Add New Repertoire")
        print("D: Delete Repertoire")
        print("V: View Repertoires")
        print("M: Return to Menu")

        repertoireMenuChoice = input("What would you like to do? ")
        if repertoireMenuChoice.upper() == 'A':
            tempTitle = input("\nWhat is the name of the piece you wish to add? ")
            tempComposer = input("Who composes the piece you wish to add? ")
            validGrade = False
            print("0.5 - Very Easy")
            print("1 - Easy")
            print("2 - Medium-Easy")
            print("3 - Medium")
            print("4 - Medium-Advanced")
            print("5 - Advanced")
            while not validGrade:
                tempGrade = input("\nWhat difficulty would you grade this piece at? ")
                try:
                    if float(tempGrade) in [0.5, 1.0, 2.0, 3.0, 4.0, 5.0]:
                        validGrade = True
                    else:
                        print("That is not a valid grade.")
                except ValueError:
                    print("Please enter a valid number.")

            tempEnsemble = input("What group is performing this piece? ")

            # Enforce YYYY-MM-DD format so it maps directly onto viewCalendar()
            validDate = False
            while not validDate:
                tempPerformanceDate = input("When is this performance (YYYY-MM-DD)? ")
                try:
                    datetime.strptime(tempPerformanceDate, "%Y-%m-%d")
                    validDate = True
                except ValueError:
                    print("Invalid format. Please use YYYY-MM-DD (e.g., 2026-12-15).")

            tempRepertoire = Repertoire(tempTitle, tempComposer, tempGrade, tempEnsemble, tempPerformanceDate)
            repertoireList.append(tempRepertoire)
            print("Piece added and synced to calendar!")

            # Triggers practice suggestions right after adding a new piece
            if input("Would you like a suggested practice plan for this piece now? (Y/N): ").upper() == 'Y':
                suggestPracticePlan()

        elif repertoireMenuChoice.upper() == 'D':
            if not repertoireList:
                print("\nNo repertoire pieces to delete.")
                continue

            print("\n")
            for index, piece in enumerate(repertoireList):
                print(f"{index + 1}.")
                piece.print()
                print("\n")

            deleted = False
            while not deleted:
                toBeDeleted = input("Which piece would you like to delete? ")
                try:
                    idx = int(toBeDeleted) - 1
                    if idx < 0 or idx >= len(repertoireList):
                        print("That is not a valid choice.")
                    else:
                        repertoireList.pop(idx)
                        deleted = True
                        print("Piece successfully deleted")
                except ValueError:
                    print("Please enter a valid number.")

        elif repertoireMenuChoice.upper() == 'V':
            if not repertoireList:
                print("\nNo repertoire pieces saved.")
            for piece in repertoireList:
                print("\n")
                piece.print()
        elif repertoireMenuChoice.upper() == 'M':
            repertoireMenuLoop = False
        else:
            print("\nInvalid Character")


# ==============================================================================================================
print("-----< Musical Practice Tracker >-----")
print("-----< CSCI-3351-01 Group 'Too' >-----")
menuLoop = True
while menuLoop:
    print("\n-----< Menu >-----")
    print("V: View Calendar")
    print("C: Create Practice Session")
    print("E: Modify Events")
    print("R: Modify Repertoire")
    print("Q: Quit")

    menuChoice = input("What would you like to do? ")
    if menuChoice.upper() == 'V':
        viewCalendar()
    elif menuChoice.upper() == 'C':
        practiceMenu()
    elif menuChoice.upper() == 'E':
        eventMenu()
    elif menuChoice.upper() == 'R':
        repertoireMenu()
    elif menuChoice.upper() == 'Q':
        print("i dont wanna be in the musical practice tracker anymore!")
        menuLoop = False
    else:
        print("Invalid Character")

print("much better")
# ==============================================================================================================
