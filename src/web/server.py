import os
from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename
import sys
import os
from db import connect_to_mysql, connect_to_database, read_db_infos

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from fingerprint.fingerprint import fingerprint


UPLOAD_FOLDER = r'static/uploads'
ALLOWED_EXTENSIONS = {'mp3'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# read db infos
db_info = read_db_infos(r"..\..\song_db\db_info.txt")
# set db infos
host = db_info["host"]
user = db_info["user"]
password = db_info["password"]
fingerprints_table = db_info["fingerprints_table"]
song_infos_table = db_info["song_infos_table"]
database_name = db_info["database_name"]

def allowed_file(filename):
	return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def home():
	return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
	if 'file' not in request.files:
		return jsonify({'error': 'No file part'}), 400

	file = request.files['file']
	if file.filename == '':
		return jsonify({'error': 'No selected file'}), 400

	if not allowed_file(file.filename):
		return jsonify({'error': 'File type not allowed'}), 400

	filename = secure_filename("query.mp3")
	file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

	result = search()
	print(result)

	return jsonify({'message': 'File uploaded successfully', 
		'filename': result["file_name"],
		'songname': result["song_name"],
		"artists": result["artists"]}), 200

def search():
	# fingerprint query 
	query_path = os.path.join(app.config["UPLOAD_FOLDER"], "query.mp3")

	hashes, query_offsets = fingerprint(query_path)
	hashes_str = ', '.join(map(str, hashes))
	query_offsets_str = ', '.join(map(str, query_offsets))
	
	# connect to db and perform retrieval
	db_conn = connect_to_database(host, user, password, database_name)
	if db_conn:
		cursor = db_conn.cursor()

		hashes_offsets_values = [(str(h), str(o)) for h, o in zip(hashes, query_offsets)]
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

		result = cursor.fetchall()

		if not result:
			return {
				"file_name": None,
				"song_name": None,
				"artists": None,
			}

		result = result[0]
		offset_diff = result[1]

		# no match hashes
		if not result or result[2] == 0:
			return {
				"file_name": None,
				"song_name": None,
				"artists": None,
			}

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

		db_conn.close()

		return {
			"file_name": result[0],
			"song_name": result[1],
			"artists": result[2],
		}

if __name__ == '__main__':
	app.run(host="0.0.0.0", port=8091, ssl_context='adhoc', debug=True)