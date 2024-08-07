#!/usr/bin/env python3

import sys
import asyncio
import selectors
import subprocess


PROJECT = 'rbsk'

GIT_CMDS = [
    'git pull',
    'git submodule update --init --recursive',
    'git pull --recurse-submodules',
    'git submodule update --remote --recursive',  # --force
]

DOCKER_CMDS = [
    f'docker stop {PROJECT}',
    f'sudo bash -c \"echo \'\' > \\$(docker inspect --format=\'{{.LogPath}}\' {PROJECT})\"'
]

START_CMDS = [
    f'docker start {PROJECT}'
]

EXIT_CMDS = [
    # exit and following the docker container logs
    f'docker logs {PROJECT} -f'
]


async def run_cmds(cmds: list[str]):
    for cmd in cmds:
        proc = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        return_code = proc.returncode
        out = '\n'.join([f'\t{line}' for line in stdout.decode().splitlines()])
        err = '\n'.join([f'\t{line}' for line in stderr.decode().splitlines()]) if stderr else ""
        print(f'>>> {cmd}\n{out}\n{err}\n')
        if return_code:
            sys.exit(return_code)


def popen_reader(p: subprocess.Popen) -> tuple:
    # borrowed from https://github.com/KumaTea/pypy-wheels/blob/main/src/tools.py
    sel = selectors.DefaultSelector()
    sel.register(p.stdout, selectors.EVENT_READ)
    sel.register(p.stderr, selectors.EVENT_READ)
    result = ''
    error = ''

    print_func = print
    done = False
    while not done:
        for key, _ in sel.select():
            data = key.fileobj.read1().decode()
            if not data:
                done = True
                break
            if key.fileobj is p.stdout:
                result += data
                print_func(data, end="")
            else:
                error += data
                print_func(data, end="", file=sys.stderr)

    p.wait()
    return result, error


async def main():
    await asyncio.gather(
        run_cmds(GIT_CMDS),
        run_cmds(DOCKER_CMDS)
    )

    await run_cmds(START_CMDS)

    try:
        for cmd in EXIT_CMDS:
            proc = subprocess.Popen(cmd, shell=True)
            popen_reader(proc)
    except KeyboardInterrupt:
        print('Interrupted by user')
        sys.exit(0)
