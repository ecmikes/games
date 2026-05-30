import random


def main() -> None:
    print("Welcome to My Python Game!")
    print("Guess the secret number between 1 and 10.")

    secret = random.randint(1, 10)

    while True:
        guess_text = input("Enter your guess: ").strip()

        try:
            guess = int(guess_text)
        except ValueError:
            print("Please enter a whole number.")
            continue

        if not 1 <= guess <= 10:
            print("Please guess a number from 1 to 10.")
            continue

        if guess < secret:
            print("Too low. Try again.")
        elif guess > secret:
            print("Too high. Try again.")
        else:
            print("You win!")
            break


if __name__ == "__main__":
    main()
