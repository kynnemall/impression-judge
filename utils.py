from resemblyzer.hparams import *
from resemblyzer import trim_long_silences, normalize_volume

def preprocess_audio(fpath, t_start=0, t_end=-1):
    """
    Load audio file and preprocess so that the resemblyzer voice encoder
    can embed the data. Start and end times can be specified so that only
    the section of interest can be extracted and put through the encoder.
    
    fpath: path to audio file (string)
    t_start: start time in seconds (int)
    t_end: end time in seconds (int)
    
    Returns:
        wav: numpy array of processed autio data
    """
    wav, source_sr = librosa.load(fpath, sr=None)
    start_idx = source_sr * t_start
    if t_end == -1:
        end_idx = -1
    else:
        end_idx = source_sr * t_end
    
    # Resample the wav
    if source_sr is not None:
        wav = librosa.resample(wav, source_sr, sampling_rate)
        
    # Apply the preprocessing: normalize volume and shorten long silences
    wav = normalize_volume(wav, audio_norm_target_dBFS, increase_only=True)
    wav = trim_long_silences(wav)
    return wav[start_idx:end_idx]
