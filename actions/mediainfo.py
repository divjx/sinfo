import asyncio


async def mi(path: str) -> dict:
    cmd = ['mediainfo', path]

    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await proc.communicate()

    if proc.returncode != 0:
        return {'text': f'Error running mediainfo: {stderr.decode()[:300]}', 'files': []}

    return {'text': stdout.decode(errors='replace').strip(), 'files': []}
