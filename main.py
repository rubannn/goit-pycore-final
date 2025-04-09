"""
Реалізуйте функціонал для збереження стану AddressBook у файл при закритті програми і відновлення стану при її запуску.
"""
import os
from collections import UserDict
import re
from datetime import datetime, date
import pickle

from colorama import init, Fore, Style
from rich.console import Console
from rich.table import Table
from functools import wraps


COLORS = ["cyan", "magenta", "green", "yellow", "blue", "bright_red", "white"]
init(autoreset=True)
ERROR = Fore.RED
FIELD = Fore.MAGENTA
RESET_ALL = Style.RESET_ALL

DATE_FORMAT = "%d.%m.%Y"


def as_table(title="Table"):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)

            # Проверка: если это не список или пустой список — вернём как есть
            if not isinstance(result, list) or not result:
                return result

            # Берём первое значение для определения полей
            first = result[0]
            if hasattr(first, "__dict__"):
                headers = list(first.__dict__.keys())
            elif isinstance(first, dict):
                headers = list(first.keys())
            else:
                return result  # не поддерживаемые типы

            table = Table(title=title)
            for i, h in enumerate(headers):
                table.add_column(h.capitalize(), style=COLORS[i % len(COLORS)])

            for item in result:
                row = []
                for h in headers:
                    value = (
                        getattr(item, h, None)
                        if hasattr(item, "__dict__")
                        else item.get(h, None)
                    )
                    if isinstance(value, list):
                        value = ", ".join(str(v) for v in value)
                    elif value is None:
                        value = "---"
                    else:
                        value = str(value)
                    row.append(value)
                table.add_row(*row)

            console = Console()
            console.print(table)
            return ""  # для предотвращения повторного вывода

        return wrapper

    return decorator


class Field:
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)


class Name(Field):
    pass


class Phone(Field):
    def __init__(self, value):
        if not re.fullmatch(r"\d{10}", value):
            print(
                ERROR
                + f'You input: {value}\nError: "Phone number format <only 10 digits>."'
            )
        super().__init__(value)


class Birthday(Field):
    def __init__(self, value):
        try:
            self.value = datetime.strptime(value, DATE_FORMAT).date()
        except ValueError:
            # raise ValueError("Invalid date format. Use DD.MM.YYYY")
            print(ERROR + "Invalid date format. Use DD.MM.YYYY")

    def __str__(self):
        return self.value.strftime(DATE_FORMAT) if self.value else "---"
class Note:
    def __init__(self):
        self.title = None
        self.note = None
        self.tag = None

class Record:
    def __init__(self, name):
        self.name = Name(name)
        self.phones = []
        self.birthday = None

    def add_phone(self, phone):
        """Додавання телефонів"""
        self.phones.append(Phone(phone))

    def remove_phone(self, phone):
        """Видалення телефонів"""
        self.phones = [p for p in self.phones if p.value != phone]

    def edit_phone(self, old_phone, new_phone):
        """Редагування телефонів"""
        for phone in self.phones:
            if phone.value == old_phone:
                phone.value = Phone(new_phone).value
                return
        print(
            ERROR + f'You want to change: {old_phone}\nError: "Phone number not found."'
        )

    def find_phone(self, search_phone):
        """Пошук телефону"""
        for phone in self.phones:
            if phone.value == search_phone:
                return phone
        return None

    def add_birthday(self, birthday):
        """Додавання дня народження"""
        self.birthday = Birthday(birthday)

    def __str__(self):
        title_name = FIELD + "Contact name:" + RESET_ALL
        title_phones = FIELD + "phones:" + RESET_ALL
        title_birthday = FIELD + "birthday:" + RESET_ALL
        return f"{title_name} {self.name.value}, {title_phones} {'; '.join(p.value for p in self.phones)}, {title_birthday} {self.birthday if self.birthday else '---'}"


class AddressBook(UserDict):
    def add_record(self, record):
        """Додавання записів"""
        self.data[record.name.value] = record

    def add_notes(self, note):
        """Додавання записів"""
        self.data[note.tite] = note

    def find(self, name):
        """Пошук записів за іменем"""
        return self.data.get(name, None)

    def delete(self, name):
        """Видалення записів за іменем"""
        if name in self.data:
            del self.data[name]

    def get_upcoming_birthdays(self):
        days_count = 300
        result = []
        today = datetime.today().date()
        for record in self.data.values():
            if record.birthday:
                name = record.name.value
                birthday = record.birthday.value
                birthday_this_year = date(today.year, birthday.month, birthday.day)
                birthday_next_year = date(today.year + 1, birthday.month, birthday.day)
                delta = (birthday_this_year - today).days
                delta_next = (birthday_next_year - today).days
                if 0 <= delta <= days_count:
                    result.append(
                        {
                            "name": name,
                            "congratulation_date": birthday_this_year.strftime(DATE_FORMAT),
                        }
                    )
                elif 0 <= delta_next <= days_count:
                    result.append(
                        {
                            "name": name,
                            "congratulation_date": birthday_next_year.strftime(DATE_FORMAT),
                        }
                    )
        return result

    def __str__(self):
        return "\n".join(str(record) for record in self.data.values())


