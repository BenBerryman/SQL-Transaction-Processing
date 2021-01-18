# SQL Transaction Processing
A simple program to demonstrate transaction processing in PostgreSQL through the lens of
ticket reservations in an airline database system.

## Getting Started

### Prerequisites
- PostgreSQL installed on your local machine
- User access on PostgreSQL with all privileges on user database
- Python interpreter installed on your local machine

### Installation

#### Set Up the Database
This program uses a database modeled around an airport and flights system. The database used for this program is
a modified, much slimmer version of the original database. To create the database:
For proper usage, the tables should be initialized in a
database titled 'airline', with the default 'public' schema. The file ***make_airline.sql*** in the repository 
will create the database used for the program.
- Open a Terminal window
- Navigate to the *Files* file
- Type:
```bash
psql
```
- Enter the password for your database user
- Type:
```postgresql
CREATE SCHEMA airline;
SET SCHEMA 'airline';
\i make_airline.sql;
```

- The user login information for the database should be stored in a plain text file titled ***password.txt*** 
and formatted like:
```
username
password
```
- The program takes an input plain text file with flight reservations, formatted like:
```
passenger_id,flight_id
<passenger_id1>,<flight_id1>
<passenger_id2>,<flight_id2>
```
and so on for as many reservations are made.

### Usage

* Example input text files are included in the repository ***(trans1.txt, trans2.txt, trans3.txt, trans4.txt, trans5.txt, trans6.txt)***.

* Once installation is complete, the program can be run using the syntax:
```bash
python transaction-bookings.py "input=Files/<txt>;transaction=[y|n];threads=<int>"
```

After running, the program will output various statistics about the run to the console.
It will also create a file *transaction-bookings.sql* with all of the SQL queries used for the run.

## Outline

- **transaction-bookings.py** : Main program. Connects to database, creates and runs threads for booking transactions,
and outputs result statistics.
- **password.txt** : Contains the username and password for the PostgreSQL user
- **make_airline.sql** : Creates the database tables.
- **transaction-bookings.sql** : Generated after every run of the program. Displays the SQL code useed in the run.

