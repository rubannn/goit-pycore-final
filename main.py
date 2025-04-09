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
    def __init__(self, name: str):
        if len(name.strip()) < 2:
            raise Exception(ERROR + "Name should contain at least 2 characters")
        super().__init__(name)


class Phone(Field):
    def __init__(self, value):
        if not re.fullmatch(r"\d{10}", value):
            raise Exception(
                ERROR
                + f'You input: {value}\nError: "Phone number format <only 10 digits>."'
            )
        super().__init__(value)


class Birthday(Field):
    def __init__(self, value):
        try:
            self.value = datetime.strptime(value, DATE_FORMAT).date()
        except ValueError:
            raise Exception(ERROR + "Invalid date format. Use DD.MM.YYYY")

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
        self.email = None
        self.address = None

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
        raise Exception(
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

    def add_address(self, address: str):
        """Додавання адреси"""
        if len(address.strip()) < 2:
            raise Exception(ERROR + "Address should contain at least 2 characters")

        self.address = address
        return "Address added."

    def add_email(self, email):
        """Додавання email адреси"""

        self.email = email
        return "Email added."

    def __str__(self):
        title_name = FIELD + "Contact name:" + RESET_ALL
        title_phones = FIELD + "phones:" + RESET_ALL
        title_birthday = FIELD + "birthday:" + RESET_ALL
        title_email = FIELD + "email:" + RESET_ALL
        title_address = FIELD + "address:" + RESET_ALL
        return f"{title_name} {self.name.value}, {title_phones} {'; '.join(p.value for p in self.phones)}, {title_birthday} {self.birthday if self.birthday else '---'}, {title_email} {self.email if self.email else '---'}, {title_address} {self.address if self.address else '---'}"


class AddressBook(UserDict):
    def add_record(self, record):
        """Додавання записів"""
        self.data[record.name.value] = record

    def add_notes(self, note):
        """Додавання записів"""
        self.data[note.tite] = note

    def find(self, name) -> Record:
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
                            "congratulation_date": birthday_this_year.strftime(
                                DATE_FORMAT
                            ),
                        }
                    )
                elif 0 <= delta_next <= days_count:
                    result.append(
                        {
                            "name": name,
                            "congratulation_date": birthday_next_year.strftime(
                                DATE_FORMAT
                            ),
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
        except Exception as e:
            return f"Error: {str(e)}"

    return inner


@input_error
def parse_input(user_input):
    """Розбирає введений користувачем рядок на команду та аргументи."""
    try:
        cmd, *args = user_input.split()
        cmd = cmd.strip().lower()
        return cmd, *args
    except Exception:
        raise Exception("There are no arguments passed")


@input_error
def add_contact(args, book: AddressBook):
    if len(args) < 2:
        raise Exception(
            '"add" command should contain 2 arguments "name" and "phone number"'
        )
    name, phone, *_ = args
    record = book.find(name)

    if record is None:
        record = Record(name)
        record.add_phone(phone)
        book.add_record(record)

    return "Contact added."


@input_error
def change_contact(args, book: AddressBook):
    """Змінює телефон існуючого контакту."""

    if len(args) < 3:
        raise Exception(
            "'change' command should contain 3 arguments: name, old_phone, new_phone"
        )
    name, old_phone, new_phone = args
    record = book.find(name)
    if record:
        return record.edit_phone(old_phone, new_phone)
    raise Exception(ERROR + f"Contact with name {name} not found.")

@as_table(title="Contact info")
@input_error
def show_phone(args, book):
    """Показує телефон контакту."""

    if not args:
        raise Exception("Contact name missing")

    name = args[0]
    record = book.find(name)
    if record:
        result = {"name": name}
        for i, phone in enumerate(record.phones, start=1):
            result[f"phone{i}"] = phone.value
        return [result]
    raise Exception(ERROR + f"Contact with name {name} not found.")


@input_error
def add_birthday(args, book: AddressBook):
    """Додає день народження до контакту."""

    if len(args) < 2:
        raise Exception(
            ERROR + '"add-birthday" command should contain 2 arguments "name" and "birthday" in format DD.MM.YYYY'
        )

    name, birthday = args
    record = book.find(name)
    if record:
        record.add_birthday(birthday)
        return "Birthday added."
    raise Exception(ERROR + f"Contact with name {name} not found.")

@as_table(title="Contact Birthday")
@input_error
def show_birthday(args, book):
    """Повертає дату дня народження контакту."""

    if len(args) < 1:
        raise Exception("Contact name missing")

    name = args[0]
    record = book.find(name)

    if not record:
        raise Exception(ERROR + f"Contact with name {name} not found.")
    if not record.birthday:
        raise Exception(ERROR + "Birthday not found.")

    return [{"name": record.name, "birthday": record.birthday}]


@as_table(title="Upcoming Birthdays")
@input_error
def birthdays(book):
    """Повертає список контактів із днями народження на наступний тиждень."""

    upcoming = book.get_upcoming_birthdays()
    if upcoming:
        return upcoming
    return "No upcoming birthdays."


@as_table(title="Address Book")
def show_all(book):
    """Повертає всі контакти у книзі у вигляді таблиці."""

    if not book:
        return "No contacts saved."
    else:
        return list(book.data.values())

@input_error
def add_address(args, book: AddressBook):
    """Додає адресу до контакту."""

    if len(args) < 2:
        raise Exception(
            ERROR + '"add-address" command should contain 2 arguments "name" and "address"'
        )

    name, *address = args
    record = book.find(name)
    if record:
        record.address = " ".join(address)
        return "Address added."
    raise Exception(ERROR + f"Contact with name {name} not found.")

@input_error
def add_email(args, book: AddressBook):
    """Додає email до контакту."""

    if len(args) < 2:
        raise Exception(
            ERROR + '"add-email" command should contain 2 arguments "name" and "email"'
        )

    name, email = args
    record = book.find(name)

    if not record:
        raise Exception(ERROR + f"Contact with name {name} not found.")
    elif not is_valid_email(email):
        raise Exception(ERROR + "❌ Invalid email format. Please enter a valid email like 'example@domain.com'. The email should contain:\n"
                 " - letters, digits, dots or dashes before the '@'\n"
                 " - a domain name after '@' (e.g. gmail, yahoo)\n"
                 " - and a domain zone like '.com', '.net', '.org', etc. (minimum 2 characters).")

    return record.add_email(email)


def is_valid_email(email) -> bool:
    """Валідатор для email адреси."""
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w{2,}$'
    return re.match(pattern, email) is not None

def get_data_path(filename="addressbook.pkl") -> str:
    """
    Get the full file path to the data file in the project directory.

    This function ensures that the 'data' folder exists inside the project
    directory and returns the full path to the specified filename.

    :param filename: The name of the file to store/load data.
    :type filename: str
    :return: Full path to the data file.
    :rtype: str
    """
    project_folder = os.getcwd()
    data_folder = os.path.join(project_folder, "data")
    os.makedirs(data_folder, exist_ok=True)
    return os.path.join(data_folder, filename)


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
    commands_list = {
        "hello": lambda args: "How can I help you?",
        "add": lambda args: add_contact(args, book),
        "change": lambda args: change_contact(args, book),
        "phone": lambda args: show_phone(args, book),
        "all": lambda args: show_all(book),
        "add-birthday": lambda args: add_birthday(args, book),
        "show-birthday": lambda args: show_birthday(args, book),
        "birthdays": lambda args: birthdays(book),
        "add-email": lambda args: add_email(args, book),
        "add-address": lambda args: add_address(args, book),
    }

    goodbye_message = "Good bye!"
    try:
        book = load_data()

        print("Welcome to the assistant bot!")
        while True:
            user_input = input("Enter a command: ")
            command, *args = parse_input(user_input)

            if command in ["close", "exit"]:
                print(goodbye_message)
                break

            elif command in commands_list:
                print(commands_list[command](args))

            else:
                print("Invalid command.")

    except KeyboardInterrupt:
        print(goodbye_message)

    finally:
        print("Saving data...")
        save_data(book)

if __name__ == "__main__":
    main()
