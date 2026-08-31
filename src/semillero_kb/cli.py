"""Minimal command-line boundary for canonical research records."""
import argparse
from pathlib import Path

from .yaml_records import load_yaml


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="semillero-kb")
    commands = parser.add_subparsers(dest="command", required=True)
    validate = commands.add_parser("validate", help="validate one canonical YAML record")
    validate.add_argument("path", type=Path)
    args = parser.parse_args(argv)
    try:
        record = load_yaml(args.path)
    except ValueError as error:
        parser.error(f"{args.path}: {error}")
    print(f"{args.path}: valid {type(record).__name__} id={record.id} version={record.version}")
    return 0