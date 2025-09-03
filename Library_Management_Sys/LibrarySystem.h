#pragma once
#include <iostream>
#include "Library.h"
#include "Authentication.h"
#include "FileHandler.h"
using namespace std;

class LibrarySystem {
    Library library;
    Authentication authSystem;
    File_Handler fileHandler;
    User *currentUser = nullptr;
    Account *currentAccount = nullptr;

    void initializeLibraryData() {
        vector<Book *> loadedBooks = fileHandler.loadBooks();
        vector<User *> loadedUsers = fileHandler.loadUsers();

        for (auto book : loadedBooks) library.addBook(book);
        for (auto user : loadedUsers) library.addUser(user);

        for (auto user : library.getUsers()) {
            Account *account = library.findAccount(user);
            if (account) {
                auto &borrowedBooks = account->getBorrowedBooks();
                fileHandler.loadBorrowedBooksFromFile(library.getBooks(), user, borrowedBooks);
            }
        }
        authSystem.loadCredentials();
    }

    void saveLibraryData() {
        try {
            fileHandler.saveBooks(library.getBooks());
            fileHandler.saveUsers(library.getUsers());
            cout << "Library data saved successfully." << endl;
        } catch (exception &e) {
            cerr << "Error saving library data: " << e.what() << endl;
        }
    }

    // Menus
    void studentMenu() {
        int choice;
        while (true) {
            cout << "\n--- Student Menu ---\n"
                 << "1. View Books\n"
                 << "2. Borrow\n"
                 << "3. Return\n"
                 << "4. My Books\n"
                 << "5. Pay Fines\n"
                 << "6. Exit\n"
                 << "7. Logout\n"
                 << "8. Change Password\n"
                 << "Choice: ";
            cin >> choice; cin.ignore();

            if (choice == 1) library.displayAllBooks();
            else if (choice == 2) borrowFlow();
            else if (choice == 3) returnFlow();
            else if (choice == 4) currentAccount->displayBorrowedBooks();
            else if (choice == 5) currentAccount->payFines();
            else if (choice == 6) return;
            else if (choice == 7) { currentUser = nullptr; currentAccount = nullptr; return; }
            else if (choice == 8) authSystem.changePassword(currentUser->getId());
            else cout << "Invalid choice!\n";
        }
    }

    void facultyMenu() {
        int choice;
        while (true) {
            cout << "\n--- Faculty Menu ---\n"
                 << "1. View Books\n"
                 << "2. Borrow\n"
                 << "3. Return\n"
                 << "4. My Books\n"
                 << "5. Logout\n"
                 << "6. Change Password\n"
                 << "Choice: ";
            cin >> choice; cin.ignore();

            if (choice == 1) library.displayAllBooks();
            else if (choice == 2) borrowFlow();
            else if (choice == 3) returnFlow();
            else if (choice == 4) currentAccount->displayBorrowedBooks();
            else if (choice == 5) { currentUser = nullptr; currentAccount = nullptr; return; }
            else if (choice == 6) authSystem.changePassword(currentUser->getId());
            else cout << "Invalid choice!\n";
        }
    }

    void librarianMenu() {
        int choice;
        while (true) {
            cout << "\n--- Librarian Menu ---\n"
                 << "1. Add Book\n"
                 << "2. Remove Book\n"
                 << "3. Show Books\n"
                 << "4. Show Users\n"
                 << "5. Add User\n"
                 << "6. Logout\n"
                 << "7. Change Password\n"
                 << "Choice: ";
            cin >> choice; cin.ignore();

            if (choice == 1) addBookFlow();
            else if (choice == 2) removeBookFlow();
            else if (choice == 3) library.displayAllBooks();
            else if (choice == 4) library.displayAllUsers();
            else if (choice == 5) addUserFlow();
            else if (choice == 6) return;
            else if (choice == 7) authSystem.changePassword(currentUser->getId());
            else cout << "Invalid choice!\n";
        }
    }

    // Common helpers
    void borrowFlow() {
        string isbn;
        cout << "Enter ISBN: "; getline(cin, isbn);
        Book *book = library.findBook(isbn);
        if (book) currentAccount->borrow(book);
        else cout << "Book not found.\n";
    }

    void returnFlow() {
        string isbn;
        cout << "Enter ISBN: "; getline(cin, isbn);
        Book *book = library.findBook(isbn);
        if (book) currentAccount->returnBook(book);
        else cout << "Book not found.\n";
    }

    void addBookFlow() {
        string title, author, publisher, isbn; int year;
        cout << "Title: "; getline(cin, title);
        cout << "Author: "; getline(cin, author);
        cout << "Publisher: "; getline(cin, publisher);
        cout << "Year: "; cin >> year; cin.ignore();
        cout << "ISBN: "; getline(cin, isbn);
        library.addBook(new Book(title, author, publisher, year, isbn));
    }

    void removeBookFlow() {
        string isbn;
        cout << "ISBN to remove: "; getline(cin, isbn);
        library.removeBook(isbn);
    }

    void addUserFlow() {
        string name, id, role;
        cout << "Name: "; getline(cin, name);
        cout << "ID: "; getline(cin, id);
        cout << "Role (Student/Faculty/Librarian): "; getline(cin, role);

        User *newUser = nullptr;
        if (role == "Student") {
            newUser = new Student(id, name);
            authSystem.addCredentials(id, "pass123", name, role);
        } else if (role == "Faculty") {
            newUser = new Faculty(id, name);
            authSystem.addCredentials(id, "prof123", name, role);
        } else {
            newUser = new Librarian(id, name);
            authSystem.addCredentials(id, "lib123", name, role);
        }
        if (newUser) library.addUser(newUser);
    }

public:
    LibrarySystem() { initializeLibraryData(); }
    ~LibrarySystem() { saveLibraryData(); }

    void start() {
        int choice;
        while (true) {
            if (!currentUser) {
                cout << "\n--- Library System ---\n"
                     << "1. Login\n2. Exit\nChoice: ";
                cin >> choice; cin.ignore();
                if (choice == 1) {
                    string user_id, password;
                    cout << "User ID: "; getline(cin, user_id);
                    cout << "Password: "; getline(cin, password);
                    if (authSystem.authenticate(user_id, password)) {
                        string role = authSystem.getUserRole(user_id);
                        currentUser = library.findUser(user_id);
                        currentAccount = library.findAccount(currentUser);
                        if (role == "Student") studentMenu();
                        else if (role == "Faculty") facultyMenu();
                        else librarianMenu();
                        currentUser = nullptr; currentAccount = nullptr;
                    } else {
                        cout << "Invalid credentials!\n";
                    }
                } else if (choice == 2) {
                    cout << "Goodbye!\n"; break;
                }
            }
        }
    }
};
