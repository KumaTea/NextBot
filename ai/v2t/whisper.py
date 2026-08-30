import io

from v2t.base import *
from v2t.media import download


logging.info('Loading faster-whisper')


from faster_whisper import WhisperModel


# CTranslate2 quantises at load time, so the published float16 checkpoint is
# taken as-is and the weights end up int8 with float32 activations.
DEVICE = 'cpu'
COMPUTE_TYPE = 'int8'

# CTranslate2 defaults to 4 threads whatever the machine happens to have.
CPU_THREADS = os.cpu_count() or 4

# resolves to mobiuslabsgmbh/faster-whisper-large-v3-turbo; the name needs
# faster-whisper >= 1.1
MODEL_ID = 'large-v3-turbo'


logging.info(f'Loading whisper {MODEL_ID} ({COMPUTE_TYPE}, {CPU_THREADS} threads)')
# https://github.com/SYSTRAN/faster-whisper

whisper_model = WhisperModel(
    MODEL_ID,
    device=DEVICE,
    compute_type=COMPUTE_TYPE,
    cpu_threads=CPU_THREADS,
)

logging.info('Done.')


class ModelStorage:
    def __init__(self, model):
        self.model = model
        self.run_at = datetime.now()


model_storage = ModelStorage(whisper_model)


def _transcribe(source):
    """
    The blocking half, to be run off the event loop.

    Nothing here branches on how long the audio is. faster-whisper implements
    the sliding 30-second window itself and stitches the segments back
    together, so a two-second voice note and a twenty-minute recording take the
    same path -- which is the whole 3000-mel-features class of failure gone,
    rather than guarded against.

    `transcribe` hands back a segment *generator* and does no decoding until it
    is walked, so the join below is where the CPU time actually goes. It has to
    happen inside this function, not at the call site.
    """
    segments, info = model_storage.model.transcribe(
        source,
        # silence is where whisper invents things; the Silero VAD cuts it out
        # before the model ever sees it
        vad_filter=True,
        # the previous window is not fed back in as a prompt: it costs a little
        # consistency across window boundaries and buys immunity from the
        # repetition loops long audio otherwise falls into. This is also what
        # the transformers pipeline did here before, which defaults it off.
        condition_on_previous_text=False,
    )
    # each segment's text already carries its own leading space
    return ''.join(segment.text for segment in segments).strip(), info


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

        # No probing for a video stream and no ffmpeg pass to strip one out:
        # PyAV opens the container and decodes stream `audio=0` from it, so an
        # mp4 is handed over exactly like an ogg.
        if file_data:
            source = io.BytesIO(file_data)
        elif file_path:
            source = file_path
        else:
            raise ValueError('nothing to transcribe')

        t0 = time.time()
        text, info = await asyncio.to_thread(_transcribe, source)
        elapsed = time.time() - t0

        # info carries the decoded length, so nothing has to ask ffprobe and
        # then disagree with it
        speed = f', {info.duration / elapsed:.1f}x' if elapsed else ''
        logging.info(
            f'Time: {elapsed:.3f}s ({info.duration:.0f}s {info.language}{speed})'
            f'\tTranscribed: {text}'
        )
        return text
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
