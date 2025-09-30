from datetime import datetime

def get_valid_int_input(prompt):
    while True:
        value = input(prompt)
        if value.isdigit():
            return int(value)
        else:
            print("Please enter a valid whole number.")

def get_valid_float_input(prompt):
    while True:
        value = input(prompt)
        try:
            return float(value)
        except ValueError:
            print("Please enter a valid number (decimals allowed).")

def log_run():
    print("Please enter your stats. If not, you can enter a 0.")

    user_inputDistance = get_valid_float_input("Please enter distance in miles: ")
    print("Your distance was:", user_inputDistance, "miles")

    print("Enter the time of your activity (hours, minutes, seconds). If none, enter 0.")

    user_inputHours = get_valid_int_input("Hours (enter 0 if none): ")
    print("You entered", user_inputHours, "hours.")

    user_inputMinutes = get_valid_int_input("Minutes (enter 0 if none): ")
    print("You entered", user_inputMinutes, "minutes.")

    user_inputSeconds = get_valid_int_input("Seconds (enter 0 if none): ")
    print("You entered", user_inputSeconds, "seconds.")

    total_minutes = (user_inputHours * 60) + user_inputMinutes + (user_inputSeconds / 60)

    # Get timestamp before using it
    now = datetime.now()
    timestamp = now.strftime("%B %d, %Y at %I:%M %p")

    if user_inputDistance == 0:
        pace = None
    else:
        pace = total_minutes / user_inputDistance

    time_parts = []
    if user_inputHours > 0:
        time_parts.append(f"{user_inputHours} hour(s)")
    if user_inputMinutes > 0:
        time_parts.append(f"{user_inputMinutes} minute(s)")
    if user_inputSeconds > 0:
        time_parts.append(f"{user_inputSeconds} second(s)")

    time_string = ", ".join(time_parts)

    print("\n==================")
    print("  Run Summary")
    print("==================")
    print(f"Date       : {timestamp}")
    print(f"Distance   : {user_inputDistance:.2f} miles")
    print(f"Time       : {time_string}")
    if pace is None:
        print("Pace       : N/A (0 miles entered)")
    else:
        print(f"Pace       : {pace:.2f} minutes per mile")
    print("==================\n")

    # 📝 Save to file
    with open("runs.txt", "a") as file:
        file.write("--------------------------------------------------\n")
        file.write(f"Date     : {timestamp}\n")
        file.write(f"Distance : {user_inputDistance:.2f} miles\n")
        file.write(f"Time     : {time_string}\n")
        if pace is None:
            file.write("Pace     : N/A (0 miles entered)\n")
        else:
            file.write(f"Pace     : {pace:.2f} minutes per mile\n")
# ----------------- Now your menu -----------------
while True:
    print("Welcome to futureRunning!")
    print("1. Log a new run")
    print("2. View past runs")
    print("3. Exit")

    user_inputChoice = get_valid_int_input("Please enter 1, 2, or 3: ")

    if user_inputChoice == 1:
        log_run()
    elif user_inputChoice == 2:
        try:
            with open("runs.txt", "r") as file:
                content = file.read()
                if content.strip() == "":
                    print("No runs saved yet.")
                else:
                    print("\nHere are your saved runs:")
                    print(content)

                    # 🧠 Calculate average pace
                    lines = content.strip().split("\n")
                    total_distance = 0
                    total_time = 0

                    for line in lines:
                        if "Distance:" in line and "Pace:" in line:
                            try:
                                # Extract Distance
                                distance_part = line.split("Distance:")[1].split("miles")[0].strip()
                                distance = float(distance_part)

                                # Extract Pace
                                pace_part = line.split("Pace:")[1].strip().split()[0]
                                pace = float(pace_part)

                                total_distance += distance
                                total_time += distance * pace
                            except (IndexError, ValueError):
                                continue

                    if total_distance > 0:
                        avg_pace = total_time / total_distance
                        print(f"\nYour average pace across all runs: {avg_pace:.2f} minutes per mile")

                    # 🔴 Ask if user wants to clear runs
                    confirm = input(
                        "Would you like to clear your run history? (Type YES to confirm, or press Enter to cancel): ")
                    if confirm.upper() == "YES":
                        with open("runs.txt", "w") as clear_file:
                            pass
                        print("All run history has been cleared.")
                    else:
                        print("No changes made.")
        except FileNotFoundError:
            print("No runs file found. You have no saved runs yet.")