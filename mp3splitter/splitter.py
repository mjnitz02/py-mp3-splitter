import os
import re
from time import sleep

import cloudscraper
import requests
from pydub import AudioSegment


class Splitter:
    RETRY_DELAY_DURATION = 0.3

    def run(
        self,
        input_path,
        output_path,
        release_id,
        overlap_offset=0,
    ):
        print(f"Loading input path: {input_path}")
        song = AudioSegment.from_mp3(input_path)

        print(f"Retrieving metadata for: {release_id}")
        metadata = self.get_metadata(release_id)
        tracklist = metadata.get("tracklist", [])

        if len(tracklist) == 0:
            raise ValueError("No tracklist found in metadata")

        os.makedirs(output_path, exist_ok=True)

        reference_position = 0
        for track in tracklist:
            export_path = self.get_export_name(track, output_path)
            print(f"Exporting: {export_path}")
            tags = self.get_mp3_tags(metadata, track)
            elapsed_time = self.get_elapsed_duration(track["duration"])
            elapsed_time -= overlap_offset
            song_data = song[reference_position : reference_position + elapsed_time]
            song_data.export(export_path, format="mp3", tags=tags)

            reference_position += elapsed_time

    @staticmethod
    def get_elapsed_duration(duration):
        minutes, seconds = duration.split(":")
        elapsed_time = (int(minutes) * 60 + int(seconds)) * 1000
        return elapsed_time

    @staticmethod
    def get_mp3_tags(metadata, track_info):
        tags = {
            "track": track_info["position"],
            "title": track_info["title"],
            "artist": track_info["artists"][0]["name"],
            "album": metadata["title"],
            "albumartist": metadata["artists"][0]["name"],
        }
        return tags

    @staticmethod
    def get_export_name(track_info, output_path):
        position = track_info["position"]
        artist = track_info["artists"][0]["name"]
        title = track_info["title"]
        export_name = f"{position} - {artist} - {title}.mp3"
        export_name = re.sub(r'[\\/*?:"<>|]', "", export_name)
        return os.path.join(output_path, export_name)

    def get_metadata(self, release_id):
        url = f"https://api.discogs.com/releases/{release_id}"
        response = self.request_with_retry(url)
        return response.json()

    @classmethod
    def request_with_retry(cls, url, params=None, retries=3, timeout=30):
        with cloudscraper.create_scraper() as scraper:
            request_parameters = {"url": url, "params": params, "timeout": timeout}

            attempt = 0
            while attempt < retries:
                try:
                    response = scraper.get(**request_parameters)
                    if response.status_code == 200:
                        sleep(cls.RETRY_DELAY_DURATION)
                        return response
                    # If the status code wasn't success, retry
                    attempt += 1
                    sleep(5 * attempt)
                # If the request times out, retry
                except requests.exceptions.Timeout:
                    attempt += 1
                    sleep(5 * attempt)

            raise EnvironmentError(f"Failed to receive response from {url} after {retries} attempts")
