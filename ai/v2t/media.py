import os
import uuid
import aiohttp
import asyncio


FFMPEG_BIN = '/usr/bin/ffmpeg'
FFPROBE_BIN = '/usr/bin/ffprobe'
TMP_PATH = '/dev/shm/v2t'


async def download(url: str) -> str:
    # download file from url and return path to file
    if not os.path.exists(TMP_PATH):
        os.makedirs(TMP_PATH)
    filename = os.path.join(TMP_PATH, str(uuid.uuid4()))
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            # get returned filename
            if 'Content-Disposition' in resp.headers:
                filename = os.path.join(
                    TMP_PATH,
                    str(uuid.uuid4()) + resp.headers['Content-Disposition'].split('filename=')[1].strip('"')
                )
            with open(filename, 'wb') as f:
                while True:
                    chunk = await resp.content.read(1024)
                    if not chunk:
                        break
                    f.write(chunk)
    return filename


async def is_video(video_path: str) -> bool:
    # check if file is video
    cmd = f'{FFPROBE_BIN} -v error -select_streams v:0 -show_entries stream=codec_type -of default=noprint_wrappers=1:nokey=1 {video_path}'
    proc = await asyncio.create_subprocess_shell(cmd, stdout=asyncio.subprocess.PIPE)
    stdout, _ = await proc.communicate()
    return stdout.decode().strip() == 'video'


async def extract_audio(video_path: str) -> str:
    # extract audio from video and return path to audio file
    audio_path = os.path.join(TMP_PATH, str(uuid.uuid4()))
    cmd = f'{FFMPEG_BIN} -i {video_path} -vn -acodec copy {audio_path}'
    proc = await asyncio.create_subprocess_shell(cmd)
    await proc.communicate()
    return audio_path
