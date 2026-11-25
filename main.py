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
                         eventType TEXT DEFAULT 'E',
                         organizerName TEXT,
                         eventDate TEXT,
                         eventTime TEXT,
                         eventStatus TEXT DEFAULT 'Pending',
                         eventNotification INTEGER DEFAULT 0,
                         repID INTEGER DEFAULT NULL )""")

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
# ==============================================================================================================
class Repertoire:
    def __init__(self, title, composer, grade, ensemble, performanceDate, repID=None):
        self.repID = repID
        self.title = title
        self.composer = composer
        self.grade = grade
        self.ensemble = ensemble
        self.performanceDate = performanceDate
        self.numberOfPractices = 0

    def print(self):
        print("-----< ", self.title, " >-----")
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

loadRepertoire()
# ==============================================================================================================
# ==============================================================================================================
# ==============================================================================================================
# ==============================================================================================================
def viewCalendar():
    with db_lock:
        sqliteCursor.execute(
            "SELECT eventID, eventType, eventDate, eventTime, organizerName FROM events ORDER BY eventDate, eventTime"
        )
        rows = sqliteCursor.fetchall()

    items_by_date = {}
    months_to_show = set()

    # Always include current month
    now = datetime.now()
    months_to_show.add((now.year, now.month))

    # 1. Load E (Misc Event), R (Rehearsal), and Pra (Practice Session) from database
    for eventID, eventType, eventDate, eventTime, name in rows:
        if eventType == 'Pra':
            entry = f"Pra: {eventID}"
        elif eventType == 'R':
            entry = f"R: {name[:12]}"
        else:
            entry = f"E: {name[:12]}"

        items_by_date.setdefault(eventDate, []).append(entry)

        try:
            dt = datetime.strptime(eventDate, "%Y-%m-%d")
            months_to_show.add((dt.year, dt.month))
        except ValueError:
            pass

    # 2. Load Per (Performance) from repertoireList without duplicates
    seen_performances = set()  # Tracks (performanceDate, ensemble.lower())
    for piece in repertoireList:
        try:
            dt = datetime.strptime(piece.performanceDate, "%Y-%m-%d")
            months_to_show.add((dt.year, dt.month))

            perf_key = (piece.performanceDate, piece.ensemble.strip().lower())
            if perf_key not in seen_performances:
                seen_performances.add(perf_key)
                entry = f"Per: {piece.ensemble[:10]}"
                items_by_date.setdefault(piece.performanceDate, []).append(entry)
        except ValueError:
            pass

    # 3. Draw Calendar Grid
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

            # Print Day Numbers
            day_num_cells = []
            for day in week:
                if day == 0:
                    day_num_cells.append(" " * BOX_WIDTH)
                else:
                    day_num_cells.append(f" {day:02d}".ljust(BOX_WIDTH))
            print("|" + "|".join(day_num_cells) + "|")

            # Print Categorized Entries inside each day's box
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

    print("-----< E: Miscellaneous Event | R: Rehearsal | Pra: Practice Session | Per: Performance >-----")
# ==============================================================================================================
# ==============================================================================================================
# ==============================================================================================================
def buildPracticeItinerary(target_piece):
    today = datetime.now().date()
    scored_pieces = []

    # Prioritize the selected piece, plus any other pieces sharing that same concert (date + ensemble)
    concert_pieces = [
        p for p in repertoireList
        if p.performanceDate == target_piece.performanceDate and p.ensemble.strip().lower() == target_piece.ensemble.strip().lower()
    ]
    if not concert_pieces:
        concert_pieces = [target_piece]

    for piece in concert_pieces:
        try:
            perf_dt = datetime.strptime(piece.performanceDate, "%Y-%m-%d").date()
            days_left = max(1, (perf_dt - today).days)
        except ValueError:
            days_left = 30

        tempPriority = float(piece.grade) / days_left
        tempPriority1 = (1 - (float(piece.grade) / 2) * 0.1) ** piece.numberOfPractices
        priority = tempPriority * tempPriority1

        # Give a slight boost to the specific piece the user selected
        if piece.repID == target_piece.repID:
            priority *= 1.25

        scored_pieces.append((priority, piece))

    scored_pieces.sort(key=lambda x: x[0], reverse=True)
    selected = [p for _, p in scored_pieces[:3]]

    total_minutes = 60
    warmup = 5
    warmdown = 5
    break_time = 5 if len(selected) > 1 else 0
    total_breaks = break_time * (len(selected) - 1)
    available_study_mins = total_minutes - warmup - warmdown - total_breaks

    total_grade_weight = sum(float(p.grade) for p in selected)
    raw_allocations = []
    for p in selected:
        mins = max(10, int(round((float(p.grade) / total_grade_weight) * available_study_mins)))
        raw_allocations.append(mins)

    diff = available_study_mins - sum(raw_allocations)
    raw_allocations += diff

    steps = [f"  - {warmup} mins: Warm-up"]
    for idx, (piece, mins) in enumerate(zip(selected, raw_allocations)):
        steps.append(f"  - {mins} mins: '{piece.title}' [Rep ID #{piece.repID}] (Grade {piece.grade}, Perf: {piece.performanceDate})")
        if idx < len(selected) - 1:
            steps.append(f"  - {break_time} mins: Short Break")
    steps.append(f"  - {warmdown} mins: Warm-down")

    for piece in selected:
        piece.numberOfPractices += 1

    return "\n".join(steps)


def generatePracticeSession():
    if not repertoireList:
        print("\nNo repertoire pieces found! Add a piece in 'Modify Repertoire' first.")
        return

    # 1. Ask which specific repertoire/performance to practice for
    print("\n--- Select a Performance / Piece to Practice For ---")
    for piece in repertoireList:
        print(f"ID #{piece.repID}: '{piece.title}' ({piece.ensemble}) - Performance Date: {piece.performanceDate}")

    try:
        chosen_rep_id = int(input("\nEnter the Repertoire ID # you are practicing for: "))
    except ValueError:
        print("Invalid ID. Returning to Practice Menu...")
        return

    target_piece = next((p for p in repertoireList if p.repID == chosen_rep_id), None)
    if not target_piece:
        print(f"No repertoire found with ID #{chosen_rep_id}.")
        return

    # 2. Cap candidate dates before specific piece's performance date
    today = datetime.now().date()
    try:
        target_perf_date = datetime.strptime(target_piece.performanceDate, "%Y-%m-%d").date()
    except ValueError:
        print("Error: Invalid performance date format on this piece.")
        return

    days_until_perf = (target_perf_date - today).days
    if days_until_perf <= 1:
        print("\nThere are no days left before the performance. Either reenter the performance to see suggestions again or manually enter practices that work better for you.")
        return

    all_perf_dates = {piece.performanceDate for piece in repertoireList}

    with db_lock:
        sqliteCursor.execute("SELECT eventDate, eventTime, eventType FROM events")
        all_events = sqliteCursor.fetchall()

    times_by_date = {}
    rehearsal_count = {}
    for edate, etime, etype in all_events:
        times_by_date.setdefault(edate, set()).add(etime)
        if etype == 'R':
            rehearsal_count[edate] = rehearsal_count.get(edate, 0) + 1

    # 3. Scan only days between tomorrow and target_perf_date
    candidate_days = []
    for offset in range(1, days_until_perf):
        cand_date = (today + timedelta(days=offset)).strftime("%Y-%m-%d")
        has_perf = 1 if cand_date in all_perf_dates else 0
        num_rehearsals = rehearsal_count.get(cand_date, 0)
        total_events = len(times_by_date.get(cand_date, set()))

        booked_hours = {t.split(":") for t in times_by_date.get(cand_date, set())}
        open_hour = None
        for hr in range(9, 21):
            hr_str = f"{hr:02d}"
            if hr_str not in booked_hours:
                open_hour = f"{hr_str}:00"
                break

        if open_hour:
            sort_key = (has_perf, num_rehearsals, total_events, offset)
            candidate_days.append((sort_key, cand_date, open_hour, has_perf, num_rehearsals))

    candidate_days.sort(key=lambda x: x)

    if not candidate_days:
        print("\nThere are no days left before the performance. Either reenter the performance to see suggestions again or manually enter practices that work better for you.")
        return

    # 4. Suggest slots up to this specific performance date
    for _, sugg_date, sugg_time, has_perf, num_reh in candidate_days:
        end_hour = f"{int(sugg_time[:2]) + 1:02d}:00"
        status_note = "No rehearsals or performances" if (has_perf == 0 and num_reh == 0) else f"{num_reh} rehearsal(s), {has_perf} performance(s)"

        print(f"\nSuggested Practice Slot for '{target_piece.title}' (Perf: {target_piece.performanceDate}):")
        print(f"  -> {sugg_date} from {sugg_time} to {end_hour} ({status_note})")
        book_choice = input("Would you like to book this session? (Y/N): ").upper()

        if book_choice == 'Y':
            itinerary = buildPracticeItinerary(target_piece)
            with db_lock:
                sqliteCursor.execute(
                    "INSERT INTO events (eventType, organizerName, eventDate, eventTime, eventStatus, repID) VALUES (?, ?, ?, ?, ?, ?)",
                    ("Pra", itinerary, sugg_date, sugg_time, "Confirmed", target_piece.repID)
                )
                userCalendar.commit()
                practice_id = sqliteCursor.lastrowid

            print(f"\n-----< Practice Session Confirmed (Practice ID: {practice_id} | Linked Rep ID: #{target_piece.repID}) >-----")
            print(f"Date & Time: {sugg_date} | {sugg_time} - {end_hour}")
            print("Itinerary:")
            print(itinerary)
            return
        else:
            next_choice = input("Would you like a new date suggested? (Y/N): ").upper()
            if next_choice != 'Y':
                print("Returning to Practice Menu...")
                return

    print("\nThere are no days left before the performance. Either reenter the performance to see suggestions again or manually enter practices that work better for you.")


def practiceMenu():
    practiceMenuLoop = True
    while practiceMenuLoop:
        print("\n-----< Create Practice Session >-----")
        print("G: Generate a Practice Session")
        print("D: Delete a Practice Session")
        print("V: View a Practice Session")
        print("M: Return to Menu")

        practiceMenuChoice = input("What would you like to do? ")
        if practiceMenuChoice.upper() == 'G':
            generatePracticeSession()

        elif practiceMenuChoice.upper() == 'V':
            target_id = input("\nEnter the Practice Session ID you would like to view: ")
            with db_lock:
                sqliteCursor.execute(
                    "SELECT eventID, eventDate, eventTime, organizerName FROM events WHERE eventType = 'Pra' AND eventID = ?",
                    (target_id,)
                )
                session = sqliteCursor.fetchone()

            if not session:
                print(f"No practice session found with ID #{target_id}.")
            else:
                pid, pdate, ptime, itinerary = session
                end_hour = f"{int(ptime[:2]) + 1:02d}:00"
                print(f"\n-----< Practice Session #{pid} >-----")
                print(f"Date & Time: {pdate} | {ptime} - {end_hour}")
                print("Itinerary:")
                print(itinerary)

        elif practiceMenuChoice.upper() == 'D':
            target_id = input("\nEnter the Practice Session ID you would like to delete: ")
            with db_lock:
                sqliteCursor.execute(
                    "SELECT eventID, eventDate, eventTime, organizerName FROM events WHERE eventType = 'Pra' AND eventID = ?",
                    (target_id,)
                )
                session = sqliteCursor.fetchone()

            if not session:
                print(f"No practice session found with ID #{target_id}.")
            else:
                pid, pdate, ptime, itinerary = session
                end_hour = f"{int(ptime[:2]) + 1:02d}:00"
                print(f"\n-----< Practice Session #{pid} >-----")
                print(f"Date & Time: {pdate} | {ptime} - {end_hour}")
                print("Itinerary:")
                print(itinerary)

                confirm = input("\nAre you sure you want to delete this practice session? (Y/N): ").upper()
                if confirm == 'Y':
                    with db_lock:
                        sqliteCursor.execute("DELETE FROM events WHERE eventID = ? AND eventType = 'Pra'", (pid,))
                        userCalendar.commit()
                    print(f"Practice Session #{pid} successfully deleted!")
                else:
                    print("Deletion canceled.")

        elif practiceMenuChoice.upper() == 'M':
            practiceMenuLoop = False
        else:
            print("\nInvalid Character")


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

        # 1. Add new event (E or R)
        if eventMenuChoice.upper() == 'A':
            etype = input("\nIs this a Rehearsal (R) or Miscellaneous Event (E)? ").upper()
            while etype not in ['R', 'E']:
                print("Invalid choice. Please enter 'R' for Rehearsal or 'E' for Miscellaneous Event.")
                etype = input("Is this a Rehearsal (R) or Miscellaneous Event (E)? ").upper()

            if etype == 'R':
                label = input("Enter the ensemble that is rehearsing: ")
            else:
                label = input("Enter the name of the event: ")

            valid_datetime = False
            while not valid_datetime:
                date_str = input("Enter date (YYYY-MM-DD): ")
                time_str = input("Enter time (HH:MM, 24-hr): ")
                try:
                    event_dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
                    if event_dt <= datetime.now():
                        print("Error: You cannot schedule an event in the past.")
                    else:
                        valid_datetime = True
                except ValueError:
                    print("Invalid format. Use YYYY-MM-DD for date and HH:MM for time (e.g., 14:30).")

            with db_lock:
                sqliteCursor.execute("SELECT * FROM events WHERE eventDate = ? AND eventTime = ?", (date_str, time_str))
                if sqliteCursor.fetchone():
                    print("Sorry, that exact date and time slot is already booked!")
                    continue

                sqliteCursor.execute(
                    "INSERT INTO events (eventType, organizerName, eventDate, eventTime, eventStatus) VALUES (?, ?, ?, ?, ?)",
                    (etype, label, date_str, time_str, "Confirmed")
                )
                userCalendar.commit()

            category_name = "Rehearsal" if etype == 'R' else "Miscellaneous Event"
            print(f"{category_name} added to the calendar!")

        # 2. Delete event
        elif eventMenuChoice.upper() == 'D':
            with db_lock:
                sqliteCursor.execute(
                    "SELECT eventID, eventType, organizerName, eventDate, eventTime FROM events WHERE eventType IN ('E', 'R') ORDER BY eventDate, eventTime"
                )
                rows = sqliteCursor.fetchall()

            if not rows:
                print("\nNo events or rehearsals to delete.")
                continue

            print("\n")
            for index, (eid, etype, name, edate, etime) in enumerate(rows):
                tag = "Rehearsal" if etype == 'R' else "Event"
                print(f"{index + 1}. -----< {tag}: {name} >-----")
                print(f"   Date: {edate} at {etime}\n")

            deleted = False
            while not deleted:
                toBeDeleted = input("Which event would you like to delete? ")
                try:
                    idx = int(toBeDeleted) - 1
                    if idx < 0 or idx >= len(rows):
                        print("That is not a valid choice.")
                    else:
                        target_id = rows[idx][0]  # Grab eventID from database
                        with db_lock:
                            sqliteCursor.execute("DELETE FROM events WHERE eventID = ?", (target_id,))
                            userCalendar.commit()
                        deleted = True
                        print("Event successfully deleted!")
                except ValueError:
                    print("Please enter a valid number.")

        # 3. View events
        elif eventMenuChoice.upper() == 'V':
            with db_lock:
                sqliteCursor.execute(
                    "SELECT eventType, organizerName, eventDate, eventTime FROM events WHERE eventType IN ('E', 'R') ORDER BY eventDate, eventTime"
                )
                rows = sqliteCursor.fetchall()

            if not rows:
                print("\nNo events or rehearsals scheduled.")
            else:
                for etype, name, edate, etime in rows:
                    tag = "Rehearsal" if etype == 'R' else "Miscellaneous Event"
                    print(f"\n-----< {tag}: {name} >-----")
                    print(f"Date: {edate}")
                    print(f"Time: {etime}")

        elif eventMenuChoice.upper() == 'M':
            eventMenuLoop = False
        else:
            print("\nInvalid Character")
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

            # Save permanently to SQLite
            with db_lock:
                sqliteCursor.execute("""
                    INSERT INTO repertoire (title, composer, grade, ensemble, performanceDate)
                    VALUES (?, ?, ?, ?, ?)
                """, (tempTitle, tempComposer, float(tempGrade), tempEnsemble, tempPerformanceDate))
                userCalendar.commit()
                new_id = sqliteCursor.lastrowid

            tempRepertoire = Repertoire(tempTitle, tempComposer, float(tempGrade), tempEnsemble, tempPerformanceDate, new_id)
            repertoireList.append(tempRepertoire)
            print("Piece added and saved to calendar!")


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
                        removed_piece = repertoireList.pop(idx)
                        with db_lock:
                            # 1. Delete the repertoire piece from the repertoire table
                            sqliteCursor.execute("DELETE FROM repertoire WHERE repID = ?", (removed_piece.repID,))
                            # 2. Delete all practice sessions linked to this repertoire piece
                            sqliteCursor.execute("DELETE FROM events WHERE repID = ? AND eventType = 'Pra'",
                                                 (removed_piece.repID,))
                            deleted_practices = sqliteCursor.rowcount
                            userCalendar.commit()
                        deleted = True
                        print(
                            f"Piece successfully deleted (along with {deleted_practices} linked practice session(s))!")
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
        print("-----< Thank you for using the Musical Practice Tracker >-----")
        menuLoop = False
    else:
        print("Invalid Character")
# ==============================================================================================================
