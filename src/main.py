from __future__ import annotations
from .cli import run_cli, build_argparser

def main():
    parser = build_argparser()
    args = parser.parse_args()
    run_cli(args.csv_path)

if __name__ == "__main__":
    main()
