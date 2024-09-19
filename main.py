import mysql.connector
import bcrypt
import maskpass
from sshtunnel import SSHTunnelForwarder, BaseSSHTunnelForwarderError
import logging
import os
import pymysql

# Define your SSH and MySQL server details
ssh_host = '192.197.151.116'
ssh_port = 22
ssh_username = 'parisaazizian'
ssh_password = 'Trent@2024'
mysql_host = '127.0.0.1'
mysql_port = 3306
mysql_user = 'parisaazizian'
mysql_password = 'Navid@1365'
mysql_db = 'parisaazizian'

# Enable logging
#logging.basicConfig(level=logging.DEBUG)

# Change to the directory where the private key is located
new_directory = "C:\\Users\\parisa\\PycharmProjects\\lab7\\pet"
os.chdir(new_directory)
print("Current Working Directory:", os.getcwd())

# Define the private key file path
private_key_filename = 'parisaazizian.private'
private_key_path = os.path.join(new_directory, private_key_filename)

# Verify the private key file exists
if not os.path.exists(private_key_path):
    print(f"Private key file not found: {private_key_path}")
    exit(1)

# Define the function to establish the SSH tunnel
tunnel = None


def create_ssh_tunnel():
    global tunnel
    if tunnel is None:
        tunnel = SSHTunnelForwarder(
            (ssh_host, ssh_port),
            ssh_username=ssh_username,
            ssh_password=ssh_password,
            ssh_pkey=private_key_path,
            remote_bind_address=(mysql_host, mysql_port)
        )

        tunnel.start()

    return tunnel


def get_db_connection():
    create_ssh_tunnel()
    connection = pymysql.connect(
        host='127.0.0.1',
        user=mysql_user,
        password=mysql_password,
        database=mysql_db,
        port=tunnel.local_bind_port
    )
    return connection


def initialize_database():
    try:
        db = get_db_connection()

        with db.cursor() as cursor:

            # Create tables
            cursor.execute("""
                    CREATE TABLE IF NOT EXISTS Users (
                        user_id INT AUTO_INCREMENT PRIMARY KEY,
                        email VARCHAR(255) UNIQUE NOT NULL,
                        hashedPassword VARCHAR(255),
                        hashSaltKey VARCHAR(255)
                    );
                """)

            cursor.execute("""
                    CREATE TABLE IF NOT EXISTS Shelters (
                        shelter_id INT AUTO_INCREMENT PRIMARY KEY,
                        location VARCHAR(255),
                        shelter_name VARCHAR(255),
                        contact_info VARCHAR(255)
                    );
                """)

            cursor.execute("""
                    CREATE TABLE IF NOT EXISTS Pets (
                        pet_id INT AUTO_INCREMENT PRIMARY KEY,
                        breed VARCHAR(100) NOT NULL,
                        image BLOB,
                        age INT NOT NULL,
                        description TEXT,
                        shelter_id INT,
                        FOREIGN KEY (shelter_id) REFERENCES Shelters(shelter_id)
                    );
                """)

            cursor.execute("""
                    CREATE TABLE IF NOT EXISTS Adoptions (
                        adoption_id INT AUTO_INCREMENT PRIMARY KEY,
                        pet_id INT,
                        user_id INT,
                        shelter_id INT,
                        application_date DATE,
                        FOREIGN KEY (pet_id) REFERENCES Pets(pet_id),
                        FOREIGN KEY (user_id) REFERENCES Users(user_id),
                        FOREIGN KEY (shelter_id) REFERENCES Shelters(shelter_id)
                    );
                """)

            # Seed default shelters and pets if not already present
            cursor.execute("SELECT COUNT(*) FROM Shelters;")
            if cursor.fetchone()[0] == 0:
                cursor.executemany("INSERT INTO Shelters (shelter_name, location, contact_info) VALUES (%s, %s, %s);", [

                    ('Happy Tails Shelter', 'New York, NY', '555-1234'),
                    ('Safe Haven Animal Rescue', 'Los Angeles, CA', '555-5678'),
                    ('Paws & Claws Sanctuary', 'Chicago, IL', '555-9101'),
                    ('Furry Friends Home', 'Houston, TX', '555-1122'),
                    ('Animal Lovers Shelter', 'Phoenix, AZ', '555-3344'),
                    ('Pet Haven Sanctuary', 'Philadelphia, PA', '555-5566'),
                    ('Compassionate Paws', 'San Antonio, TX', '555-7788'),
                    ('Forever Home Shelter', 'San Diego, CA', '555-9900'),
                    ('Hopeful Hearts Rescue', 'Dallas, TX', '555-1111'),
                    ('Loving Paws Shelter', 'San Jose, CA', '555-2222')

                ])
                db.commit()

            cursor.execute("SELECT COUNT(*) FROM Pets;")
            if cursor.fetchone()[0] == 0:
                cursor.executemany(
                    "INSERT INTO Pets (breed, age, description, image, shelter_id) VALUES (%s, %s, %s, %s, %s);", [

                        ('Labrador', 3, 'Friendly and energetic', '/images/labrador1.jpg', 2),
                        ('Beagle', 2, 'Loves to play and explore', '/images/beagle2.jpg', 3),
                        ('Bulldog', 5, 'Calm and good with kids', '/images/bulldog3.jpg', 1),
                        ('Poodle', 4, 'Intelligent and easy to train', '/images/poodle4.jpg', 4),
                        ('Dachshund', 1, 'Curious and lively', '/images/dachshund5.jpg', 8),
                        ('Boxer', 6, 'Loyal and protective', '/images/boxer6.jpg', 8),
                        ('Chihuahua', 2, 'Small and affectionate', '/images/chihuahua7.jpg', 2),
                        ('Golden Retriever', 3, 'Gentle and friendly', '/images/golden_retriever8.jpg', 1),
                        ('Shih Tzu', 4, 'Loyal and alert', '/images/shih_tzu9.jpg', 5),
                        ('German Shepherd', 3, 'Intelligent and versatile', '/images/german_shepherd10.jpg', 7)
                    ])
                db.commit()
    except mysql.connector.Error as err:
        print(f"Error: {err}")

    finally:
        cursor.close()
        db.close()


