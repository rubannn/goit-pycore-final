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
EMAIL_VALIDATION_ERROR = (
    "❌ Invalid email format. Please enter a valid email like 'example@domain.com'. The email should contain:\n"
    " - letters, digits, dots or dashes before the '@'\n"
    " - a domain name after '@' (e.g. gmail, yahoo)\n"
    " - and a domain zone like '.com', '.net', '.org', etc. (minimum 2 characters)."
)
BIRTHDAY_VALIDATION_ERROR = "Invalid date format. Use DD.MM.YYYY"


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
    def __init__(self, value: str):
        if not re.fullmatch(r"\d{10}", value):
            raise Exception(
                ERROR + f"Incorrect phone format {value}. Should be 10 digits."
            )
        super().__init__(value)

    def __str__(self):
        return self.value


class Birthday(Field):
    def __init__(self, value):
        try:
            self.value = datetime.strptime(value, DATE_FORMAT).date()
        except ValueError:
            raise Exception(ERROR + BIRTHDAY_VALIDATION_ERROR)

    def __str__(self):
        return self.value.strftime(DATE_FORMAT) if self.value else "---"


class Email(Field):
    def __init__(self, value):

        if is_valid_email(value):
            self.value = value
        else:
            raise Exception(ERROR + EMAIL_VALIDATION_ERROR)

    def __str__(self):
        return self.value if self.value else "---"


class Address(Field):
    pass


class Note:

    def __init__(self, title, text, tag=None):
        self.title = title
        self.note = text
        self.tag = tag


class Record:
    def __init__(self, name: str):
        self.name = Name(name)
        self.phones: list[Phone] = []
        self.birthday: Birthday = None
        self.email: Email = None
        self.address: Address = None

    def change_name(self, book, new_name):
        old_name = self.name.value
        self.name = Name(new_name)
        book.update_record_name(old_name, self)
        return "Contact updated."

    def add_phone(self, phone):
        """Додавання телефонів"""
        self.phones.append(Phone(phone))
        return "Contact updated."

    def remove_phone(self, phone):
        """Видалення телефонів"""
        self.phones = [p for p in self.phones if p.value != phone]

    def edit_phone(self, old_phone, new_phone):
        """Редагування телефонів"""
        for phone in self.phones:
            if phone.value == old_phone:
                phone.value = Phone(new_phone).value
                return "Contact updated."
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
        return "Contact updated."

    def add_address(self, address: str):
        """Додавання адреси"""
        if len(address.strip()) < 2:
            raise Exception(ERROR + "Address should contain at least 2 characters")

        self.address = Address(address)
        return "Address added."

    def add_email(self, email):
        """Додавання email адреси"""

        self.email = Email(email)
        return "Email added."

    def __str__(self):
        title_name = FIELD + "Contact name:" + RESET_ALL
        title_phones = FIELD + "phones:" + RESET_ALL
        title_birthday = FIELD + "birthday:" + RESET_ALL
        title_email = FIELD + "email:" + RESET_ALL
        title_address = FIELD + "address:" + RESET_ALL
        return f"{title_name} {self.name.value}, {title_phones} {'; '.join(p.value for p in self.phones)}, {title_birthday} {self.birthday if self.birthday else '---'}, {title_email} {self.email if self.email else '---'}, {title_address} {self.address if self.address else '---'}"


class AddressBook(UserDict):
    def __init__(self):
        super().__init__()
        self.notes = []

    def find(self, name):
        return self.data.get(name)

    def add_note(self, note):
        self.notes.append(note)

    def get_notes(self):
        return self.notes

    def delete_note(self, title):
        self.notes = [n for n in self.notes if n.title != title]

    def edit_note(self, title, new_text=None, new_tag=None):
        for note in self.notes:
            if note.title == title:
                if new_text:
                    note.note = new_text
                if new_tag:
                    note.tag = new_tag
                return
        raise Exception("Note with this title not found")

    def search_notes(args, book):
        if not args:
            return "Keyword required to search notes"
        keyword = args[0]
        return [
            n
            for n in book.notes
            if keyword.lower() in n.title.lower()
            or (n.tag and keyword.lower() in n.tag.lower())
        ]

    def add_record(self, record: Record):
        """Додавання записів"""
        self.data[record.name.value] = record

    def update_record_name(self, old_name: str, record: Record):
        self.delete(old_name)
        self.add_record(record)

    def add_notes(self, note):
        """Додавання записів"""
        self.data[note.tite] = note

    def find(self, name) -> Record:
        """Пошук записів за іменем"""
        return self.data.get(name, None)

    def get_all(self) -> list[Record]:
        return list(self.data.values())

    def delete(self, name):
        """Видалення записів за іменем"""
        if name in self.data:
            del self.data[name]
            return "Contact deleted"
        else:
            raise Exception(ERROR + f"Contact with name {name} not found.")

    def get_upcoming_birthdays(self, days_count):
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
            return ERROR + f"Error: {str(e)}"

    return inner


