import os
import pickle
import tempfile
import unittest
from datetime import datetime
from unittest import mock

from main import (
    AddressBook, Record, Name, Phone, Birthday,
    add_contact, change_contact, show_phone,
    add_birthday, show_birthday, birthdays,
    add_email, add_address, parse_input, is_valid_email, load_data, save_data,
    get_data_path
)

# User data constants
VALID_USER = {
    "name": "Emily",
    "phone": "1234567890",
    "birthday": "01.01.2000",
    "birthday_date": datetime.strptime("01.01.2000", "%d.%m.%Y").date(),
    "email": "emily@mail.com",
    "address": "221B Baker Street"
}

INVALID_USER = {
    "name": "A",
    "phone": "1234",
    "birthday": "31-12-1990",
    "email": "wrong-email",
    "address": " "
}

ADDITIONAL_DATA = {
    "new_name": "John",
    "unknown_name": "__nonexistent_contact__",
    "new_phone": "0987654321",
    "extra_phone": "1112223333",
    "replaced_phone": "9998887777",
    "new_birthday": "02.02.2000"
}


class TestFieldClasses(unittest.TestCase):
    def test_valid_name(self):
        name = Name(VALID_USER["name"])
        self.assertEqual(name.value, VALID_USER["name"])

    def test_invalid_name(self):
        with self.assertRaises(Exception):
            Name(INVALID_USER["name"])

    def test_valid_phone(self):
        phone = Phone(VALID_USER["phone"])
        self.assertEqual(phone.value, VALID_USER["phone"])

    def test_invalid_phone(self):
        with self.assertRaises(Exception):
            Phone(INVALID_USER["phone"])

    def test_valid_birthday(self):
        b_day = Birthday(VALID_USER["birthday"])
        self.assertEqual(b_day.value, VALID_USER["birthday_date"])

    def test_invalid_birthday(self):
        with self.assertRaises(Exception):
            Birthday(INVALID_USER["birthday"])


class TestSaveLoad(unittest.TestCase):
    def setUp(self):
        self.book = AddressBook()
        self.record = Record(VALID_USER["name"])
        self.record.add_phone(VALID_USER["phone"])
        self.record.add_birthday(VALID_USER["birthday"])
        self.book.add_record(self.record)
        self.temp_file = tempfile.NamedTemporaryFile(delete=False)
        self.filename = os.path.basename(self.temp_file.name)
        self.temp_file.close()
        self.data_path = get_data_path(self.filename)

    def tearDown(self):
        if os.path.isfile(self.data_path):
            os.remove(self.data_path)

    def test_save_data_creates_file(self):
        save_data(self.book, self.filename)
        self.assertTrue(os.path.exists(self.data_path))

    def test_load_data_returns_correct_content(self):
        save_data(self.book, self.filename)
        loaded = load_data(self.filename)
        self.assertIsInstance(loaded, AddressBook)
        self.assertIn(VALID_USER["name"], loaded)
        self.assertEqual(
            loaded[VALID_USER["name"]].phones[0].value,
            VALID_USER["phone"]
        )

    def test_load_data_missing_file_returns_empty_book(self):
        if os.path.exists(self.data_path):
            os.remove(self.data_path)

        loaded = load_data(self.filename)
        self.assertIsInstance(loaded, AddressBook)
        self.assertEqual(len(loaded.data), 0)

    def test_load_data_corrupted_file(self):
        with open(self.data_path, 'w') as f:
            f.write("This is not valid pickle content.")

        loaded = load_data(self.filename)
        self.assertIsInstance(loaded, AddressBook)
        self.assertEqual(len(loaded.data), 0)

    def test_load_data_eof_error(self):
        with open(self.data_path, 'wb') as f:
            pass

        loaded = load_data(self.filename)
        self.assertIsInstance(loaded, AddressBook)
        self.assertEqual(len(loaded.data), 0)

    def test_load_data_generic_exception(self):
        with open(self.data_path, 'wb') as f:
            pickle.dump(self.book, f)

        with mock.patch("builtins.open",
                        side_effect=Exception("Mocked exception")):
            loaded = load_data(self.filename)
            self.assertIsInstance(loaded, AddressBook)
            self.assertEqual(len(loaded.data), 0)


class TestRecord(unittest.TestCase):
    def setUp(self):
        self.record = Record(VALID_USER["name"])

    def test_add_phone(self):
        self.record.add_phone(VALID_USER["phone"])
        self.assertEqual(self.record.phones[0].value, VALID_USER["phone"])

    def test_edit_phone_success(self):
        self.record.add_phone(VALID_USER["phone"])
        self.record.edit_phone(
            VALID_USER["phone"],
            ADDITIONAL_DATA["new_phone"]
        )
        self.assertEqual(
            self.record.phones[0].value,
            ADDITIONAL_DATA["new_phone"]
        )

    def test_edit_phone_failure(self):
        with self.assertRaises(Exception):
            self.record.edit_phone("0000000000", VALID_USER["phone"])

    def test_find_phone_found(self):
        self.record.add_phone(VALID_USER["phone"])
        phone = self.record.find_phone(VALID_USER["phone"])
        self.assertIsNotNone(phone)

    def test_find_phone_not_found(self):
        phone = self.record.find_phone("0000000000")
        self.assertIsNone(phone)

    def test_add_birthday(self):
        self.record.add_birthday(VALID_USER["birthday"])
        self.assertEqual(
            self.record.birthday.value,
            VALID_USER["birthday_date"]
        )

    def test_add_address_valid(self):
        result = self.record.add_address("Main Street")
        self.assertEqual(result, "Address added.")

    def test_add_address_invalid(self):
        with self.assertRaises(Exception):
            self.record.add_address(INVALID_USER["address"])

    def test_add_email(self):
        result = self.record.add_email(VALID_USER["email"])
        self.assertEqual(result, "Email added.")


