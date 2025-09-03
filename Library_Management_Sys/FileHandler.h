#pragma once
#include <iostream>
#include <fstream>
#include <sstream>
#include <vector>
#include <string>
#include <algorithm>
#include <cmath>
#include <chrono>
#include "Book.h"
#include "User.h"
using namespace std;
using namespace chrono;

class File_Handler {
public:
    // Save borrowed books
    void saveBorrowedBooksToFile(const vector<pair<Book *, system_clock::time_point>> &borrowed_books, User *user) {
        vector<string> existingEntries;
        ifstream infile("borrowed_books.csv");

        if (infile.is_open()) {
            string line;
            while (getline(infile, line)) {
                existingEntries.push_back(line);
            }
            infile.close();
        }

        ofstream file("borrowed_books.csv", ios::trunc);
        if (!file.is_open()) {
            cerr << "Error opening borrowed_books.csv file!" << endl;
            return;
        }

        if (existingEntries.empty() || existingEntries[0] != "UserID,BookTitle,ISBN,BorrowedTime") {
            file << "UserID,BookTitle,ISBN,BorrowedTime\n";
        } else {
            for (const string &entry : existingEntries) file << entry << "\n";
        }

        for (const auto &entry : borrowed_books) {
            string userId = user->getId();
            string bookTitle = entry.first->getTitle();
            string bookISBN = entry.first->getISBN();
            string borrowedTime = to_string(duration_cast<seconds>(entry.second.time_since_epoch()).count());

            string newEntry = userId + "," + bookTitle + ",\"" + bookISBN + "\"," + borrowedTime;

            if (find(existingEntries.begin(), existingEntries.end(), newEntry) == existingEntries.end()) {
                file << newEntry << "\n";
            }
        }
        file.close();
    }

    // Load borrowed books
    void loadBorrowedBooksFromFile(const vector<Book *> &allBooks, User *user,
                                   vector<pair<Book *, system_clock::time_point>> &borrowed_books) {
        ifstream file("borrowed_books.csv");
        if (!file.is_open()) {
            cerr << "Warning: Borrowed books file not found. Starting fresh.\n";
            return;
        }

        string line, userId, title, isbn, borrowedTime;
        getline(file, line);

        while (getline(file, line)) {
            stringstream ss(line);
            getline(ss, userId, ',');
            getline(ss, title, ',');
            getline(ss, isbn, ',');
            getline(ss, borrowedTime, ',');

            if (!isbn.empty() && isbn.front() == '"' && isbn.back() == '"') {
                isbn = isbn.substr(1, isbn.size() - 2);
            }

            if (user && userId == user->getId()) {
                for (Book *book : allBooks) {
                    if (book->getISBN() == isbn) {
                        book->setStatus("Borrowed");
                        borrowed_books.push_back(make_pair(book, system_clock::from_time_t(stol(borrowedTime))));
                        break;
                    }
                }
            }
        }
        file.close();
    }

    // Save books
    void saveBooks(const vector<Book *> &books, const string &filename = "books.csv") {
        ofstream file(filename);
        if (!file.is_open()) throw runtime_error("Unable to open books file for writing");

        file << "Title,Author,Publisher,Year,ISBN,Status\n";
        for (const auto &book : books) {
            file << book->getTitle() << ","
                 << book->getAuthor() << ","
                 << book->getPublisher() << ","
                 << book->getYear() << ","
                 << book->getISBN() << ","
                 << book->getStatus() << "\n";
        }
        file.close();
    }

    // Load books
    vector<Book *> loadBooks(const string &filename = "books.csv") {
        vector<Book *> books;
        ifstream file(filename);
        if (!file.is_open()) {
            cerr << "Error: Books file '" << filename << "' not found. Aborting program!" << endl;
            exit(EXIT_FAILURE);
        }

        string line, title, author, publisher, isbn, status;
        int year;
        getline(file, line);

        while (getline(file, line)) {
            stringstream ss(line);
            getline(ss, title, ',');
            getline(ss, author, ',');
            getline(ss, publisher, ',');
            ss >> year;
            ss.ignore();
            getline(ss, isbn, ',');
            getline(ss, status);

            isbn.erase(remove_if(isbn.begin(), isbn.end(), ::isspace), isbn.end());

            try {
                double val = stod(isbn);
                if (floor(val) == val) {
                    isbn = to_string((long long)val);
                }
            } catch (...) {}

            Book *book = new Book(title, author, publisher, year, isbn);
            book->setStatus(status);
            books.push_back(book);
        }
        file.close();
        return books;
    }

    // Save users
    void saveUsers(const vector<User *> &users, const string &filename = "users.csv") {
        ofstream file(filename);
        if (!file.is_open()) throw runtime_error("Unable to open users file for writing");

        file << "Name,ID,Role\n";
        for (const auto &user : users) {
            file << user->getName() << ","
                 << user->getId() << ","
                 << user->getRole() << "\n";
        }
        file.close();
    }

    // Load users
    vector<User *> loadUsers(const string &filename = "users.csv") {
        vector<User *> users;
        ifstream file(filename);
        if (!file.is_open()) {
            cerr << "Error: Users file '" << filename << "' not found. Aborting program!" << endl;
            exit(EXIT_FAILURE);
        }

        string line, name, id, role;
        getline(file, line);

        while (getline(file, line)) {
            stringstream ss(line);
            getline(ss, name, ',');
            getline(ss, id, ',');
            getline(ss, role, ',');

            User *user = nullptr;
            if (role == "Student") user = new Student(id, name);
            else if (role == "Faculty") user = new Faculty(id, name);
            else if (role == "Librarian") user = new Librarian(id, name);

            if (user) users.push_back(user);
        }
        file.close();
        return users;
    }
};
