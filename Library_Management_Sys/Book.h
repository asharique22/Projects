#pragma once
#include <iostream>
#include <string>
using namespace std;

class Book {
private:
    string title;
    string author;
    string publisher;
    int year;
    string ISBN;
    string status;

public:
    Book(string tit, string auth, string publis, int y, string isbn)
        : title(tit), author(auth), publisher(publis), year(y), ISBN(isbn), status("Available") {}

    void display() const {
        cout << "Title : " << title << endl
             << "Author: " << author << endl
             << "Publisher : " << publisher << endl
             << "Published Year : " << year << endl
             << "ISBN : " << ISBN << endl
             << "Status : " << status << endl;
    }

    void setStatus(const string &newSt) { status = newSt; }
    string getStatus() const { return status; }
    string getTitle() const { return title; }
    string getAuthor() const { return author; }
    string getPublisher() const { return publisher; }
    int getYear() const { return year; }
    string getISBN() const { return ISBN; }
};