# @input_error
# def parse_input(user_input):
#     """Розбирає введений користувачем рядок на команду та аргументи."""
#     try:
#         cmd, *args = user_input.split()
#         cmd = cmd.strip().lower()
#         return cmd, *args
#     except Exception:
#         raise Exception("There are no arguments passed")


@input_error
def add_contact(book: AddressBook):
    name = input("Please type a name: ").strip()
    while len(name) < 2:
        name = input(
            "Please type a name or pass 'exit' to enter another command: "
        ).strip()
        if name == "exit":
            return

    record = book.find(name)

    if record is None:
        record = Record(name)
        phones = input(
            "Input phones in format: <ph1> <ph2> ... (each phone 10 digits length): "
        )
        for phone in phones.split():
            try:
                record.add_phone(phone)
            except Exception as e:
                raise Exception(str(e))

        if len(record.phones) < 1:
            return
        email = input("Add email or leave blanc: ")
        if len(email.strip()):
            try:
                record.add_email(email.strip())
            except Exception:
                print(ERROR + EMAIL_VALIDATION_ERROR)
                print("You can add email later using the command 'add-email'")
        birthday = input("Add birthday in format DD.MM.YYYY or leave blanc: ")
        if len(birthday.strip()):
            try:
                record.add_birthday(birthday.strip())
            except Exception:
                print(ERROR + BIRTHDAY_VALIDATION_ERROR)
                print("You can add birthday later using the command 'add-birthday'")
        address = input("Add address or leave blanc: ")
        if len(address.strip()):
            record.add_address(address)
        book.add_record(record)
    else:
        raise Exception(ERROR + f"contact with name {name} already exists")

    return "Contact added."


@input_error
def change_contact(book: AddressBook):
    """Змінює телефон існуючого контакту."""
    name = input("Please type a name: ").strip()
    record = book.find(name)
    if record:
        record_keys = list(record.__dict__.keys())
        input_message = f"Please pass one of the following fields that you want to change or pass 'exit': {record_keys}: "
        key = input(input_message).strip()
        while key not in record_keys:
            key = input(input_message).strip()
            if key == "exit":
                return "Operation cancelled"

        commands = {
            "phones": {
                "prompt": "Please pass old and new phones in format <ph1> <ph2>: ",
                "action": lambda data: record.edit_phone(*data.split()),
            },
            "name": {
                "prompt": "Please type a new name: ",
                "action": lambda data: record.change_name(book, data),
            },
            "birthday": {
                "prompt": "Please type birthday in format DD.MM.YYYY: ",
                "action": lambda data: record.add_birthday(data),
            },
            "email": {
                "prompt": "Please type email: ",
                "action": lambda data: record.add_email(data),
            },
            "address": {
                "prompt": "Please add address: ",
                "action": lambda data: record.add_address(data),
            },
        }
        if key in commands:
            user_input = input(commands[key]["prompt"])
            return commands[key]["action"](user_input)

    raise Exception(ERROR + f"Contact with name {name} not found.")


@as_table(title="Contact info")
@input_error
def show_phone(book: AddressBook):
    """Показує телефон контакту."""

    name = input("Please type a name: ")
    record = book.find(name)
    if record:
        result = {"name": name}
        for i, phone in enumerate(record.phones, start=1):
            result[f"phone{i}"] = phone.value
        return [result]
    raise Exception(ERROR + f"Contact with name {name} not found.")


@input_error
def add_birthday(book: AddressBook):
    """Додає день народження до контакту."""

    name = input("Please type a name: ")
    record = book.find(name)
    if record:
        birthday = input(
            "Please type a birthday in format DD.MM.YYYY (example 01.01.2000): "
        )
        return record.add_birthday(birthday)
    raise Exception(ERROR + f"Contact with name {name} not found.")


