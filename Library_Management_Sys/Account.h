#pragma once
#include <iostream>
#include <vector>
#include <algorithm>
#include <chrono>
#include "User.h"
#include "Book.h"
#include "FileHandler.h"
using namespace std;
using namespace chrono;

class Account {
private:
    User *user;
    vector<pair<Book *, system_clock::time_point>> borrowed_books;
    double fine;
    File_Handler file_handler;

public:
    Account(User *u) : user(u), fine(0.0) {}

    vector<pair<Book *, system_clock::time_point>> &getBorrowedBooks() { return borrowed_books; }
    User *getUser() const { return user; }

    void restoreBorrowedBook(Book *book, system_clock::time_point borrowTime) {
        borrowed_books.push_back({book, borrowTime});
    }

    void fine_cal() {
        auto now = system_clock::now();
        fine = 0.0;

        if (user->getRole() == "Student") {
            for (auto &it : borrowed_books) {
                auto borrowTime = it.second;
                int no_days = duration_cast<chrono::duration<int, ratio<86400>>>(now - borrowTime).count();
                int limit = user->getBorrowingPeriod();
                if (no_days > limit) {
                    fine += (no_days - limit) * user->getFineRate();
                }
            }
        }
    }

    void borrow(Book *book) {
        fine_cal();

        if (borrowed_books.size() >= user->getMaxBooks()) {
            cout << "You have reached the borrowing limit!" << endl;
            return;
        }

        if (fine > 0.0) {
            cout << "Please clear your dues first! Your fine: " << fine << " rupees." << endl;
            return;
        }

        if (book->getStatus() == "Available") {
            borrowed_books.push_back({book, system_clock::now()});
            book->setStatus("Borrowed");

            file_handler.saveBorrowedBooksToFile(borrowed_books, user);

            cout << "Book borrowed successfully!" << endl;
        } else {
            cout << "Book is not available at the moment!" << endl;
        }
    }

    bool returnBook(Book *book) {
        auto it = find_if(borrowed_books.begin(), borrowed_books.end(),
                          [book](const pair<Book *, system_clock::time_point> &entry) {
                              return entry.first->getISBN() == book->getISBN();
                          });

        if (it != borrowed_books.end()) {
            cout << "Book Successfully Returned!" << endl;
            auto borrowTime = it->second;
            auto now = system_clock::now();
            int days_borrowed = duration_cast<chrono::duration<int, ratio<86400>>>(now - borrowTime).count();
            int limit = user->getBorrowingPeriod();

            if (days_borrowed > limit) {
                double additional_fine = (days_borrowed - limit) * user->getFineRate();
                fine += additional_fine;
                cout << "Fine incurred: " << additional_fine << " rupees." << endl;
            }

            borrowed_books.erase(it);
            book->setStatus("Available");

            vector<string> updatedEntries;
            ifstream infile("borrowed_books.csv");
            string line;
            while (getline(infile, line)) {
                stringstream ss(line);
                string fileUserId, fileTitle, fileISBN, fileTime;

                getline(ss, fileUserId, ',');
                getline(ss, fileTitle, ',');
                getline(ss, fileISBN, ',');
                getline(ss, fileTime, ',');

                if (!fileISBN.empty() && fileISBN.front() == '"' && fileISBN.back() == '"')
                    fileISBN = fileISBN.substr(1, fileISBN.size() - 2);

                if (fileUserId == user->getId() && fileISBN == book->getISBN())
                    continue;

                updatedEntries.push_back(line);
            }
            infile.close();

            ofstream outfile("borrowed_books.csv", ios::trunc);
            for (const string &entry : updatedEntries) outfile << entry << "\n";
            outfile.close();

            return true;
        } else {
            cout << "ERROR: This book was not borrowed by this user." << endl;
        }
        return false;
    }

    void displayBorrowedBooks() {
        cout << "Borrowed Books for " << user->getName() << ":\n";
        fine_cal();
        for (const auto &pair : borrowed_books) {
            pair.first->display();
            cout << endl;
        }
    }

    double getFines() {
        fine_cal();
        return fine;
    }

    void payFines() {
        fine_cal();
        cout << "Fines to be paid: " << fine << " rupees" << endl;
        fine = 0;
    }
};
