"""Unit tests for the main Assistant Bot functionality."""

import os
import pickle
import tempfile
import unittest
from datetime import datetime
from unittest import mock
from unittest.mock import patch

from main import (
    AddressBook,
    Birthday,
    Name,
    Note,
    Phone,
    Record,
    add_address,
    add_birthday,
    add_contact,
    add_email,
    add_note,
    add_phone,
    birthdays,
    change_contact,
    delete_contact,
    delete_note,
    edit_note,
    find_contact,
    get_data_path,
    greeting_message,
    is_valid_email,
    load_data,
    predict_command,
    save_data,
    search_note,
    search_tags,
    show_all,
    show_birthday,
    show_notes,
    show_phone,
    sort_tags,
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
    """Unit tests for individual field classes like Name, Phone & Birthday."""

    def test_valid_name(self):
        """Test that a valid name is accepted and stored correctly."""
        name = Name(VALID_USER["name"])
        self.assertEqual(name.value, VALID_USER["name"])

    def test_invalid_name(self):
        """Test that an invalid name raises an exception."""
        with self.assertRaises(Exception):
            Name(INVALID_USER["name"])

    def test_valid_phone(self):
        """Test that a valid phone number is accepted and stored correctly."""
        phone = Phone(VALID_USER["phone"])
        self.assertEqual(phone.value, VALID_USER["phone"])

    def test_invalid_phone(self):
        """Test that an invalid phone number raises an exception."""
        with self.assertRaises(Exception):
            Phone(INVALID_USER["phone"])

    def test_valid_birthday(self):
        """Test that a valid birthday string is correctly parsed into date."""
        b_day = Birthday(VALID_USER["birthday"])
        self.assertEqual(b_day.value, VALID_USER["birthday_date"])

    def test_invalid_birthday(self):
        """Test that an invalid birthday string raises an exception."""
        with self.assertRaises(Exception):
            Birthday(INVALID_USER["birthday"])


class TestNotes(unittest.TestCase):
    """Unit tests for the note-related functionality in AddressBook."""

    def setUp(self):
        """Set up function per test within class."""
        self.book = AddressBook()

    def test_show_notes_output(self):
        """Test that show_notes returns correct string representation."""
        self.book.add_note(Note("Note1", "Some content"))
        result = show_notes(self.book)
        self.assertEqual(result, "")

    def test_add_note(self):
        """Test that a new note can be added with a tag."""
        with patch(
                "builtins.input",
                side_effect=["Todo", "Buy milk", "#personal"]
        ):
            result = add_note(self.book)
            self.assertEqual(result, "Note added.")
            self.assertEqual(len(self.book.notes), 1)

    def test_add_note_without_tag(self):
        """Test that a note can be added without providing a tag."""
        with patch(
                "builtins.input",
                side_effect=["Work", "Finish report", ""]
        ):
            result = add_note(self.book)
            self.assertEqual(result, "Note added.")
            self.assertEqual(self.book.notes[0].tag, "")

    def test_edit_note_text(self):
        """Test that the text of a note can be updated correctly."""
        self.book.add_note(Note("Plan", "Initial text", "#old"))
        with patch(
                "builtins.input",
                side_effect=["Plan", "note", "Updated content"]
        ):
            result = edit_note(self.book)
        self.assertIn("updated", result.lower())
        self.assertEqual(self.book.notes[0].note, "Updated content")
        self.assertEqual(self.book.notes[0].tag, "#old")

    def test_edit_note_tag(self):
        """Test that the tag of a note can be updated correctly."""
        self.book.add_note(Note("Plan", "Some text", "#old"))
        with patch(
                "builtins.input",
                side_effect=["Plan", "tag", "#new"]
        ):
            result = edit_note(self.book)
        self.assertIn("updated", result.lower())
        self.assertEqual(self.book.notes[0].note,"Some text")
        self.assertEqual(self.book.notes[0].tag, "#new")

    def test_delete_note(self):
        """Test that a note can be deleted by its title."""
        self.book.add_note(Note("Shopping", "Eggs and milk"))
        with patch("builtins.input", side_effect=["title", "Shopping"]):
            result = delete_note(self.book)
        self.assertIn("Deleted", result)
        self.assertEqual(len(self.book.notes), 0)

    def test_search_notes_by_title(self):
        """Test that searching notes by title returns expected result."""
        self.book.add_note(Note("Trip", "Pack luggage", "#travel"))
        with patch("builtins.input", return_value="Trip"):
            result = search_note(self.book)
        self.assertEqual(result, "")

    def test_search_notes_no_result(self):
        """Test that searching for an unknown note title returns error."""
        self.book.notes = []
        result = search_note(["Unknown"], self.book)
        self.assertIn("Error:", result)

    def test_search_tags_found(self):
        """Test that searching by tag returns correct notes."""
        self.book.add_note(Note("Meeting", "Discuss agenda", "#work"))
        with patch("builtins.input", return_value="#work"):
            result = search_tags(self.book)
        self.assertEqual(result, "")

    def test_sort_tags(self):
        """Test that notes are sorted alphabetically by tag."""
        self.book.add_note(Note("B", "content", "#beta"))
        self.book.add_note(Note("A", "content", "#alpha"))
        self.book.add_note(Note("None", "no tag"))
        result = sort_tags(self.book)
        self.assertEqual(result, "")


class TestUtils(unittest.TestCase):
    """Unit tests for utility functions like command prediction & greetings."""

    def test_predict_command_found(self):
        """Test that a close match is found by predict_command."""
        commands = {
            "add": {"description": "Add contact"},
            "delete": {"description": "Delete contact"},
        }
        result = predict_command(commands, 50, candidate="adde")
        self.assertEqual(result, "")

    def test_predict_command_not_found(self):
        """Test that predict_command returns empty for unknown candidate."""
        commands = {"add": {}, "show": {}}
        result = predict_command(commands, 90, candidate="xyz")
        self.assertEqual(result, "")

    def test_greeting_message_output(self):
        """Test that greeting_message returns a formatted help message."""
        commands = {
            "add": {"description": "Add contact"},
            "delete": {"description": "Delete contact", "end-section": True},
        }
        result = greeting_message(commands)
        self.assertEqual(result, "")


class TestSaveLoad(unittest.TestCase):
    """Unit tests for save/load logic and file error handling."""

    def setUp(self):
        """Set up function per test within class."""
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
        """Clean up function per test within class."""
        if os.path.isfile(self.data_path):
            os.remove(self.data_path)

    def test_get_data_path_folder_created(self):
        """Test that get_data_path creates the folder if not present."""
        path = get_data_path("temp_test_file.pkl")
        self.assertTrue(os.path.exists(os.path.dirname(path)))

    def test_save_data_creates_file(self):
        """Test that save_data correctly creates a file."""
        save_data(self.book, self.filename)
        self.assertTrue(os.path.exists(self.data_path))

    def test_load_data_returns_correct_content(self):
        """Test that load_data returns AddressBook with expected content."""
        save_data(self.book, self.filename)
        loaded = load_data(self.filename)
        self.assertIsInstance(loaded, AddressBook)
        self.assertIn(VALID_USER["name"], loaded)
        self.assertEqual(
            loaded[VALID_USER["name"]].phones[0].value,
            VALID_USER["phone"]
        )

    def test_load_data_missing_file_returns_empty_book(self):
        """Test that loading from a non-existent file returns empty book."""
        if os.path.exists(self.data_path):
            os.remove(self.data_path)

        loaded = load_data(self.filename)
        self.assertIsInstance(loaded, AddressBook)
        self.assertEqual(len(loaded.data), 0)

    def test_load_data_corrupted_file(self):
        """Test that corrupted pickle file returns empty AddressBook."""
        with open(self.data_path, 'w') as f:
            f.write("This is not valid pickle content.")

        loaded = load_data(self.filename)
        self.assertIsInstance(loaded, AddressBook)
        self.assertEqual(len(loaded.data), 0)

    def test_load_data_eof_error(self):
        """Test that EOFError is handled gracefully."""
        with open(self.data_path, 'wb'):
            pass

        loaded = load_data(self.filename)
        self.assertIsInstance(loaded, AddressBook)
        self.assertEqual(len(loaded.data), 0)

    def test_load_data_generic_exception(self):
        """Test that unexpected exceptions during load return empty book."""
        with open(self.data_path, 'wb') as f:
            pickle.dump(self.book, f)

        with mock.patch("builtins.open",
                        side_effect=Exception("Mocked exception")):
            loaded = load_data(self.filename)
            self.assertIsInstance(loaded, AddressBook)
            self.assertEqual(len(loaded.data), 0)


class TestRecord(unittest.TestCase):
    """Unit tests for the Record class."""

    def setUp(self):
        """Set up function per test within class."""
        self.record = Record(VALID_USER["name"])

    def test_add_phone(self):
        """Test that a phone number is added to the record."""
        self.record.add_phone(VALID_USER["phone"])
        self.assertEqual(self.record.phones[0].value, VALID_USER["phone"])

    def test_edit_phone_success(self):
        """Test that an existing phone number is updated correctly."""
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
        """Test that editing a non-existent phone raises an exception."""
        with self.assertRaises(Exception):
            self.record.edit_phone("0000000000", VALID_USER["phone"])

    def test_find_phone_found(self):
        """Test that an existing phone number is found in the record."""
        self.record.add_phone(VALID_USER["phone"])
        phone = self.record.find_phone(VALID_USER["phone"])
        self.assertIsNotNone(phone)

    def test_find_phone_not_found(self):
        """Test that searching for an unknown phone returns None."""
        phone = self.record.find_phone("0000000000")
        self.assertIsNone(phone)

    def test_add_birthday(self):
        """Test that a birthday is correctly added and parsed."""
        self.record.add_birthday(VALID_USER["birthday"])
        self.assertEqual(
            self.record.birthday.value,
            VALID_USER["birthday_date"]
        )

    def test_add_address_valid(self):
        """Test that a valid address is added to the record."""
        result = self.record.add_address("Main Street")
        self.assertEqual(result, "Address added.")

    def test_add_address_invalid(self):
        """Test that an invalid address raises an exception."""
        with self.assertRaises(Exception):
            self.record.add_address(INVALID_USER["address"])

    def test_add_email(self):
        """Test that a valid email address is added to the record."""
        result = self.record.add_email(VALID_USER["email"])
        self.assertEqual(result, "Email added.")


class TestAddressBook(unittest.TestCase):
    """Unit tests for AddressBook class: adding, finding, deleting records."""

    def setUp(self):
        """Set up function per test within class."""
        self.book = AddressBook()
        rec = Record(VALID_USER["name"])
        rec.add_phone(VALID_USER["phone"])
        rec.add_birthday(VALID_USER["birthday"])
        self.book.add_record(rec)

    def test_add_record(self):
        """Test that a new record is added to the address book."""
        rec = Record(ADDITIONAL_DATA["new_name"])
        self.book.add_record(rec)
        self.assertIn(ADDITIONAL_DATA["new_name"], self.book)

    def test_find_record_found(self):
        """Test that an existing record can be found by name."""
        result = self.book.find(VALID_USER["name"])
        self.assertIsNotNone(result)

    def test_find_record_not_found(self):
        """Test that searching for an unknown name returns None."""
        result = self.book.find("Charlie")
        self.assertIsNone(result)

    def test_delete_record(self):
        """Test that a record is removed from the address book."""
        self.book.delete(VALID_USER["name"])
        self.assertNotIn(VALID_USER["name"], self.book)

    def test_get_upcoming_birthdays(self):
        """Test that upcoming birthdays are returned as a list."""
        result = self.book.get_upcoming_birthdays(7)
        self.assertIsInstance(result, list)


class TestFunctions(unittest.TestCase):
    """Integration tests for user-level command functions on AddressBook."""

    def setUp(self):
        """Set up function per test within class."""
        self.book = AddressBook()
        rec = Record(VALID_USER["name"])
        rec.add_phone(VALID_USER["phone"])
        self.book.add_record(rec)

    def test_delete_contact_valid(self):
        """Test that an existing contact is deleted successfully."""
        self.book.add_record(Record("Temp"))
        with patch("builtins.input", return_value="Temp"):
            result = delete_contact(self.book)
        self.assertEqual(result, "Contact deleted")

    def test_find_contact_found(self):
        """Test that searching for an existing phone returns contact info."""
        with patch("builtins.input", return_value=VALID_USER["phone"]):
            result = find_contact(self.book)
        self.assertEqual(result, "")

    def test_find_contact_not_found(self):
        """Test that searching for an unknown contact returns error message."""
        with patch("builtins.input", return_value="NoMatch"):
            result = find_contact(self.book)
        self.assertEqual(result, "Contact not found.")

    def test_delete_contact_invalid(self):
        """Test that deleting a non-existent contact returns an error."""
        with patch("builtins.input", return_value="Ghost"):
            result = delete_contact(self.book)
        self.assertIn("Error:", result)

    def test_show_all_contacts(self):
        """Test that all contacts are displayed correctly."""
        result = show_all(self.book)
        self.assertEqual(result, "")

    def test_add_phone_valid(self):
        """Test that a phone number is added to an existing contact."""
        self.book.add_record(Record(ADDITIONAL_DATA["new_name"]))
        with patch("builtins.input", side_effect=[
            ADDITIONAL_DATA["new_name"],
            ADDITIONAL_DATA["new_phone"]
        ]):
            result = add_phone(self.book)
            self.assertEqual(result, "Contact updated.")
            self.assertEqual(
                self.book[ADDITIONAL_DATA["new_name"]].phones[0].value,
                ADDITIONAL_DATA["new_phone"]
            )

    def test_add_phone_invalid_then_exit(self):
        """Test that invalid phone input is handled and exits correctly."""
        self.book.add_record(Record(ADDITIONAL_DATA["new_name"]))
        with patch("builtins.input", side_effect=[
            ADDITIONAL_DATA["new_name"],
            "123",
            "exit"
        ]):
            result = add_phone(self.book)
            self.assertIn("Incorrect phone format", result)
            self.assertEqual(
                len(self.book[ADDITIONAL_DATA["new_name"]].phones), 0
            )

    def test_add_contact_valid(self):
        """Test that a new contact is added correctly with minimal data."""
        with patch(
                "builtins.input",
                side_effect=[
                    ADDITIONAL_DATA["new_name"],
                    "0987654321", "", "", ""
                ]
        ):
            result = add_contact(self.book)
            self.assertIn(ADDITIONAL_DATA["new_name"], self.book)
            self.assertEqual(result, "Contact added.")

    def test_add_contact_invalid(self):
        """Test that add_contact returns error if args are malformed."""
        result = add_contact(["OnlyName"], self.book)
        self.assertIn("Error:", result)

    def test_change_contact_valid(self):
        """Test that an existing contact's phone is successfully replaced."""
        self.book[VALID_USER["name"]].add_phone(ADDITIONAL_DATA["extra_phone"])
        with patch("builtins.input", side_effect=[
            VALID_USER["name"],
            "phones",
            f"{VALID_USER['phone']} {ADDITIONAL_DATA['replaced_phone']}"
        ]):
            change_contact(self.book)

        self.assertNotIn(
            VALID_USER["phone"],
            [p.value for p in self.book[VALID_USER["name"]].phones]
        )
        self.assertIn(
            ADDITIONAL_DATA["replaced_phone"],
            [p.value for p in self.book[VALID_USER["name"]].phones]
        )

    def test_change_contact_invalid(self):
        """Test that change_contact returns error if data is invalid."""
        result = change_contact(
            [ADDITIONAL_DATA["new_name"], "000", "111"],
            self.book
        )
        self.assertIn("Error:", result)

    def test_show_phone_valid(self):
        """Test that phone number of an existing contact is shown correctly."""
        with patch("builtins.input", return_value=VALID_USER["name"]):
            result = show_phone(self.book)
        self.assertEqual(result, "")

    def test_show_phone_invalid(self):
        """Test that showing phone number for unknown contact returns error."""
        result = show_phone([ADDITIONAL_DATA["unknown_name"]], self.book)
        self.assertIn("Error:", result)

    def test_add_birthday_valid(self):
        """Test that a valid birthday is added to an existing contact."""
        with patch(
            "builtins.input",
            side_effect=[VALID_USER["name"], ADDITIONAL_DATA["new_birthday"]]
        ):
            result = add_birthday(self.book)
        self.assertIn("Contact updated", result)

    def test_add_birthday_invalid(self):
        """Test that adding birthday to unknown contact returns error."""
        result = add_birthday(
            [ADDITIONAL_DATA["unknown_name"], INVALID_USER["birthday"]],
            self.book
        )
        self.assertIn("Error:", result)

    def test_show_birthday_valid(self):
        """Test that birthday is shown for a valid contact."""
        self.book[VALID_USER["name"]].add_birthday(VALID_USER["birthday"])
        with patch("builtins.input", return_value=VALID_USER["name"]):
            result = show_birthday(self.book)
        self.assertEqual(result, "")

    def test_show_birthday_invalid(self):
        """Test that error is returned when birthday lookup fails."""
        result = show_birthday(
            [ADDITIONAL_DATA["unknown_name"]],
            self.book
        )
        self.assertIn("Error:", result)

    def test_add_address_valid(self):
        """Test that a valid address is added to a contact."""
        with patch(
                "builtins.input",
                side_effect=[VALID_USER["name"], VALID_USER["address"]]
        ):
            result = add_address(self.book)
        self.assertIn("Address added", result)

    def test_add_address_invalid(self):
        """Test that error is returned when adding address fails."""
        result = add_address(
            [ADDITIONAL_DATA["unknown_name"], "Street"],
            self.book
        )
        self.assertIn("Error:", result)

    def test_add_email_valid(self):
        """Test that a valid email address is added to a contact."""
        with patch(
                "builtins.input",
                side_effect=[VALID_USER["name"], VALID_USER["email"]]
        ):
            result = add_email(self.book)
        self.assertEqual(result, "Email added.")

    def test_add_email_invalid_format(self):
        """Test that adding an email with invalid format returns error."""
        result = add_email(
            [VALID_USER["name"],
             INVALID_USER["email"]],
            self.book
        )
        self.assertIn("Error:", result)

    def test_add_email_invalid_name(self):
        """Test that adding an email to unknown contact returns error."""
        result = add_email(
            [ADDITIONAL_DATA["unknown_name"],
             "email@mail.com"],
            self.book
        )
        self.assertIn("Error:", result)

    def test_is_valid_email_true(self):
        """Test that a valid email returns True."""
        self.assertTrue(is_valid_email(VALID_USER["email"]))

    def test_is_valid_email_false(self):
        """Test that an invalid email returns False."""
        self.assertFalse(is_valid_email(INVALID_USER["email"]))

    def test_birthdays_none(self):
        """Test that no birthdays message is returned when list is empty."""
        with patch("builtins.input", return_value="7"):
            result = birthdays(self.book)
        self.assertEqual(result, "No upcoming birthdays in 7 days")

    # def test_parse_input_valid(self):
    #     result = parse_input(
    #         f"add {ADDITIONAL_DATA['new_name']} {VALID_USER['phone']}"
    #     )
    #     self.assertEqual(
    #         result,
    #         ("add", ADDITIONAL_DATA["new_name"], VALID_USER["phone"])
    #     )
    #
    # def test_parse_input_invalid(self):
    #     result = parse_input("")
    #     self.assertIn("Error:", result)


if __name__ == '__main__':
    unittest.main()