@as_table(title="Contact Birthday")
@input_error
def show_birthday(book):
    """Повертає дату дня народження контакту."""

    name = input("Please type a name: ").strip()
    record = book.find(name)

    if not record:
        raise Exception(ERROR + f"Contact with name {name} not found.")
    if not record.birthday:
        raise Exception(ERROR + f"Birthday for contact {name} not added yet.")

    return [{"name": record.name, "birthday": record.birthday}]


@as_table(title="Upcoming Birthdays")
@input_error
def birthdays(book: AddressBook):
    """Повертає список контактів із днями народження на наступний тиждень."""
    days_count = input(
        "Please enter the number of days within which you want to find upcoming birthdays: "
    )
    try:
        days_count = int(days_count)
    except ValueError:
        raise Exception(ERROR + "The value should be a positive integer")

    upcoming = book.get_upcoming_birthdays(days_count)
    if upcoming:
        return upcoming
    else:
        return f"No upcoming birthdays in {days_count} days"


@as_table(title="Address Book")
def show_all(book):
    """Повертає всі контакти у книзі у вигляді таблиці."""

    if not book:
        return "No contacts saved."
    else:
        return list(book.data.values())


@input_error
def add_address(book: AddressBook):
    """Додає адресу до контакту."""

    name = input("Please type a name: ")
    record = book.find(name)
    if record:
        address = input("Please type address: ")
        record.address = address
        return "Address added."
    raise Exception(ERROR + f"Contact with name {name} not found.")


@input_error
def add_email(book: AddressBook):
    """Додає email до контакту."""

    name = input("Please type a name: ")
    record = book.find(name)

    if not record:
        raise Exception(ERROR + f"Contact with name {name} not found.")

    email = input("Please type email: ")
    return record.add_email(email)


@as_table("Notes")
def show_notes(book):
    return book.get_notes()


@input_error
def add_note(args, book):
    title = input("Please type a title for the note: ").strip()
    while len(title) < 1:
        title = input(
            "Please type a title or pass 'exit' to enter another command: "
        ).strip()
        if title.lower() == "exit":
            return

    text = input("Please type the content of the note: ").strip()
    while len(text) < 1:
        text = input(
            "Note cannot be empty. Please enter text or type 'exit' to cancel: "
        ).strip()
        if text.lower() == "exit":
            return

    tag = input("Add tag (optional, format #tag) or leave blank: ").strip()
    if tag and not tag.startswith("#"):
        print("Invalid tag format. Tags should start with '#' (e.g., #todo).")
        print("You can edit the tag later using the 'edit-note' command.")
        tag = None

    note = Note(title, text, tag)
    book.add_note(note)

    return "Note added."

@input_error
def delete_note(args, book):
    if not args:
        raise Exception("Provide note title to delete")
    title = args[0]
    book.delete_note(title)
    return "Note deleted."


@input_error
def edit_note(args, book):
    if len(args) < 2:
        raise Exception("Use: edit-note title new_text [#tag]")
    title, *note = args
    tag = None
    if note[-1].startswith("#"):
        tag = note.pop()
    new_text = " ".join(note)
    book.edit_note(title, new_text, tag)
    return "Note updated."


@as_table(title="Found Notes:")
@input_error
def search_notes(args, book):
    if not args:
        raise Exception("Keyword required to search notes")

    keyword = args[0].lower()
    result = []
    for note in book.notes:
        if keyword in note.title.lower() or keyword in note.note.lower():
            result.append({
                "Title": note.title,
                "Note": note.note,
                "Tag": note.tag
                })

    if not result:
        raise Exception("No matching notes found.")

    return result


def is_valid_email(email) -> bool:
    """Валідатор для email адреси."""
    pattern = r"^[\w\.-]+@[\w\.-]+\.\w{2,}$"
    return re.match(pattern, email) is not None


def add_phone(book: AddressBook):
    name = input("Please type a name: ")
    record: Record = book.find(name)

    if not record:
        raise Exception(ERROR + f"Contact with name {name} not found.")

    phone = input("Please type phone: ")
    return record.add_phone(phone)


@as_table(title="Search Result")
def find_contact(book: AddressBook):
    all_records = book.get_all()
    value = input("Please pass a value for search: ").strip()

    for record in all_records:  # Проходим по всем записям в адресной книге
        record_dict = record.__dict__  # Получаем атрибуты записи как словарь

        for _, field_value in record_dict.items():
            if isinstance(field_value, list):
                for item in field_value:
                    if str(item) == str(value):
                        return [record]
            elif str(field_value) == value:
                return [record]

    return "Contact not found."


