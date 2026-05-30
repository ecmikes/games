import random


def main() -> None:
    print("Welcome to My Python Game!")
    print("Guess the secret number between 1 and 10.")

    secret = random.randint(1, 10)

    while True:
        guess_text = input("Enter your guess: ").strip()

        if not guess_text.isdigit():
            print("Please enter a whole number.")
            continue

        guess = int(guess_text)

        if guess < secret:
            print("Too low. Try again.")
        elif guess > secret:
            print("Too high. Try again.")
        else:
            print("You win!")
            break


if __name__ == "__main__":
    main()
