# Music Search
Search for songs based on audio input.

## Set up
1. Collect your songs (in .mp3 format) and place them in the `/song_db/songs` directory.  
2. Create a `/song_db/songs_info.txt` file containing song information in the following format: {file_name_without_extension} ||| {song_name} ||| {artists}.  
3. Set your database root password in `/song_db/db_info.txt`.
   
I have already added 10 example songs. To avoid copyright infringement, I can't provide more.

## How to run
1. Install MySQL 8.0.40
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Fingerprint collected songs:
   ```bash
   python src/web/db.py
   ```
4. Run the web app:
   ```bash
   python src/web/server.py
   ```
5. To test performance:
   ```bash
   python src/test.py
   ```
There will be some path-related errors.

## References
**Avery Li-Chun Wang.** "An Industrial-Strength Audio Search Algorithm."  
https://www.audiolabs-erlangen.de/resources/MIR/FMP/C7/C7S1_AudioIdentification.html  
https://willdrevo.com/fingerprinting-and-audio-recognition-with-python/ 
