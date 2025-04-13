
# Address Book Assistant

A command-line address book application for managing contacts with phone numbers, emails, birthdays, and addresses.

## Features

- **Contact Management**:
  - Add, edit, and delete contacts
  - Store multiple phone numbers per contact
  - Add email addresses with validation
  - Store birthdays and get upcoming birthday reminders
  - Save physical addresses

- **User Interface**:
  - Colorful console output
  - Tabular data display
  - Input validation with helpful error messages

- **Data Persistence**:
  - Automatic saving/loading of contacts
  - Data stored in pickle format

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/rubannn/goit-pycore-final.git
2. Navigate to the project directory:
   ```bash
   cd goit-pycore-final
3. Install required dependencies:
   ```bash
   pip install -r requirements.txt
## Usage
Run the application:

	python main.py


## Available Commands

### 📇 Contact Management
| Command         | Description                         |
| --------------- | ----------------------------------- |
| `add`           | Add a new contact                   |
| `change`        | Modify an existing contact          |
| `delete`        | Remove a contact                    |
| `phone`         | Show contact's phone numbers        |
| `add-phone`     | Add phone number to contact         |
| `add-email`     | Add email to contact                |
| `add-birthday`  | Add birthday to contact             |
| `add-address`   | Add address to contact              |
| `show-birthday` | Show contact's birthday             |
| `birthdays`     | Show upcoming birthdays             |
| `all`           | Display all contacts                |
| `find`          | Search contacts by name/phone/email |

### 📝 Notes Management
| Command        | Description             |
| -------------- | ----------------------- |
| `add-note`     | Add new note            |
| `edit-note`    | Edit an existing note   |
| `delete-note`  | Delete specific note    |
| `show-notes`   | Show all existing notes |
| `search-notes` | Search notes by keyword |
| `search-tags`  | Find notes by tag       |
| `sort-tags`    | Sort notes by tag       |

### ⚙️ Utility Commands
| Command         | Description                    |
| --------------- | ------------------------------ |
| `generate-data` | Generate fake data for testing |
| `help`          | Show full list of commands     |
| `hello`         | Show greeting message          |
| `exit`/`close`  | Exit the application           |

## Data Storage

Contacts are automatically saved to **data/addressbook.pkl** when you exit the application.

## Requirements
- Python 3.8+
- Required packages:
  - colorama
  - rich
  - pickle


## Examples
1. Adding a new contact:
    ```bash
    Enter a command: add
    Please type a name: John Doe
    Input phones: 1234567890
    Add email: john@example.com
    Add birthday: 15.05.1990
    Add address: 123 Main St
2. Finding upcoming birthdays:
    ```bash
    Enter a command: birthdays
    Please enter the number of days: 7
4. Viewing all contacts:
    ```bash
    Enter a command: all
## Error Handling

The application provides clear error messages for:
- Invalid phone numbers (must be 10 digits)
- Invalid email formats
- Invalid date formats
- Missing contacts

## Running Unit Tests
- Ensure to follow Installation section for setup
- Execute the following command from the project directory: ```python -m unittest discover -s tests```

## License

This project is licensed under the MIT License.
