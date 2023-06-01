CREATE TABLE Trip (
  Trip_ID INT PRIMARY KEY AUTO_INCREMENT,
  Departure_Location VARCHAR(255) NOT NULL,
  Destination_Location VARCHAR(255) NOT NULL,
  Intermediate_Stations TEXT,
  Departure_Date DATE NOT NULL,
  Departure_Time TIME NOT NULL,
  Arrival_Date DATE NOT NULL,
  Arrival_Time TIME NOT NULL
);

CREATE TABLE Account (
  Account_ID INT PRIMARY KEY AUTO_INCREMENT,
  Name VARCHAR(255) NOT NULL,
  Last_Name VARCHAR(255) NOT NULL,
  Email VARCHAR(255) UNIQUE NOT NULL,
  Phone_Number VARCHAR(20) UNIQUE NOT NULL,
  Password_Hash VARBINARY(MAX) NOT NULL
);

CREATE TABLE Reservation (
  PNR INT PRIMARY KEY AUTO_INCREMENT,
  Account_ID INT NOT NULL,
  Trip_ID INT NOT NULL,
  FOREIGN KEY (Account_ID) REFERENCES Account(Account_ID),
  FOREIGN KEY (Trip_ID) REFERENCES Trip(Trip_ID)
);

CREATE TABLE Trip_Status (
  Trip_ID INT PRIMARY KEY,
  Total_Booked_Seats INT NOT NULL,
  Total_Available_Seats INT NOT NULL,
  FOREIGN KEY (Trip_ID) REFERENCES Trip(Trip_ID)
);