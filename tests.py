import unittest
from unittest.mock import patch, MagicMock, call
import bcrypt
from io import StringIO

from main import (
     create_ssh_tunnel, get_db_connection, initialize_database,
     register_user, login_user, browse_pets, print_adopted_pets,
     adopt_pet, cancel_adoption
 )

ssh_host = '192.197.151.116'
ssh_port = 22
ssh_username = 'parisaazizian'
ssh_password = 'Trent@2024'
mysql_host = '127.0.0.1'
mysql_port = 3306
mysql_user = 'parisaazizian'
mysql_password = 'Navid@1365'
mysql_db = 'parisaazizian'

class TestPetAdoption(unittest.TestCase):

    @patch('main.SSHTunnelForwarder')
    def test_create_ssh_tunnel(self, MockSSHTunnelForwarder):
        # Mocking SSH tunnel creation
        mock_tunnel = MockSSHTunnelForwarder.return_value
        mock_tunnel.local_bind_port = 3306

        tunnel = create_ssh_tunnel()

        MockSSHTunnelForwarder.assert_called_once_with(
            ('192.197.151.116', 22),
            ssh_username=ssh_username,
            ssh_password=ssh_password,
            ssh_pkey='C:\\Users\\parisa\\PycharmProjects\\lab7\\pet\\parisaazizian.private',
            remote_bind_address=('127.0.0.1', 3306)
        )

        mock_tunnel.start.assert_called_once()
        self.assertEqual(tunnel, mock_tunnel)

    @patch('main.pymysql.connect')
    @patch('main.create_ssh_tunnel')
    def test_get_db_connection(self, mock_create_ssh_tunnel, mock_pymysql_connect):
        # Mock SSH tunnel and pymysql.connect
        mock_tunnel = MagicMock()
        mock_tunnel.local_bind_port = 3306
        mock_create_ssh_tunnel.return_value = mock_tunnel

        connection = get_db_connection()

        mock_pymysql_connect.assert_called_once_with(
            host='127.0.0.1',
            user=mysql_user,
            password=mysql_password,
            database=mysql_db,
            port=3306
        )
        self.assertEqual(connection, mock_pymysql_connect.return_value)

    @patch('main.get_db_connection')
    @patch('builtins.input', side_effect=['test@example.com', 'password'])
    @patch('sys.stdout', new_callable=StringIO)
    def test_register_user(self, mock_stdout, mock_input, mock_get_db_connection):
        mock_conn = MagicMock()
        mock_cursor = mock_conn.cursor.return_value.__enter__.return_value
        mock_get_db_connection.return_value = mock_conn

        register_user()

        mock_cursor.execute.assert_called_once()
        args, _ = mock_cursor.execute.call_args
        self.assertEqual(args[0], "INSERT INTO Users (email, hashedPassword, hashSaltKey) VALUES ( %s, %s, %s)")
        self.assertEqual(args[1][0], 'test@example.com')
        self.assertTrue(bcrypt.checkpw('password'.encode(), args[1][1]))
        self.assertIn('Registration successful!', mock_stdout.getvalue())

    @patch('main.get_db_connection')
    @patch('builtins.input', side_effect=['test@example.com', 'password'])
    @patch('sys.stdout', new_callable=StringIO)
    def test_login_user_success(self, mock_stdout, mock_input, mock_get_db_connection):
        mock_conn = MagicMock()
        mock_cursor = mock_conn.cursor.return_value.__enter__.return_value
        mock_get_db_connection.return_value = mock_conn

        # Mock the cursor's fetchone method
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw('password'.encode(), salt)
        mock_cursor.fetchone.return_value = (1, hashed_password.decode(), salt.decode())

        user_id = login_user()

        mock_cursor.execute.assert_called_once_with("SELECT user_id, hashedPassword, hashSaltKey FROM Users WHERE email = %s", ('test@example.com',))
        self.assertEqual(user_id, 1)
        self.assertIn('Login successful!', mock_stdout.getvalue())

    @patch('main.get_db_connection')
    @patch('builtins.input', side_effect=['test@example.com', 'wrongpassword'])
    @patch('builtins.input', side_effect=['test@example.com', 'wrongpassword'])
    @patch('sys.stdout', new_callable=StringIO)
    def test_login_user_failure(self, mock_stdout, mock_input, mock_get_db_connection):
        mock_conn = MagicMock()
        mock_cursor = mock_conn.cursor.return_value.__enter__.return_value
        mock_get_db_connection.return_value = mock_conn

        # Mock the cursor's fetchone method
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw('password'.encode(), salt)
        mock_cursor.fetchone.return_value = (1, hashed_password.decode(), salt.decode())

        user_id = login_user()

        mock_cursor.execute.assert_called_once_with(
            "SELECT user_id, hashedPassword, hashSaltKey FROM Users WHERE email = %s", ('test@example.com',))
        self.assertIsNone(user_id)
        self.assertIn('Invalid password.', mock_stdout.getvalue())

    @patch('main.get_db_connection')
    @patch('sys.stdout', new_callable=StringIO)
    def test_browse_pets(self, mock_stdout, mock_get_db_connection):
        mock_conn = MagicMock()
        mock_cursor = mock_conn.cursor.return_value.__enter__.return_value
        mock_get_db_connection.return_value = mock_conn

        # Mock the cursor's fetchall method
        mock_cursor.fetchall.return_value = [
            (1, 'Labrador', 'Friendly and energetic', 'Happy Tails Shelter', 0),
            (2, 'Beagle', 'Loves to play and explore', 'Safe Haven Animal Rescue', 1)
        ]

        browse_pets()

        expected_output = (
            "1: Labrador (Friendly and energetic) at Happy Tails Shelter - Available\n"
            "2: Beagle (Loves to play and explore) at Safe Haven Animal Rescue - Adopted\n"
        )
        self.assertIn(expected_output, mock_stdout.getvalue())

    @patch('main.get_db_connection')
    @patch('sys.stdout', new_callable=StringIO)
    def test_print_adopted_pets_no_adoptions(self, mock_stdout, mock_get_db_connection):
        mock_conn = MagicMock()
        mock_cursor = mock_conn.cursor.return_value.__enter__.return_value
        mock_get_db_connection.return_value = mock_conn

        # Mock the cursor's fetchall method
        mock_cursor.fetchall.return_value = []

        print_adopted_pets(1)

        self.assertIn("\nYou haven't adopted any pet yet.\n", mock_stdout.getvalue())

    @patch('main.get_db_connection')
    @patch('sys.stdout', new_callable=StringIO)
    def test_print_adopted_pets_with_adoptions(self, mock_stdout, mock_get_db_connection):
        mock_conn = MagicMock()
        mock_cursor = mock_conn.cursor.return_value.__enter__.return_value
        mock_get_db_connection.return_value = mock_conn

        # Mock the cursor's fetchall method
        mock_cursor.fetchall.return_value = [
            (1, 'Labrador', 'Friendly and energetic', 'Happy Tails Shelter', '2024-01-01'),
            (2, 'Beagle', 'Loves to play and explore', 'Safe Haven Animal Rescue', '2024-02-01')
        ]

        print_adopted_pets(1)

        expected_output = (
            "Your current adoptions are:\n"
            "Labrador (ID= 1) from  Happy Tails Shelter at 2024-01-01 (Friendly and energetic)\n"
            "Beagle (ID= 2) from  Safe Haven Animal Rescue at 2024-02-01 (Loves to play and explore)\n"
        )
        self.assertIn(expected_output, mock_stdout.getvalue())

    @patch('main.get_db_connection')
    @patch('builtins.input', side_effect=['1'])
    @patch('sys.stdout', new_callable=StringIO)
    def test_adopt_pet_success(self, mock_stdout, mock_input, mock_get_db_connection):
        mock_conn = MagicMock()
        mock_cursor = mock_conn.cursor.return_value.__enter__.return_value
        mock_get_db_connection.return_value = mock_conn

        # Mock the cursor's fetchone method
        mock_cursor.fetchone.side_effect = [(0,), (1,)]

        adopt_pet(1)

        expected_calls = [
            call("SELECT COUNT(*) FROM Adoptions WHERE pet_id = %s", ('1',)),
            call("SELECT shelter_id FROM Pets WHERE pet_id = %s", ('1',)),
            call("INSERT INTO Adoptions (pet_id, user_id, application_date, shelter_id) VALUES (%s, %s, CURDATE(), %s)",
                 ('1', 1, 1))
        ]

        mock_cursor.execute.assert_has_calls(expected_calls)
        mock_conn.commit.assert_called()
        self.assertIn("Pet adopted successfully!", mock_stdout.getvalue())

    @patch('main.get_db_connection')
    @patch('builtins.input', side_effect=['1'])
    @patch('sys.stdout', new_callable=StringIO)
    def test_adopt_pet_already_adopted(self, mock_stdout, mock_input, mock_get_db_connection):
        mock_conn = MagicMock()
        mock_cursor = mock_conn.cursor.return_value.__enter__.return_value
        mock_get_db_connection.return_value = mock_conn

        # Mock the cursor's fetchone method
        mock_cursor.fetchone.return_value = (1,)

        adopt_pet(1)

        mock_cursor.execute.assert_called_once_with("SELECT COUNT(*) FROM Adoptions WHERE pet_id = %s", ('1',))
        self.assertIn("This pet has already been adopted.", mock_stdout.getvalue())

    @patch('main.get_db_connection')
    @patch('builtins.input', side_effect=['1'])
    @patch('sys.stdout', new_callable=StringIO)
    def test_cancel_adoption_success(self, mock_stdout, mock_input, mock_get_db_connection):
        mock_conn = MagicMock()
        mock_cursor = mock_conn.cursor.return_value.__enter__.return_value
        mock_get_db_connection.return_value = mock_conn

        # Mock the cursor's fetchone method
        mock_cursor.fetchone.return_value = (1,)

        cancel_adoption(1)

        expected_calls = [
            call("SELECT COUNT(*) FROM Adoptions WHERE pet_id = %s AND user_id = %s", ('1', 1)),
            call("DELETE From Adoptions WHERE pet_id = %s AND user_id = %s", ('1', 1))
        ]

        mock_cursor.execute.assert_has_calls(expected_calls)
        mock_conn.commit.assert_called()
        self.assertIn("Pet adoption is canceled successfully!", mock_stdout.getvalue())

    @patch('main.get_db_connection')
    @patch('builtins.input', side_effect=['1'])
    @patch('sys.stdout', new_callable=StringIO)
    def test_cancel_adoption_not_adopted_by_user(self, mock_stdout, mock_input, mock_get_db_connection):
        mock_conn = MagicMock()
        mock_cursor = mock_conn.cursor.return_value.__enter__.return_value
        mock_get_db_connection.return_value = mock_conn

        # Mock the cursor's fetchone method
        mock_cursor.fetchone.return_value = (0,)

        cancel_adoption(1)

        mock_cursor.execute.assert_called_once_with("SELECT COUNT(*) FROM Adoptions WHERE pet_id = %s AND user_id = %s",
                                                    ('1', 1))
        self.assertIn("This pet is not adopted by you.", mock_stdout.getvalue())


if __name__ == '__main__':
    unittest.main()
