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

# whisper turbo wants at least this much audio before timestamps are usable
LONG_AUDIO_SECONDS = 30


logging.info('Loading whisper-large-v3-turbo')
# https://huggingface.co/openai/whisper-large-v3-turbo#usage

whisper_model = AutoModelForSpeechSeq2Seq.from_pretrained(
    MODEL_ID,
    torch_dtype=torch_dtype,
    # loads the weights straight into their final home instead of building a
    # second full copy first -- roughly halves peak memory during startup
    low_cpu_mem_usage=True,
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
    """
    Transcribe audio, from a URL, a path or raw bytes.

    Raises on failure rather than returning the error text: the caller turns an
    exception into a 500, whereas a returned string used to be published as if
    it were the transcription.
    """
    logging.info('Transcribing...')
    model_storage.run_at = datetime.now()

    # everything created here, removed on the way out however we leave.
    # /dev/shm is a RAM disk, so leaked scratch files are leaked memory.
    scratch = []

    try:
        if url:
            logging.info('Downloading...')
            downloaded = await download(url)
            scratch.append(downloaded)
            logging.info('Downloaded: ' + downloaded)
            file_path = downloaded

            if await is_video(downloaded):
                logging.info('Video detected, extracting audio...')
                audio_path = await extract_audio(downloaded)
                scratch.append(audio_path)
                logging.info('Extracted: ' + audio_path)
                file_path = audio_path

        source = file_data or file_path or url
        if not source:
            raise ValueError('nothing to transcribe')

        audio_length = await get_audio_length(file_path) if file_path else 0
        is_long_audio = audio_length >= LONG_AUDIO_SECONDS

        t0 = time.time()
        # the pipeline is blocking CPU work; on the event loop it would stall
        # the health endpoint the frontend uses to decide the backend is alive
        if is_long_audio:
            result = await asyncio.to_thread(
                model_storage.pipe, source, return_timestamps=True
            )
        else:
            result = await asyncio.to_thread(model_storage.pipe, source)
        logging.info(f'Time: {time.time() - t0:.3f}s\t' + 'Transcribed: ' + result['text'])

        if is_long_audio:
            return '\n'.join(
                chunk['text'].strip()
                for chunk in result['chunks'] if chunk['text'].strip()
            )
        return result['text']
    finally:
        # counted from when the work finished, so a long job cannot be cut
        # short by the idle timer part way through
        model_storage.run_at = datetime.now()
        for path in scratch:
            try:
                os.remove(path)
                logging.info('Deleted: ' + path)
            except OSError as e:
                logging.warning(f'Could not delete {path}: {e}')
