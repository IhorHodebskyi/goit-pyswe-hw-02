from collections import UserDict
from datetime import datetime, date, timedelta
import pickle
import atexit


from abc import ABC, abstractmethod

class View(ABC):
    """Абстрактний базовий клас для користувальницьких уявлень."""
    
    
    @abstractmethod
    def display_contact(self, contact):
        """Метод для відображення інформації про контакт."""
        pass
    
    @abstractmethod
    def display_message(self, message: str):
        """Метод для відображення повідомлення."""
        pass
    
    @abstractmethod
    def display_all_contacts(self, contacts):
        """Метод для відображення всіх контактів."""
        pass
    
    @abstractmethod
    def display_birthdays(self, birthdays):
        """Метод для відображення майбутніх днів народжень."""
        pass



class ConsoleView(View):
    """Конкретна реалізація для консольного інтерфейсу."""
    
    def display_contact(self, contact):
        """Виведення інформації про контакт у консоль."""
        print(f"Contact name: {contact.name.value}")
        print(f"Phones: {', '.join(p.value for p in contact.phones)}")
        print(f"Birthday: {contact.sow_birthday()}")
    
    def display_message(self, message: str):
        """Виведення повідомлення в консоль."""
        print(message)
    
    def display_all_contacts(self, contacts):
        """Виведення всіх контактів у консоль."""
        if not contacts:
            print("No contacts available.")
        for contact in contacts:
            self.display_contact(contact)
    
    def display_birthdays(self, birthdays):
        """Виведення майбутніх днів народжень у консоль."""
        if not birthdays:
            print("No upcoming birthdays.")
        for birthday in birthdays:
            print(f"{birthday['name']} - {birthday['congratulation_date']}")


def input_error(func: callable) -> callable:
    """Декоратор для обробки помилок."""

    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except KeyError:
            return "Contact not found."
        except ValueError as e:
            return str(e)
        except IndexError:
            return "Invalid input. Please provide the correct number of arguments."

    return wrapper


class Field:
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)


class Name(Field):
    def __init__(self, value):
        if not value:
            raise ValueError("Name is required.")
        super().__init__(value)


class Phone(Field):
    def __init__(self, value: str):
        if not isinstance(value, str) or not value.isdigit() or len(value) != 10:
            raise ValueError("Phone number must contain exactly 10 digits.")
        super().__init__(value)


class Birthday(Field):
    def __init__(self, value: str):
        try:
            date_value = datetime.strptime(value, "%d.%m.%Y")
            if date_value > datetime.now():
                raise ValueError("Birthday cannot be in the future.")
            super().__init__(date_value.strftime("%d.%m.%Y"))
        except ValueError:
            raise ValueError("Invalid date format. Use DD.MM.YYYY")


class Record:
    name = None

    def __init__(self, name):
        self.name = Name(name)
        self.phones = []
        self.birthday = None

    def add_phone(self, phone):
        self.phones.append(Phone(phone))

    def edit_phone(self, old_phone, new_phone):
        for p in self.phones:
            if p.value == old_phone:
                p.value = str(Phone(new_phone))
                return
        raise ValueError("Phone number not found.")

    def find_phone(self, phone: str):
        for p in self.phones:
            if p.value == phone:
                return p
        return None

    def remove_phone(self, phone):
        for p in self.phones:
            if p.value == phone:
                self.phones.remove(p)
                return ("Phone number removed")
        raise ValueError("Phone number not found.")

    def add_birthday(self, birthday):
        self.birthday = Birthday(birthday)

    def sow_birthday(self):
        return str(self.birthday) if self.birthday else "Birthday: None"

    def __str__(self):
        phones = '; '.join(p.value for p in self.phones) if self.phones else "No phones"
        birthday = self.birthday.value if self.birthday else "No birthday"
        return f"Contact name: {self.name.value}, phones: {phones}, birthday: {birthday}"


class AddressBook(UserDict):
    def __init__(self):
        super().__init__()

    def add_record(self, record):
        self.data[record.name.value] = record

    def find(self, name: str):
        return self.data.get(name, None)

    def delete(self, name):
        if name in self.data:
            del self.data[name]

    def __str__(self):
        if not self.data:
            return "Address book is empty."

        result = ["Address Book:"]
        for record in self.data.values():
            result.append(str(record))

        return "\n".join(result)

    @staticmethod
    def date_to_string(date: date) -> str:
        return date.strftime("%Y.%m.%d")

    @staticmethod
    def find_next_weekday(start_date: date, weekday: int) -> date:
        days_ahead = weekday - start_date.weekday()
        if days_ahead <= 0:
            days_ahead += 7
        return start_date + timedelta(days=days_ahead)

    @staticmethod
    def adjust_for_weekend(birthday: date) -> date:
        if birthday.weekday() >= 5:
            return AddressBook.find_next_weekday(birthday, 0)
        return birthday

    def save_data(self, filename="addressbook.pkl"):
        with open(filename, "wb") as f:
            pickle.dump(self, f)

    @staticmethod
    def load_data(filename="addressbook.pkl"):
        try:
            with open(filename, "rb") as f:
                return pickle.load(f)
        except FileNotFoundError:
            return AddressBook()

    def get_upcoming_birthdays(self, days=7) -> list:
        upcoming_birthdays = []
        today = date.today()

        for record in self.data.values():
            if not record.birthday:
                continue

            birthday_this_year = datetime.strptime(record.birthday.value, "%d.%m.%Y").date().replace(year=today.year)

            if birthday_this_year < today:
                birthday_this_year = birthday_this_year.replace(year=today.year + 1)

            birthday_this_year = self.adjust_for_weekend(birthday_this_year)

            if 0 <= (birthday_this_year - today).days <= days:
                congratulation_date_str = self.date_to_string(birthday_this_year)
                upcoming_birthdays.append({"name": record.name.value, "congratulation_date": congratulation_date_str})

        return upcoming_birthdays


