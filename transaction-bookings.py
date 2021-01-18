import sys
import psycopg2
from psycopg2 import pool
import threading
import random
import string
import textwrap

# global variables
successful_transactions = 0
unsuccessful_transactions = 0
ticket_updated = 0
ticket_flights_updated = 0
flights_updated = 0
bookings_updated = 0


def db_connect():
    with open('password.txt') as f:
        lines = [line.rstrip() for line in f]
    username = lines[0]
    pg_password = lines[1]
    try:
        conn_pool = psycopg2.pool.ThreadedConnectionPool(1, nthread, database=username,
                                                         user=username, password=pg_password)
        return conn_pool
    except psycopg2.OperationalError:
        print("Error connecting to database!")
        raise


def open_file(text_in):
    sql = open("transaction-bookings.sql", mode='w+')
    lines = list()
    try:
        file = open(text_in, mode='r')
        lines = [line.replace('\n', '').replace('\r', '') for line in file]
        file.close()
        return lines[1:], sql
    except FileNotFoundError:
        print("ERROR: File " + text_in + " not found!")
        raise


def get_random_alphanumeric_string(length):
    letters_and_digits = string.ascii_uppercase + string.digits
    result_str = ''.join((random.choice(letters_and_digits) for i in range(length)))
    return result_str


def execute(cursor, command):
    global sql
    cursor.execute(command)
    sql.write(textwrap.dedent(command) + "\n\n")


def check_valid(cursor, flight_id):
    execute(cursor, f"""\
            SELECT
                CASE WHEN
                    seats_available<=0 THEN FALSE
                ELSE TRUE
                END
            FROM flights WHERE flight_id={flight_id};
            """)
    result = cursor.fetchone()
    if result is None:
        return None
    elif result[0] is True:
        return True
    else:
        return False


def make_reservation(data):
    global conn_pool
    global transaction
    global successful_transactions
    global unsuccessful_transactions
    global bookings_updated
    global flights_updated
    global ticket_updated
    global ticket_flights_updated

    thread_conn = conn_pool.getconn()
    cursor = thread_conn.cursor()
    try:
        for entry in data:
            passenger_id = entry.split(',')[0]
            flight_id = entry.split(',')[1]
            book_ref = get_random_alphanumeric_string(6) # generate book_ref
            ticket_no = get_random_alphanumeric_string(13) # generate ticket_no
            # check if passenger_id or flight_id is valid
            while True:
                try:
                    proceed = False
                    cost = "0.00"
                    execute(cursor, "SET SCHEMA 'airline';")
                    if transaction == 'y':
                        execute(cursor, "BEGIN TRANSACTION ISOLATION LEVEL SERIALIZABLE;")
                    available = check_valid(cursor, flight_id)
                    if available is None or passenger_id.lower() == "null" or passenger_id == '':
                        execute(cursor, "ROLLBACK;")
                        break
                    # check if flight have available seat
                    if available:
                        proceed = True
                        cost = "200.00"
                    # update book_ref in bookings
                    execute(cursor, f"""\
                            INSERT INTO bookings VALUES (
                                '{book_ref}',
                                CURRENT_TIMESTAMP,
                                {cost});
                            """)
                    # proceed to update flights, ticket, ticket_flights
                    if proceed:
                        execute(cursor, f"""\
                                UPDATE flights
                                    SET seats_available=seats_available-1,
                                        seats_booked=seats_booked+1
                                WHERE flight_id = {flight_id};
        
                                INSERT INTO ticket VALUES (
                                    '{ticket_no}',
                                    '{book_ref}',
                                    '{passenger_id}',
                                    ' ',
                                    NULL,
                                    NULL);
        
                                INSERT INTO ticket_flights VALUES (
                                    '{ticket_no}',
                                    '{flight_id}',
                                    'Economy',
                                    {cost});
        
                                COMMIT;
                                """)
                        bookings_updated += 1
                        flights_updated += 1
                        ticket_updated += 1
                        ticket_flights_updated += 1
                        successful_transactions += 1
                        break
                    # flight full, still update bookings table but count as unsuccessful transaction
                    execute(cursor, "COMMIT;")
                    bookings_updated += 1
                    unsuccessful_transactions += 1
                    break
                # serialization failure, rollback and retry
                except (psycopg2.errors.SerializationFailure,
                        psycopg2.errors.UniqueViolation,
                        psycopg2.errors.ForeignKeyViolation):
                    execute(cursor, "ROLLBACK;")
        conn_pool.putconn(thread_conn)
    except (psycopg2.pool.PoolError, psycopg2.InterfaceError, psycopg2.OperationalError):
        pass


def run_threads():
    # Partition reservations between threads and start each one
    threads = []
    for tid in range(0, nthread):
        thread_trans = []
        for i in range(tid, len(lines), nthread):
            thread_trans.append(lines[i])
        thread = threading.Thread(target=make_reservation, args=(thread_trans,))
        threads.append(thread)
        thread.start()
    # Wait for all threads to finish
    for thread in threads:
        thread.join()

    
# arguments[0] : input=<file_name.txt>
# arguments[1] : transaction=[y|n]
# arguments[2] : threads=<int>
arguments = sys.argv[1].split(';')
text_in = arguments[0].split('=')[1]
transaction = arguments[1].split('=')[1]
nthread = int(arguments[2].split('=')[1])

conn_pool = db_connect()
lines, sql = open_file(text_in)

try: 
    run_threads()
except KeyboardInterrupt:
    print("-KeyboardInterrupt, proceed to result...")

print("Successful Transactions:", successful_transactions)
print("Unsuccessful Transactions:", unsuccessful_transactions)
print("# of records update for table bookings:", bookings_updated)
print("# of records update for table ticket:", ticket_updated)
print("# of records update for table ticket_flights:", ticket_flights_updated)
print("# of records update for table flights:", flights_updated)
conn_pool.closeall()
sql.close()
