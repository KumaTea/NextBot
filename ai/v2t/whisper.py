from v2t.base import *


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
        model_storage.run_at = datetime.now()
        t0 = time.time()
        result = model_storage.pipe(url or file_path or file_data)
        t = time.time()
        logging.info(f'Time: {t - t0:.3f}s\t' + 'Transcribed: ' + result['text'])
        return result['text']
    except Exception as e:
        logging.error(e)
        return str(e)
