//Just learning Github...
//What are u doing bro..

#include <iostream>
#include <vector>
#include <string>
#include <chrono>
#include <algorithm>
#include <map>
#include <fstream>
#include <sstream>

using namespace std;
using namespace chrono;

class User
{
protected:
    string id;
    string name;
    string role;

public:
    User(string userId, string userName) : id(userId), name(userName) {}

    virtual int getMaxBooks() const = 0;
    virtual int getBorrowingPeriod() const = 0;
    virtual bool canManageSystem() const = 0;
    virtual double getFineRate() const = 0;

    string getName() const { return name; }
    string getId() const { return id; }
    string getRole() const { return role; }

    virtual ~User() {}
};

class Student : public User
{
public:
    Student(string id, string name) : User(id, name) { role = "Student"; }

    int getMaxBooks() const override { return 3; }
    int getBorrowingPeriod() const override { return 15; }
    bool canManageSystem() const override { return false; }
    double getFineRate() const override { return 10.0; }
};

class Faculty : public User
{
public:
    Faculty(string id, string name) : User(id, name) { role = "Faculty"; }
    int getMaxBooks() const override { return 5; }
    int getBorrowingPeriod() const override { return 30; }
    bool canManageSystem() const override { return false; }
    double getFineRate() const override { return 0.0; }
};

class Librarian : public User
{
public:
    Librarian(string id, string name) : User(id, name) { role = "Librarian"; }

    int getMaxBooks() const override { return 0; }
    int getBorrowingPeriod() const override { return 0; }
    bool canManageSystem() const override { return true; }
    double getFineRate() const override { return 0.0; }
};

class Book
{
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

