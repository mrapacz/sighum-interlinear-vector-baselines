#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "qrcode[pil]>=8.0",
# ]
# ///
"""Generate a QR code for the poster."""

from __future__ import annotations

import argparse
from pathlib import Path

DEFAULT_URL = "https://mrapacz.com/eacl2026"
DEFAULT_OUTPUT = Path("figures/poster/qr.png")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default=DEFAULT_URL, help="URL to encode")
    parser.add_argument(
        "--output", type=Path, default=DEFAULT_OUTPUT, help="Output path"
    )
    parser.add_argument("--box-size", type=int, default=20, help="Pixels per QR module")
    parser.add_argument("--border", type=int, default=2, help="Border width in modules")
    args = parser.parse_args()

    import qrcode

    qr = qrcode.QRCode(box_size=args.box_size, border=args.border)
    qr.add_data(args.url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="transparent").convert("RGBA")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    img.save(args.output)
    print(f"QR code → {args.output}  ({args.url})")


if __name__ == "__main__":
    main()
