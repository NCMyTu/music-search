import librosa

def get_audio_metadata(file_path):
    try:
        y, sr = librosa.load(file_path, sr=None)  # Load audio file
        duration = librosa.get_duration(y=y, sr=sr)  # Duration in seconds
        channels = 1 if len(y.shape) == 1 else y.shape[0]  # Number of channels

        metadata = {
            'duration_seconds': duration,
            'sample_rate': sr,
            'channels': channels
        }
        return metadata

    except Exception as e:
        print(f"Error extracting metadata: {e}")
        return None

# Example usage
file_path = r"C:\Users\PC MY TU\Desktop\CK IR\static\uploads\query.mp3"
metadata = get_audio_metadata(file_path)

if metadata:
    print(f"Duration: {metadata['duration_seconds']} seconds")
    print(f"Sample Rate: {metadata['sample_rate']} Hz")
    print(f"Channels: {metadata['channels']}")