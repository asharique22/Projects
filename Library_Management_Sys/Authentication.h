#pragma once
#include <iostream>
#include <fstream>
#include <sstream>
#include <map>
#include <string>
#include "SHA256.h"
using namespace std;

class Authentication {
    map<string, pair<string, string>> credentials;

public:
    void addCredentials(const string &user_id, const string &password, const string &name, const string &role) {
        string hashedPassword = SHA256::hash(password);
        credentials[user_id] = {hashedPassword, role};
        saveCredentials();
    }

    void loadCredentials() {
        ifstream file("credentials.csv");
        if (!file.is_open()) {
            cerr << "Error: credentials.csv not found. Creating a new one.\n";
            return;
        }

        string line, id, passwordHash, role;
        while (getline(file, line)) {
            stringstream ss(line);
            getline(ss, id, ',');
            getline(ss, passwordHash, ',');
            getline(ss, role, ',');
            credentials[id] = {passwordHash, role};
        }
        file.close();
    }

    void saveCredentials() {
        ofstream file("credentials.csv");
        if (!file.is_open()) {
            cerr << "Error: Cannot save credentials.\n";
            return;
        }

        for (const auto &entry : credentials) {
            file << entry.first << "," << entry.second.first << "," << entry.second.second << "\n";
        }
        file.close();
    }

    bool authenticate(const string &user_id, const string &password) {
        auto it = credentials.find(user_id);
        if (it != credentials.end()) {
            return it->second.first == SHA256::hash(password);
        }
        return false;
    }

    string getUserRole(const string &user_id) {
        return credentials.count(user_id) ? credentials[user_id].second : "";
    }

    void changePassword(const string &user_id) {
        if (credentials.find(user_id) == credentials.end()) {
            cout << "User not found!\n";
            return;
        }

        string oldPassword, newPassword;
        cout << "Enter old password: ";
        cin >> oldPassword;

        if (credentials[user_id].first != SHA256::hash(oldPassword)) {
            cout << "Incorrect password!\n";
            return;
        }

        cout << "Enter new password: ";
        cin >> newPassword;

        credentials[user_id].first = SHA256::hash(newPassword);
        saveCredentials();
        cout << "Password changed successfully!\n";
    }
};
