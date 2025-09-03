#pragma once
#include <iostream>
#include <unordered_map>
#include <vector>
#include "User.h"
#include "Book.h"
#include "Account.h"
#include "FileHandler.h"
using namespace std;

class Library {
    unordered_map<string, Book *> books;       // key = ISBN
    unordered_map<string, User *> users;       // key = UserID
    unordered_map<string, Account *> accounts; // key = UserID
    File_Handler fileHandler;

public:
    ~Library() {
        for (auto &b : books) delete b.second;
        for (auto &u : users) delete u.second;
        for (auto &a : accounts) delete a.second;
    }

    void addBook(Book *book) {
        if (books.find(book->getISBN()) != books.end()) {
            cout << "Error: A book with ISBN " << book->getISBN() << " already exists!" << endl;
            delete book;
            return;
        }

        books[book->getISBN()] = book;

        vector<Book *> bookVec;
        for (const auto &pair : books) bookVec.push_back(pair.second);
        fileHandler.saveBooks(bookVec);
        cout << "Book added successfully!" << endl;
    }

    void addUser(User *user) {
        users[user->getId()] = user;
        accounts[user->getId()] = new Account(user);

        vector<User *> userVec;
        for (const auto &pair : users) userVec.push_back(pair.second);
        fileHandler.saveUsers(userVec);
    }

    bool removeBook(const string &isbn) {
        auto it = books.find(isbn);
        if (it != books.end()) {
            if (it->second->getStatus() == "Borrowed") {
                cout << "Cannot remove book. It is currently borrowed." << endl;
                return false;
            }
            delete it->second;
            books.erase(it);

            vector<Book *> bookVec;
            for (const auto &pair : books) bookVec.push_back(pair.second);
            fileHandler.saveBooks(bookVec);

            cout << "Book removed successfully!" << endl;
            return true;
        }
        cout << "Book with ISBN " << isbn << " not found." << endl;
        return false;
    }

    Book *findBook(const string &isbn) {
        return books.count(isbn) ? books[isbn] : nullptr;
    }

    User *findUser(const string &id) {
        return users.count(id) ? users[id] : nullptr;
    }

    Account *findAccount(User *user) {
        if (!user) return nullptr;
        return accounts.count(user->getId()) ? accounts[user->getId()] : nullptr;
    }

    void displayAllBooks() {
        cout << "Library Books:\n";
        for (auto &pair : books) {
            pair.second->display();
            cout << endl;
        }
    }

    void displayAllUsers() {
        cout << "Users:\n";
        for (auto &pair : users) {
            cout << "Name: " << pair.second->getName()
                 << ", ID: " << pair.second->getId()
                 << ", Role: " << pair.second->getRole() << endl;
        }
    }

    vector<Book *> getBooks() {
        vector<Book *> bookVec;
        for (const auto &pair : books) bookVec.push_back(pair.second);
        return bookVec;
    }

    vector<User *> getUsers() {
        vector<User *> userVec;
        for (const auto &pair : users) userVec.push_back(pair.second);
        return userVec;
    }
};
