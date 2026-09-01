from database import get_user


def is_admin(user_id):
    user = get_user(user_id)

    return bool(user and user[4] == 1)


def is_allowed(user_id):
    user = get_user(user_id)

    if not user:
        return False

    if user[5] == 1:
        return False

    return bool(user[3] == 1 or user[4] == 1)