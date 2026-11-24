"""Generate QR code images for each exhibit's live URL (e.g. from Cloudflare Tunnel).

Run this once the server and tunnel are live and you know the URL:

    python scripts/generate_qr.py --space-url https://random-words.trycloudflare.com
    python scripts/generate_qr.py --url https://random-words.trycloudflare.com --session P8
    python scripts/generate_qr.py --url https://random-words.trycloudflare.com --live

Two PNG files are written to artifacts/:
    artifacts/qr-van-gogh.png
    artifacts/qr-t-rex.png

Print or scan them to open the exhibit page straight away.
Requires `qrcode[pil]` (included in requirements.txt).
"""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ARTIFACTS_DIR = ROOT / "artifacts"


def make_qr(url: str, out_path: Path) -> None:
    """Write a single QR code PNG for `url` to `out_path`."""
    try:
        import qrcode
    except ImportError:
        print("qrcode is not installed. Run:  pip install 'qrcode[pil]'", file=sys.stderr)
        sys.exit(1)

    qr = qrcode.QRCode(
        # Version None lets the library pick the smallest version that fits the data.
        version=None,
        # ERROR_CORRECT_M means the code can still scan even if up to 15% of it is
        # damaged or obscured — useful when the printout gets a bit crumpled.
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    img.save(out_path)
    print(f"Written: {out_path.relative_to(ROOT)}  ({url})")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--url", "--space-url",
        dest="url",
        required=True,
        help="The public base URL (e.g. from Cloudflare Tunnel: https://random-words.trycloudflare.com)",
    )
    parser.add_argument(
        "--session",
        help="Label a user test, e.g. P8: adds ?session=P8 to the links and -P8 to the file names",
    )
    parser.add_argument(
        "--live",
        action="store_true",
        help="Point the codes at the animated page (/live) instead of the plain page, and add -live to the file names",
    )
    args = parser.parse_args()

    # Strip trailing slashes so we can always append the path cleanly.
    base = args.url.rstrip("/")
    page = "/live" if args.live else "/"
    session = f"&session={args.session}" if args.session else ""
    suffix = ("-live" if args.live else "") + (f"-{args.session}" if args.session else "")

    exhibits = [
        ("van-gogh", f"{base}{page}?persona=van-gogh{session}"),
        ("t-rex",    f"{base}{page}?persona=t-rex{session}"),
    ]

    for persona_id, url in exhibits:
        out_path = ARTIFACTS_DIR / f"qr-{persona_id}{suffix}.png"
        make_qr(url, out_path)

    print("\nDone. QR codes are written to artifacts/ ready for testers to scan.")


if __name__ == "__main__":
    main()
