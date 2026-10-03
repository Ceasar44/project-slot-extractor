"""Build baking GGUFs with the shared real builder and a search default."""

import sys

from scripts.quantize.build_phase05_real import main as build_real


def main(argv=None):
    arguments = list(sys.argv[1:] if argv is None else argv)
    if not any(arg == "--config" or arg.startswith("--config=") for arg in arguments):
        arguments = ["--config", "configs/quantization/baking_search_v1.yaml", *arguments]
    return build_real(arguments)


if __name__ == "__main__":
    raise SystemExit(main())