@input_error
def delete_contact(book: AddressBook):
    name = input("Please type a name: ").strip()
    return book.delete(name)


@as_table(title="Sort Notes by Tags Result")
def search_tags(book: AddressBook):
    value = input("Please pass a value for tag search: ").strip()

    result = []
    for note in book.notes:
        if note.tag and note.tag.lower() == value.lower():
            result.append({"Title": note.title, "Note": note.note, "Tag": note.tag})
    if result:
        return result
    return "Tag not found."

@as_table(title="Search Tags Result")
def sort_tags(book: AddressBook):
    return (
        sorted(book.notes, key=lambda x: (x.tag is None, x.tag or ""))
        if book.notes
        else "No notes found."
    )


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
    project_folder = os.path.dirname(os.path.abspath(__file__))

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

    path = get_data_path(filename)

    if not os.path.exists(path):
        return AddressBook()

    try:
        with open(path, "rb") as f:
            return pickle.load(f)
    except (FileNotFoundError, EOFError, pickle.UnpicklingError):
        return AddressBook()
    except Exception as e:
        print(
            f"Error {e} has occurred.\n"
            + f"We have handled this situation and you may proceed ☺️."
        )
        return AddressBook()


@as_table(title="Command list")
def greeting_message(commands_list):
    return [
        {"command": command, "description": commands_list[command]["description"]}
        for command in commands_list
    ]


def main():
    commands_list = {
        "exit": {"description": "Leave the app", "handler": None},
        "close": {"description": "Leave the app", "handler": None},
        "hello": {
            "description": "Greeting message",
            "handler": lambda: "How can I help you?",
        },
        "add": {
            "description": "Add new contact",
            "handler": lambda book: add_contact(book),
        },
        "change": {
            "description": "Change existing contact",
            "handler": lambda book: change_contact(book),
        },
        "add-phone": {
            "description": "Add phone to existing contact",
            "handler": lambda book: add_phone(book),
        },
        "add-email": {
            "description": "Add email to existing contact",
            "handler": lambda book: add_email(book),
        },
        "add-birthday": {
            "description": "Add birthday to existing contact",
            "handler": lambda book: add_birthday(book),
        },
        "add-address": {
            "description": "Add address to existing contact",
            "handler": lambda book: add_address(book),
        },
        "all": {
            "description": "Show all contacts",
            "handler": lambda book: show_all(book),
        },
        "phone": {
            "description": "Show the phone of existing contact",
            "handler": lambda book: show_phone(book),
        },
        "show-birthday": {
            "description": "Show birthday of existing contact",
            "handler": lambda book: show_birthday(book),
        },
        "birthdays": {
            "description": "Show upcoming birthdays for a given period of time",
            "handler": lambda book: birthdays(book),
        },
        "find": {
            "description": "Find contact by a given field",
            "handler": lambda book: find_contact(book),
        },
        "delete": {
            "description": "Delete contact",
            "handler": lambda book: delete_contact(book),
        },
        "add-note": {
            "description": "...Add description...",
            "handler": lambda args: add_note(args, book),
        },
        "show-notes": {
            "description": "...Add description...",
            "handler": lambda args: show_notes(book),
        },
        "edit-note": {
            "description": "...Add description...",
            "handler": lambda args: edit_note(args, book),
        },
        "delete-note": {
            "description": "...Add description...",
            "handler": lambda args: delete_note(args, book),
        },
        "search-notes": {
            "description": "...Add description...",
            "handler": lambda args: search_notes(args, book),
        },
        "search-tags": {
            "description": "Find notes by tag",
            "handler": lambda book: search_tags(book),
        },
        "sort-tags": {
            "description": "Sort notes by tag",
            "handler": lambda book: sort_tags(book),
        },
        "help": {
            "description": "Full list of commands",
            "handler": lambda _: greeting_message(commands_list),
        },
    }

    goodbye_message = "Good bye!"
    try:
        book = load_data()
        print("Welcome to the assistant bot!")
        print(greeting_message(commands_list))
        while True:
            command = input("Enter a command: ").strip()
            if command:
                command = command.lower().split()[0]

            if command in ["close", "exit"]:
                break

            elif command in commands_list:
                print(commands_list[command]["handler"](book))

            else:
                print("Invalid command.")

    except KeyboardInterrupt:
        print("\nSaving data...")
    finally:
        print(goodbye_message)
        save_data(book)


if __name__ == "__main__":
    main()