def input_error(func):
    """Декоратор для обробки помилок введення користувача."""

    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValueError:
            return ERROR + f"\tGive me name and phone please. Format: <name> <phone>"
        except KeyError:
            return ERROR + f"\tContact not found."
        except IndexError:
            return ERROR + f"\tNot enough arguments provided."

    return inner


@input_error
def parse_input(user_input):
    """Розбирає введений користувачем рядок на команду та аргументи."""

    cmd, *args = user_input.split()
    cmd = cmd.strip().lower()
    return cmd, *args


@input_error
def add_contact(args, book: AddressBook):
    name, phone, *_ = args
    record = book.find(name)
    message = "Contact updated."
    if record is None:
        record = Record(name)
        book.add_record(record)
        message = "Contact added."
    if phone:
        record.add_phone(phone)
    return message


@input_error
def change_contact(args, book: AddressBook):
    """Змінює телефон існуючого контакту."""

    name, old_phone, new_phone = args
    record = book.find(name)
    if record:
        return record.edit_phone(old_phone, new_phone)
    return ERROR + "Contact not found."


@input_error
def show_phone(args, book):
    """Показує телефон контакту."""

    name = args[0]
    record = book.find(name)
    if record:
        return f"{name}: {', '.join(p.value for p in record.phones)}"
    return ERROR + "Contact not found."


@input_error
def add_birthday(args, book: AddressBook):
    """Додає день народження до контакту."""

    name, birthday = args
    record = book.find(name)
    if record:
        record.add_birthday(birthday)
        return "Birthday added."
    return ERROR + "Contact not found."


@input_error
def show_birthday(args, book):
    """Повертає дату дня народження контакту."""

    name = args[0]
    record = book.find(name)
    if record and record.birthday:
        return f"{name}'s birthday: {record.birthday}"
    return ERROR + "Birthday not found."


@as_table(title="Upcoming Birthdays")
@input_error
def birthdays(book):
    """Повертає список контактів із днями народження на наступний тиждень."""

    upcoming = book.get_upcoming_birthdays()
    if upcoming:
        return upcoming
        # return "Upcoming birthdays:\n" + "\n".join(
        #     f"{item['name']}: {item['congratulation_date']}" for item in upcoming
        # )
    return "No upcoming birthdays."


# def show_all(book):
#     """Повертає всі контакти у книзі."""

#     if not book:
#         return "No contacts saved."
#     return "\n".join(f"{record}" for record in book.data.values())


@as_table(title="Address Book")
def show_all(book):
    """Повертає всі контакти у книзі у вигляді таблиці."""

    if not book:
        return "No contacts saved."
    else:
        return list(book.data.values())


def get_data_path(filename="addressbook.pkl") -> str:
    """
    Get the full file path to the data file in the user's home directory.

    This function ensures that the application data folder exists and
    returns the full path to the specified filename.

    :param filename: The name of the file to store/load data.
    :type filename: str
    :return: Full path to the data file.
    :rtype: str
    """
    user_folder = os.path.expanduser("~")
    app_folder = os.path.join(user_folder, ".goit_personal_assistant")
    os.makedirs(app_folder, exist_ok=True)
    return os.path.join(app_folder, filename)


def save_data(book: AddressBook, filename="addressbook.pkl"):
    """
    Save the AddressBook instance to a data file using pickle.

    The file is saved in a hidden folder inside the user's home directory.

    :param book: The AddressBook instance to be saved.
    :type book: AddressBook
    :param filename: The name of the file to save to.
    :type filename: str
    """
    path = get_data_path(filename)
    with open(path, "wb") as f:
        pickle.dump(book, f)


def load_data(filename="addressbook.pkl") -> AddressBook:
    """
        Load the AddressBook instance from a data file using pickle.

        If the file does not exist, a new empty AddressBook is returned.

        :param filename: The name of the file to load from.
        :type filename: str
        :return: Loaded AddressBook instance or a new one if file not found.
        :rtype: AddressBook
        """
    try:
        path = get_data_path(filename)
        if os.path.exists(path):
            with open(path, "rb") as f:
                return pickle.load(f)
    except FileNotFoundError:
        return AddressBook()


def main():
    # book = AddressBook()
    book = load_data()

    print("Welcome to the assistant bot!")
    while True:
        user_input = input("Enter a command: ")
        command, *args = parse_input(user_input)

        if command in ["close", "exit"]:
            print("Good bye!")
            break

        elif command == "hello":
            print("How can I help you?")

        elif command == "add":
            print(add_contact(args, book))

        elif command == "change":
            print(change_contact(args, book))

        elif command == "phone":
            print(show_phone(args, book))

        elif command == "all":
            print(show_all(book))

        elif command == "add-birthday":
            print(add_birthday(args, book))

        elif command == "show-birthday":
            print(show_birthday(args, book))

        elif command == "birthdays":
            print(birthdays(book))

        else:
            print("Invalid command.")

    save_data(book)


if __name__ == "__main__":
    main()
