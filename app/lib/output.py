import sys
import threading


wlock = threading.Lock()


def puts(string, include_newline=True, stderr=False):
    with wlock:
        ending = "\n" if include_newline else ""
        f = sys.stderr if stderr else sys.stdout
        print(string, end=ending, file=f, flush=True)
