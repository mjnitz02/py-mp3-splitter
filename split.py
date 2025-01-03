import argparse
from mp3splitter.splitter import Splitter


def main():
    parser = argparse.ArgumentParser(description="Process an MP3 file and split it based on metadata.")
    parser.add_argument("input_file", type=str, help="Path to the input MP3 file")
    parser.add_argument("output_path", type=str, help="Path to the output directory")
    parser.add_argument("release_id", type=int, help="Release ID for fetching metadata")
    parser.add_argument("--offset", type=int, default=0, help="Overlap offset in milliseconds (default: 0)")

    args = parser.parse_args()

    splitter = Splitter()
    splitter.run(
        input_path=args.input_file,
        output_path=args.output_path,
        release_id=args.release_id,
        overlap_offset=args.offset
    )


if __name__ == "__main__":
    main()