def register_user():
    db = get_db_connection()
    with db.cursor() as cursor:
        email = input("Enter your email: ")
        password = input("Enter your password: ")
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(password.encode(), salt)

        try:
            cursor.execute(
                "INSERT INTO Users (email, hashedPassword, hashSaltKey) VALUES ( %s, %s, %s)",
                (email, hashed_password, salt))
            db.commit()
            print("Registration successful!")
        except mysql.connector.Error as err:
            print(f"Error: {err}")

        finally:
            cursor.close()
            db.close()


def login_user():
    db = get_db_connection()
    with db.cursor() as cursor:

        email = input("Enter your email: ")
        password = input("Enter your password: ")

        cursor.execute("SELECT user_id, hashedPassword, hashSaltKey FROM Users WHERE email = %s", (email,))
        result = cursor.fetchone()

        if result:
            user_id, hashed_password, salt = result
            if bcrypt.checkpw(password.encode(), hashed_password.encode()):
                print("Login successful!")
                cursor.close()
                db.close()
                return user_id
            else:
                print("Invalid password.")
        else:
            print("User not found.")

        cursor.close()
        db.close()
        return None


def browse_pets():
    db = get_db_connection()
    with db.cursor() as cursor:
        cursor.execute("""
            SELECT p.pet_id, p.breed, p.description, s.shelter_name, 
                   (SELECT COUNT(*) FROM Adoptions a WHERE a.pet_id = p.pet_id) AS adopted
            FROM Pets p
            JOIN Shelters s ON p.shelter_id = s.shelter_id;
        """)

        for (pet_id, name, type_, shelter_name, adopted) in cursor:
            status = "Adopted" if adopted else "Available"
            print(f"{pet_id}: {name} ({type_}) at {shelter_name} - {status}")

        cursor.close()
        db.close()


def print_adopted_pets(user_id):
    db = get_db_connection()
    with db.cursor() as cursor:
        cursor.execute("""
            SELECT 
            p.pet_id, p.breed, p.description, s.shelter_name, a.application_date 
            FROM Adoptions a 
            JOIN Pets p ON p.pet_id = a.pet_id
            JOIN Shelters s ON a.shelter_id = s.shelter_id
            WHERE a.user_id = %s
        """, user_id)

        pets = cursor.fetchall()
        if(not pets):
            print("\nYou haven't adopted any pet yet.\n")
        else:
            print("Your current adoptions are:")
            for (pet_id, name, description, shelter_name, application_date) in pets:
                print(f"{name} (ID= {pet_id}) from  {shelter_name} at {application_date} ({description})")

            print("\n=============================================\n")
        cursor.close()
        db.close()


def adopt_pet(user_id):
    db = get_db_connection()
    with db.cursor() as cursor:
        pet_id = input("Enter the ID of the pet you want to adopt: ")

        cursor.execute("SELECT COUNT(*) FROM Adoptions WHERE pet_id = %s", (pet_id,))
        if cursor.fetchone()[0] > 0:
            print("This pet has already been adopted.")
            return

        cursor.execute("SELECT shelter_id FROM Pets WHERE pet_id = %s", (pet_id,))
        shelter_id = cursor.fetchone()[0]

        cursor.execute(
            "INSERT INTO Adoptions (pet_id, user_id, application_date, shelter_id) VALUES (%s, %s, CURDATE(), %s)",
            (pet_id, user_id, shelter_id))
        db.commit()
        print("Pet adopted successfully!")

        cursor.close()
        db.close()


def cancel_adoption(user_id):
    db = get_db_connection()
    with db.cursor() as cursor:
        pet_id = input("Enter the ID of the pet you want to adopt: ")

        cursor.execute("SELECT COUNT(*) FROM Adoptions WHERE pet_id = %s AND user_id = %s", (pet_id, user_id))
        if cursor.fetchone()[0] == 0:
            print("This pet is not adopted by you.")
            return

        cursor.execute(
            "DELETE From Adoptions WHERE pet_id = %s AND user_id = %s",
            (pet_id, user_id))
        db.commit()
        print("Pet adoption is canceled successfully!")

        cursor.close()
        db.close()


def main():
    initialize_database()

    while True:
        print("Welcome to the Pet Adoption CLI")
        print("1. Register")
        print("2. Login")
        choice = input("Choose an option: ")

        if choice == '1':
            register_user()
        elif choice == '2':
            user_id = login_user()
            if user_id:
                while True:
                    print("\nMenu:")

                    print_adopted_pets(user_id)

                    print("1. Browse Pets")
                    print("2. Adopt a Pet")
                    print("3. Cancel adoption")
                    print("4. Logout")
                    choice = input("Choose an option: ")

                    if choice == '1':
                        browse_pets()
                    elif choice == '2':
                        adopt_pet(user_id)
                    elif choice == '3':
                        cancel_adoption(user_id)
                    elif choice == '4':
                        break
                    else:
                        print("Invalid option. Please try again.")
        else:
            print("Invalid option. Please try again.")


if __name__ == "__main__":
    main()
