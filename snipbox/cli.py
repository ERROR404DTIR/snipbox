"""Command-line interface for snipbox."""
import argparse
import json
import shutil
import subprocess
import sys
import time

from . import __version__
from .store import Store


def _read_content(args) -> str:
    if args.text:
        return args.text
    if not sys.stdin.isatty():
        return sys.stdin.read().rstrip("\n")
    print("Enter content, finish with Ctrl-D (Ctrl-Z + Enter on Windows):", file=sys.stderr)
    return sys.stdin.read().rstrip("\n")


def _copy_to_clipboard(text: str) -> bool:
    candidates = [
        ["pbcopy"],
        ["wl-copy"],
        ["xclip", "-selection", "clipboard"],
        ["xsel", "--clipboard", "--input"],
        ["clip"],
    ]
    for cmd in candidates:
        if shutil.which(cmd[0]):
            subprocess.run(cmd, input=text.encode("utf-8"), check=False)
            return True
    return False


def _row(s) -> str:
    date = time.strftime("%Y-%m-%d", time.localtime(s["created"]))
    tags = ",".join(s["tags"]) or "-"
    return f"{s['id']:>4}  {date}  {s['title'][:40]:<40}  [{tags}]"


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="snipbox", description="Save, tag, search and copy snippets.")
    p.add_argument("--version", action="version", version=f"snipbox {__version__}")
    sub = p.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("add", help="add a snippet (text arg, pipe, or interactive)")
    a.add_argument("title")
    a.add_argument("text", nargs="?", help="snippet content (omit to read stdin)")
    a.add_argument("-t", "--tag", action="append", default=[], help="tag (repeatable)")

    l = sub.add_parser("list", help="list snippets")
    l.add_argument("-t", "--tag", help="filter by tag")

    s = sub.add_parser("search", help="search title/content/tags")
    s.add_argument("query", nargs="+")

    sh = sub.add_parser("show", help="print a snippet's content")
    sh.add_argument("id", type=int)

    c = sub.add_parser("copy", help="copy a snippet to the clipboard")
    c.add_argument("id", type=int)

    r = sub.add_parser("rm", help="delete a snippet")
    r.add_argument("id", type=int)

    sub.add_parser("tags", help="list all tags with counts")

    e = sub.add_parser("export", help="export everything as JSON to stdout")
    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    store = Store()

    if args.cmd == "add":
        content = _read_content(args)
        if not content.strip():
            print("error: empty content", file=sys.stderr)
            return 1
        snip = store.add(args.title, content, args.tag)
        print(f"saved #{snip['id']}: {snip['title']}")
    elif args.cmd == "list":
        items = store.list(args.tag)
        if not items:
            print("no snippets yet")
        for s in items:
            print(_row(s))
    elif args.cmd == "search":
        items = store.search(" ".join(args.query))
        if not items:
            print("no matches")
            return 1
        for s in items:
            print(_row(s))
    elif args.cmd == "show":
        s = store.get(args.id)
        if not s:
            print(f"error: no snippet #{args.id}", file=sys.stderr)
            return 1
        print(s["content"])
    elif args.cmd == "copy":
        s = store.get(args.id)
        if not s:
            print(f"error: no snippet #{args.id}", file=sys.stderr)
            return 1
        if _copy_to_clipboard(s["content"]):
            print(f"copied #{s['id']} to clipboard")
        else:
            print("no clipboard tool found; printing instead:\n", file=sys.stderr)
            print(s["content"])
    elif args.cmd == "rm":
        if store.remove(args.id):
            print(f"removed #{args.id}")
        else:
            print(f"error: no snippet #{args.id}", file=sys.stderr)
            return 1
    elif args.cmd == "tags":
        for tag, n in store.tags().items():
            print(f"{tag:<20} {n}")
    elif args.cmd == "export":
        print(json.dumps(store.list(), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
