import numpy as np
import time
import librosa
import os
from web.db import connect_to_mysql, connect_to_database, read_db_infos
from fingerprint.fingerprint import compute_spectrogram, compute_constellation_map, create_group, \
									create_hashes, fingerprint, fingerprint_with_noise

def query_from_db(db_info, hashes, offsets):
	host = db_info["host"]
	user = db_info["user"]
	password = db_info["password"]
	fingerprints_table = db_info["fingerprints_table"]
	song_infos_table = db_info["song_infos_table"]
	database_name = db_info["database_name"]

	hashes_str = ', '.join(map(str, hashes))
	query_offsets_str = ', '.join(map(str, offsets))

	result = None

	# connect to db and perform retrieval
	db_conn = connect_to_database(host, user, password, database_name)
	if db_conn:
		cursor = db_conn.cursor()

		hashes_offsets_values = [(str(h), str(o)) for h, o in zip(hashes, offsets)]
		cursor.execute("""
			CREATE TEMPORARY TABLE input_hashes (
				hash INT UNSIGNED,
				offset INT UNSIGNED
			)
		""")
		cursor.executemany("""
			INSERT INTO input_hashes (hash, offset) 
			VALUES (%s, %s)
		""", hashes_offsets_values)
		query = f"""
			SELECT 
				db.song_id, 
				ABS(CAST(db.offset AS SIGNED) - CAST(ih.offset AS SIGNED)) AS offset_diff,
				COUNT(*) AS count
			FROM 
				{fingerprints_table} AS db
			JOIN 
				input_hashes AS ih
			ON 
				db.hash = ih.hash
			GROUP BY 
				db.song_id, offset_diff
			ORDER BY 
				count DESC
			LIMIT 5;
		"""
		cursor.execute(query)

		result = cursor.fetchall()[0]

		# no match hashes
		if not result or result[2] == 0:
			return None

		song_id = result[0]
		query = f"""
			SELECT 
				file_name, song_name, artists 
			FROM 
				{song_infos_table} 
			WHERE 
				song_id = {song_id};
		"""
		cursor.execute(query)

		result = cursor.fetchall()[0]

		result = {
			"file_name": result[0],
			"song_name": result[1],
			"artists": result[2]
		}

		db_conn.close()

	return result


margin = 10 # exclude margin seconds from start and end of each song
query_length_sec = 7 # duration in seconds of query audio
noise_factor = 0.5

db_info = read_db_infos(r"..\song_db\db_info.txt")
songs_dir = r"..\song_db\songs"
file_names = os.listdir(songs_dir)
# file_names = np.random.permutation(file_names) #shuffle
count = 0
n_songs = len(file_names)

for i in range(n_songs):
	np.random.seed(i)
	song_path = os.path.join(songs_dir, file_names[i])
	
	x, sr = librosa.load(song_path)
	duration = int(len(x) / sr)

	start = np.random.randint(margin, duration-margin-query_length_sec+1)
	end = start + query_length_sec
	print(f"progress: {i}/{n_songs}, start at {start}s, end at {end}s, ", end="")

	# hashes, offsets = fingerprint(song_path, 
	# 								start=start,
	# 				 				end=end)
	hashes_noise, offsets_noise = fingerprint_with_noise(song_path,
														start=start, 
														end=end,
														noise_factor=noise_factor, 
														random_state=2)

	# query_result = query_from_db(db_info, hashes, offsets)
	query_result = query_from_db(db_info, hashes_noise, offsets_noise)

	print(f"ground_truth: {file_names[i]}, predict: {query_result["file_name"]}")
	
	if query_result["file_name"] == file_names[i]:
		count += 1

print(f"number of seconds: {query_length_sec}")
print(f"noise factor: {noise_factor}")
print(f"number of correct: {count} / {len(file_names)}")
print(f"accuracy: {count / len(file_names):.2f}")
