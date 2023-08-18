from datetime import datetime

dt = datetime.now()


def log_new_user(user):
    with open("./logs/users.txt", "a") as file:
        file.write(f"{dt} ADD {user.id} {user.username} {user.email}\n")


def log_delete_user(user_id):
    with open("./logs/users.txt", "a") as file:
        file.write(f"{dt} DELETE {user_id}\n")


def log_modify_user(user):
    with open("./logs/users.txt", "a") as file:
        file.write(f"{dt} UPDATE {user.id} {user.username} {user.email}\n")
