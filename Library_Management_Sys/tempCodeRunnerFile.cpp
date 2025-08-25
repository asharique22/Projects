
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