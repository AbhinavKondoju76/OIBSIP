import random
import string


def generate_password(length, use_upper, use_lower, use_digits, use_symbols):
    characters = ""
    password = []

    if use_upper:
        characters += string.ascii_uppercase
        password.append(random.choice(string.ascii_uppercase))

    if use_lower:
        characters += string.ascii_lowercase
        password.append(random.choice(string.ascii_lowercase))

    if use_digits:
        characters += string.digits
        password.append(random.choice(string.digits))

    if use_symbols:
        characters += string.punctuation
        password.append(random.choice(string.punctuation))

    while len(password) < length:
        password.append(random.choice(characters))

    random.shuffle(password)
    return "".join(password)


print("=" * 40)
print("      RANDOM PASSWORD GENERATOR")
print("=" * 40)

while True:

    # Password Length
    while True:
        try:
            length = int(input("\nEnter password length (Minimum 8): "))

            if length < 8:
                print("Password must be at least 8 characters.")
            else:
                break

        except ValueError:
            print("Please enter a valid number.")

    print("\nSelect character types (Y/N):")

    upper = input("Include Uppercase Letters? ").strip().lower() == "y"
    lower = input("Include Lowercase Letters? ").strip().lower() == "y"
    digits = input("Include Numbers? ").strip().lower() == "y"
    symbols = input("Include Symbols? ").strip().lower() == "y"

    selected = sum([upper, lower, digits, symbols])

    if selected < 2:
        print("\nError: Select at least TWO character types.")
        continue

    password = generate_password(
        length,
        upper,
        lower,
        digits,
        symbols
    )

    print("\nGenerated Password:")
    print(password)

    again = input("\nGenerate another password? (Y/N): ").strip().lower()

    if again != "y":
        print("\nThank you for using Password Generator!")
        break