class TestAddressBook(unittest.TestCase):
    def setUp(self):
        self.book = AddressBook()
        rec = Record(VALID_USER["name"])
        rec.add_phone(VALID_USER["phone"])
        rec.add_birthday(VALID_USER["birthday"])
        self.book.add_record(rec)

    def test_add_record(self):
        rec = Record(ADDITIONAL_DATA["new_name"])
        self.book.add_record(rec)
        self.assertIn(ADDITIONAL_DATA["new_name"], self.book)

    def test_find_record_found(self):
        result = self.book.find(VALID_USER["name"])
        self.assertIsNotNone(result)

    def test_find_record_not_found(self):
        result = self.book.find("Charlie")
        self.assertIsNone(result)

    def test_delete_record(self):
        self.book.delete(VALID_USER["name"])
        self.assertNotIn(VALID_USER["name"], self.book)

    def test_get_upcoming_birthdays(self):
        result = self.book.get_upcoming_birthdays()
        self.assertIsInstance(result, list)


class TestFunctions(unittest.TestCase):
    def setUp(self):
        self.book = AddressBook()
        rec = Record(VALID_USER["name"])
        rec.add_phone(VALID_USER["phone"])
        self.book.add_record(rec)

    def test_add_contact_valid(self):
        result = add_contact(
            [ADDITIONAL_DATA["new_name"], "0987654321"],
            self.book
        )
        self.assertIn(ADDITIONAL_DATA["new_name"], self.book)
        self.assertEqual(result, "Contact added.")

    def test_add_contact_invalid(self):
        result = add_contact(["OnlyName"], self.book)
        self.assertIn("Error:", result)

    def test_change_contact_valid(self):
        self.book[VALID_USER["name"]].add_phone(ADDITIONAL_DATA["extra_phone"])
        change_contact(
            [
                VALID_USER["name"],
                VALID_USER["phone"],
                ADDITIONAL_DATA["replaced_phone"]
            ],
            self.book
        )
        self.assertNotIn(
            VALID_USER["phone"],
            [p.value for p in self.book[VALID_USER["name"]].phones]
        )

    def test_change_contact_invalid(self):
        result = change_contact(
            [ADDITIONAL_DATA["new_name"], "000", "111"],
            self.book
        )
        self.assertIn("Error:", result)

    def test_show_phone_valid(self):
        result = show_phone([VALID_USER["name"]], self.book)
        self.assertEqual(result, "")

    def test_show_phone_invalid(self):
        result = show_phone([ADDITIONAL_DATA["unknown_name"]], self.book)
        self.assertIn("Error:", result)

    def test_add_birthday_valid(self):
        result = add_birthday(
            [VALID_USER["name"], ADDITIONAL_DATA["new_birthday"]],
            self.book
        )
        self.assertIn("Birthday added", result)

    def test_add_birthday_invalid(self):
        result = add_birthday(
            [
                ADDITIONAL_DATA["unknown_name"],
                INVALID_USER["birthday"]
            ],
            self.book
        )
        self.assertIn("Error:", result)

    def test_show_birthday_valid(self):
        self.book[VALID_USER["name"]].add_birthday(VALID_USER["birthday"])
        result = show_birthday([VALID_USER["name"]], self.book)
        self.assertEqual(result, "")

    def test_show_birthday_invalid(self):
        result = show_birthday([ADDITIONAL_DATA["unknown_name"]], self.book)
        self.assertIn("Error:", result)

    def test_add_address_valid(self):
        result = add_address(
            [VALID_USER["name"], VALID_USER["address"]],
            self.book
        )
        self.assertIn("Address added", result)

    def test_add_address_invalid(self):
        result = add_address(
            [ADDITIONAL_DATA["unknown_name"], "Street"],
            self.book
        )
        self.assertIn("Error:", result)

    def test_add_email_valid(self):
        result = add_email(
            [VALID_USER["name"], VALID_USER["email"]],
            self.book
        )
        self.assertEqual(result, "Email added.")

    def test_add_email_invalid_format(self):
        result = add_email(
            [VALID_USER["name"], INVALID_USER["email"]],
            self.book
        )
        self.assertIn("Error:", result)

    def test_add_email_invalid_name(self):
        result = add_email(
            [ADDITIONAL_DATA["unknown_name"], "email@mail.com"],
            self.book
        )
        self.assertIn("Error:", result)

    def test_parse_input_valid(self):
        result = parse_input(
            f"add {ADDITIONAL_DATA['new_name']} {VALID_USER['phone']}"
        )
        self.assertEqual(
            result,
            ("add", ADDITIONAL_DATA["new_name"], VALID_USER["phone"])
        )

    def test_parse_input_invalid(self):
        result = parse_input("")
        self.assertIn("Error:", result)

    def test_is_valid_email_true(self):
        self.assertTrue(is_valid_email(VALID_USER["email"]))

    def test_is_valid_email_false(self):
        self.assertFalse(is_valid_email(INVALID_USER["email"]))

    def test_birthdays_none(self):
        result = birthdays(self.book)
        self.assertEqual(result, "No upcoming birthdays.")


if __name__ == '__main__':
    unittest.main()