    void display() const
    {
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

class File_Handler
{
public:
    void saveBorrowedBooksToFile(const vector<pair<Book *, system_clock::time_point>> &borrowed_books, User *user)
    {
        vector<string> existingEntries;
        ifstream infile("borrowed_books.csv");

        // Read existing entries and store them
        if (infile.is_open())
        {
            string line;
            while (getline(infile, line))
            {
                existingEntries.push_back(line);
            }
            infile.close();
        }

        ofstream file("borrowed_books.csv", ios::trunc); // Rewrite file with existing + new data
        if (!file.is_open())
        {
            cerr << "Error opening borrowed_books.csv file!" << endl;
            return;
        }

        // Rewrite header if file was empty
        if (existingEntries.empty() || existingEntries[0] != "UserID,BookTitle,ISBN,BorrowedTime")
        {
            file << "UserID,BookTitle,ISBN,BorrowedTime\n";
        }
        else
        {
            for (const string &entry : existingEntries)
            {
                file << entry << "\n";
            }
        }

        // Append new borrowed book entries only if they don't already exist
        for (const auto &entry : borrowed_books)
        {
            string userId = user->getId();
            string bookTitle = entry.first->getTitle();
            string bookISBN = entry.first->getISBN();
            string borrowedTime = to_string(duration_cast<seconds>(entry.second.time_since_epoch()).count());

            string newEntry = userId + "," + bookTitle + ",\"" + bookISBN + "\"," + borrowedTime;

            // Check for duplicates before writing
            if (find(existingEntries.begin(), existingEntries.end(), newEntry) == existingEntries.end())
            {
                file << newEntry << "\n";
            }
        }

        file.close();
    }

    void loadBorrowedBooksFromFile(vector<Book *> &allBooks, User *user, vector<pair<Book *, system_clock::time_point>> &borrowed_books)
    {
        ifstream file("borrowed_books.csv");
        if (!file.is_open())
        {
            cerr << "Warning: Borrowed books file not found. Starting fresh.\n";
            return;
        }

        string line, userId, title, isbn, borrowedTime;
        getline(file, line);

        while (getline(file, line))
        {
            stringstream ss(line);
            getline(ss, userId, ',');
            getline(ss, title, ',');
            getline(ss, isbn, ',');
            getline(ss, borrowedTime, ',');

            if (!isbn.empty() && isbn.front() == '"' && isbn.back() == '"')
            {
                isbn = isbn.substr(1, isbn.size() - 2);
            }

            if (user && userId == user->getId())
            {
                for (Book *book : allBooks)
                {
                    if (book->getISBN() == isbn)
                    {
                        book->setStatus("Borrowed");
                        borrowed_books.push_back(make_pair(book, system_clock::from_time_t(stol(borrowedTime))));
                        break;
                    }
                }
            }
        }

        file.close();
    }

    void saveBooks(const vector<Book *> &books, const string &filename = "books.csv")
    {
        ofstream file(filename);
        if (!file.is_open())
        {
            throw runtime_error("Unable to open books file for writing");
        }

        file << "Title,Author,Publisher,Year,ISBN,Status\n";

        for (const auto &book : books)
        {
            file << book->getTitle() << ","
                 << book->getAuthor() << ","
                 << book->getPublisher() << ","
                 << book->getYear() << ","
                 << book->getISBN() << ","
                 << book->getStatus() << "\n";
        }
        file.close();
    }

    vector<Book *> loadBooks(const string &filename = "books.csv")
    {
        vector<Book *> books;
        ifstream file(filename);
        if (!file.is_open())
        {
            cerr << "Error: Books file '" << filename << "' not found. Aborting program!" << endl;
            exit(EXIT_FAILURE);
        }

        string line, title, author, publisher, isbn, status;
        int year;

        getline(file, line);

        while (getline(file, line))
        {
            stringstream ss(line);
            getline(ss, title, ',');
            getline(ss, author, ',');
            getline(ss, publisher, ',');
            ss >> year;
            ss.ignore();
            getline(ss, isbn, ',');
            getline(ss, status);

            Book *book = new Book(title, author, publisher, year, isbn);
            book->setStatus(status);
            books.push_back(book);
        }

        file.close();
        return books;
    }

    void saveUsers(const vector<User *> &users, const string &filename = "users.csv")
    {
        ofstream file(filename);
        if (!file.is_open())
        {
            throw runtime_error("Unable to open users file for writing");
        }

        file << "Name,ID,Role\n";

        for (const auto &user : users)
        {
            file << user->getName() << ","
                 << user->getId() << ","
                 << user->getRole() << "\n";
        }
        file.close();
    }

    vector<User *> loadUsers(const string &filename = "users.csv")
    {
        vector<User *> users;
        ifstream file(filename);
        if (!file.is_open())
        {
            cerr << "Error: Users file '" << filename << "' not found. Aborting program!" << endl;
            exit(EXIT_FAILURE);
        }

        string line, name, id, role;
        getline(file, line);

        while (getline(file, line))
        {
            stringstream ss(line);
            getline(ss, name, ',');
            getline(ss, id, ',');
            getline(ss, role, ',');

            User *user = nullptr;
            if (role == "Student")
            {
                user = new Student(id, name);
            }
            else if (role == "Faculty")
            {
                user = new Faculty(id, name);
            }
            else if (role == "Librarian")
            {
                user = new Librarian(id, name);
            }

            if (user)
            {
                users.push_back(user);
            }
        }

        file.close();
        return users;
    }
};

class Account
{
private:
    User *user;
    vector<pair<Book *, system_clock::time_point>> borrowed_books;
    double fine;
    File_Handler file_handler;

public:
    vector<pair<Book *, system_clock::time_point>> &getBorrowedBooks() { return borrowed_books; }
    Account(User *u) : user(u), fine(0.0) {}

    void restoreBorrowedBook(Book *book, system_clock::time_point borrowTime)
    {
        borrowed_books.push_back({book, borrowTime});
    }

    User *getUser() const { return user; }

    void fine_cal()
    {
        auto now = system_clock::now();
        fine = 0.0;

        if (user->getRole() == "Student")
        {
            for (auto &it : borrowed_books)
            {
                auto borrowTime = it.second;
                int no_days = duration_cast<chrono::duration<int, ratio<86400>>>(now - borrowTime).count();
                int limit = user->getBorrowingPeriod();
                if (no_days > limit)
                {
                    fine += (no_days - limit) * user->getFineRate();
                }
            }
        }
    }

    void borrow(Book *book)
    {
        fine_cal();

        if (borrowed_books.size() >= user->getMaxBooks())
        {
            cout << "You have reached the borrowing limit!" << endl;
            return;
        }

        if (fine > 0.0)
        {
            cout << "Please clear your dues first! Your fine: " << fine << " rupees." << endl;
            return;
        }

        if (book->getStatus() == "Available")
        {
            borrowed_books.push_back({book, system_clock::now()});
            book->setStatus("Borrowed");

            // Save borrowed books
            file_handler.saveBorrowedBooksToFile(borrowed_books, user);

            cout << "Book borrowed successfully!" << endl;
        }
        else
        {
            cout << "Book is not available at the moment!" << endl;
        }
    }

    // Function to save borrowed books to file
    void saveBorrowedBooksToFile()
    {
        ofstream file("borrowed_books.csv");

        if (!file.is_open())
        {
            cerr << "Error opening borrowed_books.csv file!" << endl;
            return;
        }

        file << "UserID,BookTitle,ISBN,BorrowedTime\n";
        for (const auto &entry : borrowed_books)
        {
            string userId = user->getId();
            string bookTitle = entry.first->getTitle();
            string bookISBN = entry.first->getISBN();
            string borrowedTime = to_string(duration_cast<seconds>(entry.second.time_since_epoch()).count());

            file << userId << "," << bookTitle << ",\"" << bookISBN << "\"," << borrowedTime << "\n"; // Ensure ISBN stays as a string
        }
        file.close();
    }

    bool returnBook(Book *book)
    {
        auto it = find_if(borrowed_books.begin(), borrowed_books.end(),
                          [book](const pair<Book *, system_clock::time_point> &entry)
                          {
                              return entry.first->getISBN() == book->getISBN(); // Compare ISBN
                          });

        if (it != borrowed_books.end())
        {
            cout << "Book Successfully Returned!" << endl;
            auto borrowTime = it->second;
            auto now = system_clock::now();
            int days_borrowed = duration_cast<chrono::duration<int, ratio<86400>>>(now - borrowTime).count();
            int limit = user->getBorrowingPeriod();

            if (days_borrowed > limit)
            {
                double additional_fine = (days_borrowed - limit) * user->getFineRate();
                fine += additional_fine;
                cout << "Fine incurred: " << additional_fine << " rupees." << endl;
            }

            borrowed_books.erase(it);
            book->setStatus("Available");

            // Reload file and remove the returned book's entry
            vector<string> updatedEntries;
            ifstream infile("borrowed_books.csv");

            string line;
            while (getline(infile, line))
            {
                stringstream ss(line);
                string fileUserId, fileTitle, fileISBN, fileTime;

                getline(ss, fileUserId, ',');
                getline(ss, fileTitle, ',');
                getline(ss, fileISBN, ',');
                getline(ss, fileTime, ',');

                if (fileISBN.front() == '"' && fileISBN.back() == '"')
                    fileISBN = fileISBN.substr(1, fileISBN.size() - 2);

                // Skip the entry matching the returned book
                if (fileUserId == user->getId() && fileISBN == book->getISBN())
                    continue;

                updatedEntries.push_back(line);
            }
            infile.close();

            // Rewrite file with updated entries
            ofstream outfile("borrowed_books.csv", ios::trunc);
            for (const string &entry : updatedEntries)
            {
                outfile << entry << "\n";
            }
            outfile.close();

            return true;
        }
        else
        {
            cout << "ERROR: This book was not borrowed by this user." << endl;
        }
        return false;
    }

    void displayBorrowedBooks()
    {
        cout << "Borrowed Books for " << user->getName() << ":\n";
        fine_cal();
        for (const auto &pair : borrowed_books)
        {
            pair.first->display();
            cout << endl;
        }
    }

    double getFines()
    {
        fine_cal();
        return fine;
    }

    void payFines()
    {
        fine_cal();
        cout << "Fines to be paid: " << fine << " rupees" << endl;
        fine = 0;
    }
};

class Authentication
{
    map<string, pair<string, string>> credentials;

public:
    void addCredentials(const string &user_id, const string &password, const string &name, const string &role)
    {
        credentials[user_id] = {password, role};
        saveCredentials();
    }

public:
    void loadCredentials()
    {
        ifstream file("credentials.csv");
        if (!file.is_open())
        {
            cerr << "Error: credentials.csv not found. Creating a new one.\n";
            return;
        }

        string line, id, password, role;
        while (getline(file, line))
        {
            stringstream ss(line);
            getline(ss, id, ',');
            getline(ss, password, ',');
            getline(ss, role, ',');

            credentials[id] = {password, role};
        }
        file.close();
    }

    void saveCredentials()
    {
        ofstream file("credentials.csv");
        if (!file.is_open())
        {
            cerr << "Error: Cannot save credentials.\n";
            return;
        }

        for (const auto &entry : credentials)
        {
            file << entry.first << "," << entry.second.first << "," << entry.second.second << "\n";
        }
        file.close();
    }

    bool authenticate(string user_id, string password)
    {
        auto it = credentials.find(user_id);
        if (it != credentials.end())
        {
            return it->second.first == password;
        }
        return false;
    }

    string getUserRole(string user_id)
    {
        return credentials.count(user_id) ? credentials[user_id].second : "";
    }

    void changePassword(string user_id)
    {
        if (credentials.find(user_id) == credentials.end())
        {
            cout << "User not found!\n";
            return;
        }

        string oldPassword, newPassword;
        cout << "Enter old password: ";
        cin >> oldPassword;

        if (credentials[user_id].first != oldPassword)
        {
            cout << "Incorrect password!\n";
            return;
        }

        cout << "Enter new password: ";
        cin >> newPassword;

        credentials[user_id].first = newPassword;
        saveCredentials();
        cout << "Password changed successfully!\n";
    }
};

class Library
{
    vector<Book *> books;
    vector<User *> users;
    vector<Account *> accounts;

private:
    File_Handler fileHandler;

public:
    ~Library()
    {
        for (auto book : books)
            delete book;
        for (auto user : users)
            delete user;
        for (auto account : accounts)
            delete account;
    }

    void addBook(Book *book)
    {
        books.push_back(book);
        fileHandler.saveBooks(books);
    }
    void addUser(User *user)
    {
        users.push_back(user);
        accounts.push_back(new Account(user));

        fileHandler.saveUsers(users);
    }

    bool removeBook(const string &isbn)
    {
        auto it = find_if(books.begin(), books.end(),
                          [&isbn](Book *book)
                          { return book->getISBN() == isbn; });

        if (it != books.end())
        {
            if ((*it)->getStatus() == "Borrowed")
            {
                cout << "Cannot remove book. It is currently borrowed." << endl;
                return false;
            }

            delete *it;
            books.erase(it);

            fileHandler.saveBooks(books);
            cout << "Book removed successfully!" << endl;
            return true;
        }

        cout << "Book with ISBN " << isbn << " not found." << endl;
        return false;
    }

    Book *findBook(const string &isbn)
    {
        for (auto book : books)
        {
            if (book->getISBN() == isbn)
            {
                return book;
            }
        }
        return nullptr;
    }

    User *findUser(const string &id)
    {
        for (auto user : users)
        {
            if (user->getId() == id)
            {
                return user;
            }
        }
        return nullptr;
    }

    Account *findAccount(User *user)
    {
        for (auto &account : accounts)
        {
            if (account->getFines() >= 0 && account->getUser()->getId() == user->getId())
            {
                return account;
            }
        }
        return nullptr;
    }

    void displayAllBooks()
    {
        cout << "Library Books:\n";
        for (auto book : books)
        {
            book->display();
            cout << endl;
        }
    }

    void displayAllUsers()
    {
        cout << "Users:\n";
        for (auto user : users)
        {
            cout << "Name: " << user->getName()
                 << ", ID: " << user->getId()
                 << ", Role: " << user->getRole() << endl;
        }
    }

    vector<Book *> &getBooks() { return books; }
    vector<User *> &getUsers() { return users; }
};

class LibrarySystem
{
    Library library;
    Authentication authSystem;
    File_Handler fileHandler;
    User *currentUser = nullptr;
    Account *currentAccount = nullptr;

    void initializeLibraryData()
    {
        vector<Book *> loadedBooks = fileHandler.loadBooks();
        vector<User *> loadedUsers = fileHandler.loadUsers();

        // Add books to library
        for (auto book : loadedBooks)
        {
            library.addBook(book);
        }

        // Add users and create accounts
        for (auto user : loadedUsers)
        {
            library.addUser(user);
        }

        // Load borrowed books for all users
        for (auto user : library.getUsers())
        {
            Account *account = library.findAccount(user);
            if (account)
            {
                fileHandler.loadBorrowedBooksFromFile(library.getBooks(), user, account->getBorrowedBooks());
            }
        }

        authSystem.loadCredentials();
    }

    void saveLibraryData()
    {
        try
        {
            fileHandler.saveBooks(library.getBooks());
            fileHandler.saveUsers(library.getUsers());
            cout << "Library data saved successfully." << endl;
        }
        catch (exception &e)
        {
            cerr << "Error saving library data: " << e.what() << endl;
        }
    }

    void studentMenu()
    {
        int choice;
        while (true)
        {
            cout << "\n--- Student Menu ---\n"
                 << "1. View Available Books\n"
                 << "2. Borrow a Book\n"
                 << "3. Return a Book\n"
                 << "4. Display Borrowed Books\n"
                 << "5. Pay Fines\n"
                 << "6. Exit\n"
                 << "7. Logout\n"
                 << "8. Change Password\n"
                 << "Enter your choice: ";
            cin >> choice;
            cin.ignore();

            switch (choice)
            {
            case 1:
                library.displayAllBooks();
                break;
            case 2:
            {
                string isbn;
                cout << "Enter the ISBN of the book you want to borrow: ";
                getline(cin, isbn);
                Book *book = library.findBook(isbn);
                if (book)
                {
                    currentAccount->borrow(book);
                }
                else
                {
                    cout << "Book with ISBN " << isbn << " not found." << endl;
                }
                break;
            }
            case 3:
            {
                string isbn;
                cout << "Enter the ISBN of the book you want to return: ";
                getline(cin, isbn);
                Book *book = library.findBook(isbn);
                if (book)
                {
                    currentAccount->returnBook(book);
                }
                else
                {
                    cout << "Book with ISBN " << isbn << " not found." << endl;
                }
                break;
            }
            case 4:
                currentAccount->displayBorrowedBooks();
                break;
            case 5:
                currentAccount->payFines();
                break;
            case 6:
                cout << "Exiting Student Menu." << endl;
                return;
            case 7:
                currentUser = nullptr;
                currentAccount = nullptr;
                return;
            case 8:
                authSystem.changePassword(currentUser->getId());
                break;
            default:
                cout << "Invalid choice. Please try again." << endl;
            }
        }
    }

    void librarianMenu()
    {
        int choice;
        while (true)
        {
            cout << "\n--- Librarian Menu ---\n"
                 << "1. Add a Book\n"
                 << "2. Remove a Book\n"
                 << "3. Display All Books\n"
                 << "4. Display All Users\n"
                 << "5. Display Available Users\n"
                 << "6. Add a User\n"
                 << "7. Logout\n"
                 << "8. Change Password\n"
                 << "Enter your choice: ";
            cin >> choice;
            cin.ignore();

            switch (choice)
            {
            case 1:
            {
                string title, author, publisher, isbn;
                int year;

                cout << "Enter Title: ";
                getline(cin, title);
                cout << "Enter Author: ";
                getline(cin, author);
                cout << "Enter Publisher: ";
                getline(cin, publisher);
                cout << "Enter Year: ";
                cin >> year;
                cin.ignore();
                cout << "Enter ISBN: ";
                getline(cin, isbn);

                library.addBook(new Book(title, author, publisher, year, isbn));
                cout << "Book added successfully!" << endl;
                break;
            }
            case 2:
            {
                string isbn;
                cout << "Enter the ISBN of the book you want to remove: ";
                getline(cin, isbn);
                library.removeBook(isbn);
                break;
            }
            case 3:
                library.displayAllBooks();
                break;
            case 4:
                library.displayAllUsers();
                break;
            case 5:
                library.displayAllUsers();
                break;
            case 6:
            {
                string name, id, role;
                cout << "Enter Name: ";
                getline(cin, name);
                cout << "Enter User ID: ";
                getline(cin, id);
                cout << "Enter Role (Student/Faculty/Librarian): ";
                getline(cin, role);

                User *newUser = nullptr;
                if (role == "Student")
                {
                    newUser = new Student(id, name);
                    library.addUser(newUser);
                    authSystem.addCredentials(id, "pass123", name, role);
                }
                else if (role == "Faculty")
                {
                    newUser = new Faculty(id, name);
                    library.addUser(newUser);
                    authSystem.addCredentials(id, "prof123", name, role);
                }
                else
                {
                    newUser = new Librarian(id, name);
                    library.addUser(newUser);
                    authSystem.addCredentials(id, "lib123", name, role);
                }

                if (newUser)
                {
                    cout << "User added successfully!" << endl;
                }
                break;
            }
            case 7:
                cout << "Exiting Librarian Menu." << endl;
                return;
            case 8:
                authSystem.changePassword(currentUser->getId());
                break;
            default:

                cout << "Invalid choice. Please try again." << endl;
            }
        }
    }

    void facultyMenu()
    {
        int choice;
        while (true)
        {
            cout << "\n--- Faculty Menu ---\n"
                 << "1. View Available Books\n"
                 << "2. Borrow a Book\n"
                 << "3. Return a Book\n"
                 << "4. View Borrowed Books\n"
                 << "5. Logout\n"
                 << "6. Change Password\n"
                 << "Enter your choice: ";
            cin >> choice;
            cin.ignore();

            switch (choice)
            {
            case 1:
                library.displayAllBooks();
                break;
            case 2:
            {
                string bookIsbn;
                cout << "Enter Book ISBN to borrow: ";
                getline(cin, bookIsbn);
                Book *book = library.findBook(bookIsbn);
                if (book)
                {
                    currentAccount->borrow(book);
                    book->setStatus("Borrowed");
                }
                break;
            }
            case 3:
            {
                string bookIsbn;
                cout << "Enter Book ISBN to return: ";
                getline(cin, bookIsbn);
                Book *book = library.findBook(bookIsbn);
                if (book && currentAccount->returnBook(book))
                {
                    book->setStatus("Available");
                    cout << "Book returned successfully!" << endl;
                }
                break;
            }
            case 4:
                currentAccount->displayBorrowedBooks();
                break;
            case 5:
                currentUser = nullptr;
                currentAccount = nullptr;
                return;
            case 6:
                authSystem.changePassword(currentUser->getId());
                break;
            default:
                cout << "Invalid choice. Please try again." << endl;
            }
        }
    }

public:
    LibrarySystem() : currentUser(nullptr), currentAccount(nullptr)
    {
        initializeLibraryData();
    }

    ~LibrarySystem()
    {
        saveLibraryData();
    }

    void start()
    {
        int choice;
        while (true)
        {
            if (currentUser == nullptr)
            {
                cout << "\n--- Library Management System ---\n"
                     << "1. Login\n"
                     << "2. Exit\n"
                     << "Enter your choice: ";
                cin >> choice;
                cin.ignore();

                if (choice == 1)
                {
                    string user_id, password;
                    cout << "Enter User ID: ";
                    getline(cin, user_id);
                    cout << "Enter Password: ";
                    getline(cin, password);

                    if (authSystem.authenticate(user_id, password))
                    {
                        string role = authSystem.getUserRole(user_id);
                        currentUser = library.findUser(user_id);
                        currentAccount = library.findAccount(currentUser);

                        if (role == "Student")
                        {
                            studentMenu();
                        }
                        else if (role == "Faculty")
                        {
                            facultyMenu();
                        }
                        else if (role == "Librarian")
                        {
                            librarianMenu();
                        }
                        currentUser = nullptr;
                        currentAccount = nullptr;
                    }
                    else
                    {
                        cout << "Invalid User ID or Password!" << endl;
                    }
                }
                else if (choice == 2)
                {
                    cout << "Exiting Library Management System.\n";
                    break;
                }
                else
                {
                    cout << "Invalid choice. Please try again." << endl;
                }
            }
        }
    }
};

int main()
{
    LibrarySystem librarySystem;
    librarySystem.start();
    return 0;
}
