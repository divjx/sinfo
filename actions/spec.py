import asyncio
import os


async def get_spec(path: str) -> dict:
    output_path = os.path.splitext(path)[0] + '_spectrogram.png'

    cmd = [
        'ffmpeg', '-y',
        '-i', path,
        '-lavfi', 'showspectrumpic=s=1024x512:mode=combined:color=intensity', output_path
        ]

    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
        )
    stdout, stderr = await proc.communicate()

    if proc.returncode != 0:
        raise RuntimeError(f'ffmpeg failed: {stderr.decode()[-300:]}')

    return {'text': None, 'files': output_path}
