"""Minimal command-line boundary for canonical research records."""
import argparse
from datetime import datetime, timezone
from pathlib import Path

from .curation import curate_record, promote_record
from .yaml_records import dump_yaml
from .yaml_records import load_yaml


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="semillero-kb")
    commands = parser.add_subparsers(dest="command", required=True)
    validate = commands.add_parser("validate", help="validate one canonical YAML record")
    validate.add_argument("path", type=Path)
    for command, help_text in (("curate", "admit a candidate as a human seed"),
                               ("promote", "promote a human seed after validation")):
        action = commands.add_parser(command, help=help_text)
        action.add_argument("path", type=Path)
        action.add_argument("--curator", required=True)
        action.add_argument("--reason", required=True)
        action.add_argument("--output", type=Path, required=True)
        if command == "promote":
            action.add_argument("--validation-evidence", action="append", required=True)
    args = parser.parse_args(argv)
    try:
        record = load_yaml(args.path)
        if args.command == "curate":
            record = curate_record(record, curator=args.curator, rationale=args.reason, curated_at=datetime.now(timezone.utc))
        elif args.command == "promote":
            record = promote_record(record, curator=args.curator, rationale=args.reason,
                                    curated_at=datetime.now(timezone.utc), validation_evidence=args.validation_evidence)
    except ValueError as error:
        parser.error(f"{args.path}: {error}")
    if args.command != "validate":
        if args.output == args.path:
            parser.error("curation output must be a new path to preserve the original record")
        args.output.write_text(dump_yaml(record), encoding="utf-8")
        print(f"{args.output}: {record.admission_state} id={record.id}")
        return 0
    print(f"{args.path}: valid {type(record).__name__} id={record.id} version={record.version}")
    return 0
