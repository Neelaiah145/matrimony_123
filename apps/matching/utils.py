from datetime import date


def calculate_age(date_of_birth):
    today = date.today()

    age = today.year - date_of_birth.year

    if (
        (today.month, today.day)
        < (date_of_birth.month, date_of_birth.day)
    ):
        age -= 1

    return age

def calculate_height_difference(user_height, candidate_height):
    return abs(float(user_height) - float(candidate_height))