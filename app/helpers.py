
def init_app_secret(datastore_path):
    secret = ""

    path = "{}/secret.txt".format(datastore_path)

    try:
        with open(path, "r") as f:
            secret = f.read()

    except FileNotFoundError:
        import secrets
        with open(path, "w") as f:
            secret = secrets.token_hex(32)
            f.write(secret)

    return secret

def generate_random_instance_name():
    import random

    filename = "random-names.txt"
    candidates = [x.strip().lower() for x in open(filename, "r")]

    name = candidates[(random.randint(0, len(candidates) - 1))]
    name += "-" + candidates[(random.randint(0, len(candidates) - 1))]
    return name


def salted_password(password):
    import hashlib
    import base64
    import secrets

    # Make a new salt on every new password and store it with the password
    salt = secrets.token_bytes(32)

    key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    store = base64.b64encode(salt + key).decode('ascii')

    return store