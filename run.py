import argparse
import os
import sys

from satprep.api.server import serve


def main():
    parser = argparse.ArgumentParser(
        description="TutorSat - local server")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--db", default="satprep.db",
                        help="SQLite database file (default: ./satprep.db)")
    parser.add_argument("--google-client-id", default=None,
                        help=("Google OAuth client ID for Sign-In; falls back "
                              "to the GOOGLE_CLIENT_ID environment variable"))
    parser.add_argument("--allowed-origins", default="",
                        help=("Comma-separated origins allowed to call the API "
                              "cross-origin; falls back to "
                              "SATPREP_ALLOWED_ORIGINS"))
    parser.add_argument("--stateless-secret", default=None,
                        help=("HMAC secret for /api/x stateless mode; falls "
                              "back to SATPREP_STATELESS_SECRET"))
    args = parser.parse_args()
    client_id = args.google_client_id or os.environ.get("GOOGLE_CLIENT_ID")
    origins = args.allowed_origins or os.environ.get("SATPREP_ALLOWED_ORIGINS", "")
    secret = args.stateless_secret or os.environ.get("SATPREP_STATELESS_SECRET")
    serve(host=args.host, port=args.port, db_path=args.db,
          google_client_id=client_id, allowed_origins=origins,
          stateless_secret=secret)


if __name__ == "__main__":
    sys.exit(main())
