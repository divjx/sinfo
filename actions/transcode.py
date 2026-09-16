import asyncio
import os


async def run(path: str, target_format: str = 'mp3') -> dict:
    output_path = os.path.splitext(path)[0]+'.'+target_format
    cmd = ['ffmpeg', '-y', '-i', path, output_path]
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stdin=asyncio.subprocess.PIPE
        )
    _, stderr = await proc.communicate()

    if proc.returncode != 0:
        raise RuntimeError(
            f'ffmpeg (transcode) failed: {stderr.decode()[-300:]}'
        )

    return {'text': None, 'files': output_path}
