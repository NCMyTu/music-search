import mysql.connector
from mysql.connector import Error
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from fingerprint.fingerprint import fingerprint

def connect_to_mysql(host, user, password):
	try:
		connection = mysql.connector.connect(
			host=host,
			user=user,
			password=password
		)
		if connection.is_connected():
			return connection
	except Error as e:
		return None

def create_database(connection, database_name):
	try:
		cursor = connection.cursor()
		cursor.execute(f"CREATE DATABASE IF NOT EXISTS {database_name}")
	except Error as e:
		return

def connect_to_database(host, user, password, database_name):
	try:
		connection = mysql.connector.connect(
			host=host,
			user=user,
			password=password,
			database=database_name
		)
		if connection.is_connected():
			return connection
	except Error as e:
		return None

def read_song_infos_from_file(path):
	infos = []

	with open(path, encoding="utf-8") as file:
		lines = file.readlines()

		for line in lines:
			temp = [element.strip() for element in line.split("|||")]
			file_name, song_name, artists = temp
			info = (file_name+".mp3", song_name, artists)
			infos.append(info)

	return infos

def read_db_infos(path):
	info = {}

	with open(path, encoding="utf-8") as file:
		lines = file.readlines()

		for line in lines:
			temp = [element.strip() for element in line.split("=")]
			info[temp[0]] = temp[1]

	return info

if __name__ == "__main__":
	db_info = read_db_infos(r"..\..\song_db\db_info.txt")
	host = db_info["host"]
	user = db_info["user"]
	password = db_info["password"]
	fingerprints_table = db_info["fingerprints_table"]
	song_infos_table = db_info["song_infos_table"]
	database_name = db_info["database_name"]
	
	connection = connect_to_mysql(host, user, password)
	if connection:
		create_database(connection, database_name)
		connection.close()
	
	song_dir = r"..\..\song_db\songs"
	infos_dir = r"..\..\songs_info.txt"

	infos = read_song_infos_from_file(infos_dir)

	db_connection = connect_to_database(host, user, password, database_name)
	if db_connection:
		cursor = db_connection.cursor()

		# create tables
		# cursor.execute(f"DROP TABLE IF EXISTS {song_infos_table}")
		# cursor.execute(f"DROP TABLE IF EXISTS {fingerprints_table}")

		cursor.execute(f"""
			CREATE TABLE IF NOT EXISTS {song_infos_table} (
				song_id INT NOT NULL AUTO_INCREMENT,
				file_name VARCHAR(255) NOT NULL,
				song_name VARCHAR(255) NOT NULL,
				artists VARCHAR(255) NOT NULL,
				PRIMARY KEY (song_id)	
			)
		""")

		cursor.execute(f"""
			CREATE TABLE IF NOT EXISTS {fingerprints_table} (
				song_id INT NOT NULL,
				hash INT UNSIGNED NOT NULL,
				offset INT UNSIGNED NOT NULL,
				PRIMARY KEY (song_id, hash, offset)
				INDEX (hash)
			)
		""")

		count = 0
		# insert song infos and fingerprint them
		for info in infos:
			song_infos_insert = f'''
				INSERT INTO {song_infos_table} (file_name, song_name, artists)
				VALUES (%s, %s, %s)
			'''
			cursor.execute(song_infos_insert, info)
			db_connection.commit()

			song_id = cursor.lastrowid

			song_path = os.path.join(song_dir, info[0])
			hashes, offset = fingerprint(song_path)
			
			fingerprint_data = [(song_id, int(h), int(o)) for h, o in zip(hashes, offset)]

			fingerprints_insert = f"""
				INSERT INTO {fingerprints_table} (song_id, hash, offset)
				VALUES (%s, %s, %s)
			"""
			cursor.executemany(fingerprints_insert, fingerprint_data)
			db_connection.commit()	

			count += len(hashes)
			print(f"processed {info[0]}, number of hashes: {len(hashes)}")

		print(f"number of fingerprints (hash): {count}")

		# query = f"SELECT * FROM {song_infos_table}"
		# cursor.execute(query)
		# rows = cursor.fetchall()
		# print(rows)

		query = f"SELECT COUNT(*) FROM {fingerprints_table}"
		cursor.execute(query)
		n_rows = cursor.fetchone()[0]
		print(f"number of fingerprints (db): {n_rows}")

		db_connection.close()