import json
import re
import os
#pip install pandas
# import pandas as pd

# Clear Screen
def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')
    print(notification)


notification = ''

# Member Registration
def member_register():
    global notification

    # Read data from the database
    with open("member_detail.txt", "r") as file:
        lines = file.readlines()

    clear_screen()

    print("=== Member Registration ===")
    print("**Enter e in every input to back to previous page.  ")

    username = input("Username: ")
    if username.upper() == "E":
        notification = ""
        main_page()
        return

    if username == "":
        notification = "Username cannot be blank. "
        member_register()
        return

    if "," in username or " " in username:
        notification = "Invalid input, please enter a correct input. "
        member_register()
        return

    # Check for existing username
    for line in lines:
        data = line.strip().split(",")
        if len(data) == 4:
            if data[0] == username:
                notification = "This username already exists!"
                member_register()
                return

    phone_number = input("Phone Number: ")
    if phone_number.upper() == "E":
        notification = ""
        main_page()
        return

    if phone_number == "":
        notification = "Phone number cannot be blank. "
        member_register()
        return

    if "," in phone_number or " " in phone_number:
        notification = "Invalid input, please enter a correct input. "
        member_register()
        return

    # Check phone number format
    if phone_number.startswith("011") and re.match(r"^011[0-9]{8}$",phone_number):
        if not re.match(r"^011[0-9]{8}$", phone_number):
            notification = "Wrong format for phone number, please try again!"
            member_register()
            return

    elif phone_number.startswith("01") and re.match(r"^01[0-9]{8}$",phone_number):
        if not re.match(r"^01[0-9]{8}$", phone_number):
            notification = "Wrong format for phone number, please try again!"
            member_register()
            return
    else:
        notification = "Invalid phone number, please try again!"
        member_register()
        return

    # Check for existing phone number
    for line in lines:
        data = line.strip().split(",")
        if len(data) == 4:
            if data[1] == phone_number:
                notification = "This phone number already exists!"
                member_register()
                return

    email = input("Email: ")
    if email.upper() == "E":
        notification = ""
        main_page()
        return

    if email == "":
        notification = "Email cannot be blank. "
        member_register()
        return

    if "," in email or " " in email:
        notification = "Invalid input, please enter a correct input. "
        member_register()
        return

    # Check email format
    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        notification = "Wrong format for email, please try again!"
        member_register()
        return

    # Check for existing email
    for line in lines:
        data = line.strip().split(",")
        if len(data) == 4:
            if data[2] == email:
                notification = "This email already exists!"
                member_register()
                return

    password = input("Password: ")
    if password.upper() == "E":
        notification = ""
        main_page()
        return

    if password == "":
        notification = "Password cannot be blank. "
        member_register()
        return

    if "," in password or " " in password:
        notification = "Invalid input, please enter a correct input. "
        member_register()
        return

    # Check password length
    if len(password) <= 3:
        notification = "Password is too short!"
        member_register()
        return
    elif len(password) > 10:
        notification = "Password is too long!"
        member_register()
        return

    # Check if username, password same or not
    if username == password:
        notification = "Username and Password cannot be the same!"
        member_register()
        return

    confirm_password = input("Confirm Password: ")
    if confirm_password.upper() == "E":
        notification = ""
        main_page()
        return

    # Check if password and confirm password match
    if password != confirm_password:
        notification = "Password does not match!"
        member_register()
        return

    # Save data to the database
    with open("member_detail.txt", "a") as file:
        file.write(f"{username},{phone_number},{email},{password}\n")

    # Save data to the database in lowercase
    with open("member_detail_lowercase.txt", "a") as file:
        file.write(
        f"{username.lower()},{phone_number.lower()},{email.lower()},{password.lower()}\n"
        )

    notification = "Registration Successful! Please log in."
    member_login()


# Member Login
def member_login():
    global notification
    clear_screen()
    print("\n=== Member Login ==")
    print("**Enter e in every input to back to previous page.  ")

    global username
    username = input("Username: ")
    if username.upper() == "E":
        notification = ""
        main_page()
        return

    password = input("Password: ")
    if password.upper() == "E":
        notification = ""
        main_page()
        return

    # Read data from the database
    with open("member_detail.txt", "r") as file:
        lines = file.readlines()

    # Check if username and password match
    for line in lines:
        data = line.split(",")
        if data[0] == username:
            if data[3].rstrip() == password:
                member_page()
                return
            else:
                print("Wrong password!\n")

                # choice = input("Forgot password? (Y/N): ")
                # if choice.upper() == "Y":
                #     member_forgotpassword()
                #     return
                # elif choice.upper() == "N":
                #     member_login()
                #     return
                # else:
                #     print("Invalid choice! Please try again.")
                #     member_forgotpassword()
                #     return

    notification = "Username does not exist!"
    member_login()


# Admin Login
def admin_login():
    global notification
    clear_screen()
    print("\n=== Admin Login ===")
    print("**Enter e in every input to back to previous page.  ")

    global username
    username = input("Username: ")
    if username.upper() == "E":
        notification = ""
        main_page()
        return

    if username == "" or username == "," or username == " ": 
        notification = "Input blank, please enter a valid input. "
        admin_login()

    password = input("Password: ")
    if password.upper() == "E":
        notification = ""
        main_page()
        return

    if password == "" or password == "," or password == " ": 
        notification = "Input blank, please enter a valid input. "
        admin_login()


    # Check if username and password are the same
    if username == password:
        notification = "Username and password cannot be the same!"
        admin_login()
        return

    # Read data from the database
    with open("admin_detail.txt", "r") as file:
        lines = file.readlines()

    # Check if username and password match
    for line in lines:
        data = line.split(",")
        if data[0] == username:
            if data[3].rstrip() == password:
                admin_page()
                return
            else:
                print("Wrong password!\n")

                choice = input("Forgot password? (Y/N): ")
                # if choice.upper() == "Y":
                #     admin_forgotpassword()
                #     return
                # elif choice.upper() == "N":
                #     admin_login()
                #     return
                # else:
                #     print("Invalid choice! Please try again.")
                #     admin_forgotpassword()
                #     return

    notification = "Username does not exist!"
    admin_login()


# Member Page
def member_page():
    global notification
    clear_screen()
    print("=== Member Page ===")


# Admin Page
def admin_page():
    global notification
    clear_screen()
    print("=== Member Page ===")


# Main Page
def main_page():
  global notification
  clear_screen()
  print("=== SecondLife ===")
  print("1. Member Login")
  print("2. Admin Login")
  print("3. Member Registration")

  choice = input("Enter your choice: ")

  if choice == "1":
    notification = ''
    member_login()
  elif choice == "2":
    notification = ''
    admin_login()
  elif choice == "3":
    notification = ''
    member_register()

  else:
    notification = "Invalid choice. Please try again."
    main_page()


main_page()