def parse_input(user_input: str) -> tuple:
    parts = user_input.strip().split(" ")
    command = parts[0].lower()
    args = parts[1:]
    return command, args


@input_error
def add_contact(args: list, book: AddressBook, view: View) -> str:
    name, phone, *_ = args
    record = book.find(name)
    message = "Contact updated."
    if record is None:
        record = Record(name)
        book.add_record(record)
        message = "Contact added."
    if phone:
        record.add_phone(phone)

    view.display_message(message)
    return message


@input_error
def change_phone_number(args, book: AddressBook, view: View) -> str:
    if len(args) != 3:
        return "Invalid input. Please provide name, old phone, and new phone."

    name, old_phone, new_phone = args
    record = book.find(name)

    if record is None:
        return "Contact not found."

    try:
        record.edit_phone(old_phone, new_phone)
        view.display_message("Phone number changed successfully.")
    except ValueError:
        view.display_message("Old phone number not found in contact.")


@input_error
def show_all_contacts(book: AddressBook, view: View) -> str:
    view.display_all_contacts(book.data.values())

@input_error
def sow_contact_by_name(args: list, book: AddressBook, view: View) -> str:
    name = args[0]
    record = book.find(name)
    if record is None:
        view.display_message("Contact not found.")
    else:
        view.display_contact(record)


@input_error
def add_birthday(args: list, book: AddressBook, view: View) -> str:
    name, birthday = args
    record = book.find(name)
    if record is None:
        view.display_message("Contact not found.")
    else:
        record.add_birthday(birthday)
        view.display_message("Birthday added successfully.")


@input_error
def show_birthday(args: list, book: AddressBook, view: View) -> str:
    name = args[0]
    record = book.find(name)
    if record is None:
        view.display_message("Contact not found.")
    else:
        view.display_message(record.sow_birthday())


@input_error
def show_birthdays(book: AddressBook, view: View) -> str:
    birthdays = book.get_upcoming_birthdays()
    view.display_birthdays(birthdays)


def main():
    book = AddressBook.load_data()
    atexit.register(lambda: book.save_data())

    # Використовуємо конкретне представлення для консолі
    view = ConsoleView()

    print("Welcome to the assistant bot!")

    while True:
        user_input = input("Enter a command: ")
        command, args = parse_input(user_input)

        if command in ["close", "exit"]:
            view.display_message("Good bye!")
            break

        elif command == "hello":
            view.display_message("How can I help you?")

        elif command == "add":
            add_contact(args, book, view)

        elif command == "change":
            change_phone_number(args, book, view)

        elif command == "phone":
            sow_contact_by_name(args, book, view)

        elif command == "all":
            show_all_contacts(book, view)

        elif command == "add-birthday":
            add_birthday(args, book, view)

        elif command == "show-birthday":
            show_birthday(args, book, view)

        elif command == "birthdays":
            show_birthdays(book, view)

        else:
            view.display_message("Invalid command.")

def print_uml():
    uml = """
    +------------------+
    |      Field       |
    +------------------+
    | - value: str     |
    +------------------+
    | + __str__()      |
    +------------------+
          ▲
          │
    +------------------+   +------------------+   +------------------+
    |      Name        |   |     Phone        |   |    Birthday      |
    +------------------+   +------------------+   +------------------+
    | + __init__()     |   | + __init__()     |   | + __init__()     |
    +------------------+   +------------------+   +------------------+
          │                 │                  │
          └──────────┬──────┘                  │
                     │                         │
          +--------------------------------------+
          |               Record                 |
          +--------------------------------------+
          | - name: Name (1)                     |
          | - phones: list[Phone] (0..*)         |
          | - birthday: Birthday (0..1)          |
          +--------------------------------------+
          | + add_phone(phone: str)              |
          | + edit_phone(old, new)               |
          | + remove_phone(phone: str)           |
          | + add_birthday(birthday: str)        |
          | + show_birthday()                    |
          | + __str__()                          |
          +--------------------------------------+
                    ▲
                    │
          +--------------------------------------+
          |         AddressBook (UserDict)       |
          +--------------------------------------+
          | - records: dict[str, Record] (0..*) |
          +--------------------------------------+
          | + add_record(record: Record)         |
          | + find(name: str)                    |
          | + delete(name: str)                  |
          | + get_upcoming_birthdays()           |
          | + save_data(filename: str)           |
          | + load_data(filename: str)           |
          +--------------------------------------+

          +--------------------------------------+
          |          Main Functions              |
          +--------------------------------------+
          | + parse_input(user_input: str)       |
          | + add_contact(args, book)            |
          | + change_phone_number(args, book)    |
          | + show_all_contacts(book)            |
          | + show_contact_by_name(args, book)   |
          | + add_birthday(args, book)           |
          | + show_birthday(args, book)          |
          | + show_birthdays(book)               |
          | + main()                             |
          +--------------------------------------+
    """
    print(uml)





if __name__ == "__main__":
    print_uml()
    main()
