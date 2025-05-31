from v2t.base import *
from v2t.media import download, is_video, extract_audio, get_audio_length


logging.info('Loading torch')


import torch


logging.info('Loading transformers')


from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline


# device = 'cuda:0' if torch.cuda.is_available() else 'cpu'
device = 'cpu'
# torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32
torch_dtype = torch.float32

MODEL_ID = 'openai/whisper-large-v3-turbo'


logging.info('Loading whisper-large-v3-turbo')
# https://huggingface.co/openai/whisper-large-v3-turbo#usage

whisper_model = AutoModelForSpeechSeq2Seq.from_pretrained(
    MODEL_ID,
    torch_dtype=torch_dtype,
    # low_cpu_mem_usage=True,
    device_map='auto',
    use_safetensors=True
)
# model.to(device)

whisper_processor = AutoProcessor.from_pretrained(MODEL_ID)

whisper_pipe = pipeline(
    'automatic-speech-recognition',
    model=whisper_model,
    tokenizer=whisper_processor.tokenizer,
    feature_extractor=whisper_processor.feature_extractor,
    torch_dtype=torch_dtype,
    # device=device,
    # ValueError: The model has been loaded with `accelerate` and therefore cannot be moved to a specific device.
)

logging.info('Done.')

class ModelStorage:
    def __init__(self, model, processor, pipe):
        self.model = model
        self.processor = processor
        self.pipe = pipe
        self.run_at = datetime.now()


model_storage = ModelStorage(whisper_model, whisper_processor, whisper_pipe)


async def whisper_transcribe(url: str = '', file_path: str = '', file_data: bytes = b'') -> str:
    logging.info('Transcribing...')

    try:
        audio_path = None
        video_path = None
        model_storage.run_at = datetime.now()


        # ====== download ======
        if url:
            logging.info('Downloading...')
            audio_path = await download(url)
            logging.info('Downloaded: ' + audio_path)
            file_path = audio_path
            if await is_video(audio_path):
                logging.info('Video detected, extracting audio...')
                video_path = await extract_audio(file_path)
                logging.info('Extracted: ' + file_path)
                file_path = video_path

        # ====== detect ======
        audio_length = await get_audio_length(file_path)
        is_long_audio = audio_length >= 30  # required by whisper turbo

        # ====== transcribe ======
        t0 = time.time()
        if is_long_audio:
            result = model_storage.pipe(file_data or file_path or url, return_timestamps=True)
        else:
            result = model_storage.pipe(file_data or file_path or url)
        t = time.time()
        logging.info(f'Time: {t - t0:.3f}s\t' + 'Transcribed: ' + result['text'])

        # ====== cleanup ======
        if audio_path:
            os.remove(audio_path)
            logging.info('Deleted: ' + audio_path)
        if video_path:
            os.remove(video_path)
            logging.info('Deleted: ' + video_path)

        # ====== return ======
        if is_long_audio:
            text = '\n'.join(chunk['text'].strip() for chunk in result['chunks'] if chunk['text'].strip())
        else:
            text = result['text']
        return text
    except Exception as e:
        logging.error(e)
        return str(e)
