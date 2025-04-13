from faker import Faker
import random
from main import AddressBook, Record, Note

fake = Faker()


def generate_fake_contacts(book: AddressBook, num_contacts=10):
    """Генерує фейкові контакти та додає їх до AddressBook."""
    for _ in range(num_contacts):
        try:
            record = Record(f"{fake.first_name()} {fake.last_name()}")

            # Додаємо телефони (1-3 номери)
            for _ in range(random.randint(1, 3)):
                phone = fake.numerify(text="##########")  # 10 цифр
                record.add_phone(phone)

            # Додаємо email (50% ймовірність)
            if random.choice([True, False]):
                record.add_email(fake.email())

            # Додаємо день народження (50% ймовірність)
            if random.choice([True, False]):
                birth_date = fake.date_of_birth(minimum_age=18, maximum_age=90)
                record.add_birthday(birth_date.strftime("%d.%m.%Y"))

            # Додаємо адресу (50% ймовірність)
            if random.choice([True, False]):
                record.add_address(fake.address().replace("\n", ", "))

            book.add_record(record)
        except Exception as e:
            print(f"Error generating fake contact: {e}")


def generate_fake_notes(book: AddressBook, num_notes=5):
    """Генерує фейкові нотатки та додає їх до AddressBook."""
    tags = ["#work", "#personal", "#family", "#friends", "#todo", None]
    for _ in range(num_notes):
        title = fake.sentence(nb_words=3)[:-1]  # Прибираємо крапку в кінці
        text = fake.paragraph(nb_sentences=3)
        tag = random.choice(tags)
        book.add_note(Note(title, text, tag))


def fill_with_fake_data(book: AddressBook, num_contacts=10, num_notes=5):
    """Заповнює AddressBook фейковими даними."""
    print("Generating fake data...")
    generate_fake_contacts(book, num_contacts)
    generate_fake_notes(book, num_notes)
    return f"Generated {num_contacts} contacts and {num_notes} notes."
