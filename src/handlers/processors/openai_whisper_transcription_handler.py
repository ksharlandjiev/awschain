import torch
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline
from typing import Dict
import soundfile as sf
import numpy as np
from handlers.abstract_handler import AbstractHandler
from dotenv import load_dotenv
import os

# Transcription Handler Class
class OpenAIWhisperTranscriptionHandler(AbstractHandler):

    def handle(self, request: Dict) -> Dict:

        # Configuration for the model and device
        device = "cpu"
        if torch.cuda.is_available():
            device = "cuda:0"
        # elif torch.backends.mps.is_available(): 
        #      # Detect device (MPS for Apple Silicon or CPU for others)
        #      device = "mps"
        
        torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32
        model_id = "openai/whisper-small"

        # Load model and processor only once for all instances
        model = AutoModelForSpeechSeq2Seq.from_pretrained(
            model_id, torch_dtype=torch_dtype, low_cpu_mem_usage=True, use_safetensors=True
        )
        model.to(device)
        

        processor = AutoProcessor.from_pretrained(model_id)

        # Initialize the ASR pipeline
        asr_pipeline = pipeline(
            "automatic-speech-recognition",
            model=model,
            tokenizer=processor.tokenizer,
            feature_extractor=processor.feature_extractor,
            max_new_tokens=128,
            chunk_length_s=30,
            batch_size=16,
            return_timestamps=True,
            torch_dtype=torch_dtype,
            device=device
        )
        
        # Extract the audio file path from the request
        audio_path = request.get("path")

        # Load the audio file
        audio_data, sample_rate = sf.read(audio_path)

        # If the audio has more than one channel, convert to mono
        if len(audio_data.shape) > 1:
            audio_data = np.mean(audio_data, axis=1)  # Convert to mono

        # Transcribe the audio
        transcription_result = asr_pipeline({"array": audio_data, "sampling_rate": sample_rate})

        # Update the request with the transcribed text
        request.update({"text": transcription_result["text"]})

        return super().handle(request)  # Continue with the chain
