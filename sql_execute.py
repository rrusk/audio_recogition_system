#!/usr/bin/env python3
"""
A command-line utility to execute a single read query on the project's SQLite database.
"""
import argparse
import sys
import sqlite3
from argparse import RawTextHelpFormatter

from libs.db_sqlite import SqliteDatabase


def main():
    """Main function to parse arguments and execute the query."""
    parser = argparse.ArgumentParser(
        description="Execute a single SQL query and print the first result.",
        formatter_class=RawTextHelpFormatter,
    )
    parser.add_argument(
        "-q", "--query", required=True, help="The SQL query to execute."
    )
    args = parser.parse_args()

    try:
        # Use a 'with' statement to properly manage the database connection
        with SqliteDatabase() as db:
            try:
                row = db.execute_one(args.query)
                print(row)
            except sqlite3.Error as e:
                # Handle potential SQL errors gracefully
                print(f"Database error: {e}", file=sys.stderr)
                return 1  # Return an error code

    except sqlite3.Error as e:
        # Handle database connection errors
        print(f"Database connection error: {e}", file=sys.stderr)
        return 1
    except argparse.ArgumentError as e:
        # Handle argument parsing errors
        print(f"Argument error: {e}", file=sys.stderr)
        return 1

    return 0  # Success


if __name__ == "__main__":
    sys.exit(main())
