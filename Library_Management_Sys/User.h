#pragma once
#include <string>
using namespace std;

class User {
protected:
    string id, name, role;
public:
    User(string userId, string userName) : id(userId), name(userName) {}
    virtual ~User() {}

    virtual int getMaxBooks() const = 0;
    virtual int getBorrowingPeriod() const = 0;
    virtual bool canManageSystem() const = 0;
    virtual double getFineRate() const = 0;

    string getName() const { return name; }
    string getId() const { return id; }
    string getRole() const { return role; }
};

class Student : public User {
public:
    Student(string id, string name) : User(id, name) { role = "Student"; }
    int getMaxBooks() const override { return 3; }
    int getBorrowingPeriod() const override { return 15; }
    bool canManageSystem() const override { return false; }
    double getFineRate() const override { return 10.0; }
};

class Faculty : public User {
public:
    Faculty(string id, string name) : User(id, name) { role = "Faculty"; }
    int getMaxBooks() const override { return 5; }
    int getBorrowingPeriod() const override { return 30; }
    bool canManageSystem() const override { return false; }
    double getFineRate() const override { return 0.0; }
};

class Librarian : public User {
public:
    Librarian(string id, string name) : User(id, name) { role = "Librarian"; }
    int getMaxBooks() const override { return 0; }
    int getBorrowingPeriod() const override { return 0; }
    bool canManageSystem() const override { return true; }
    double getFineRate() const override { return 0.0; }
};
