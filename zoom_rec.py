import os
import requests
import urllib.parse


class ZoomClient:
    def __init__(self, account_id: str, client_id: str, client_secret: str):
        self.account_id = account_id
        self.client_id = client_id
        self.client_secret = client_secret
        self.base_url = "https://api.zoom.us/v2"
        self.access_token = self._get_access_token()

    def _get_access_token(self) -> str:
        """Fetch OAuth access token using account credentials grant."""
        url = "https://zoom.us/oauth/token"
        params = {"grant_type": "account_credentials", "account_id": self.account_id}
        response = requests.post(url, params=params, auth=(self.client_id, self.client_secret))
        response.raise_for_status()
        return response.json()["access_token"]

    def get_recording_by_meeting_url(self, detail_url: str) -> dict:
        """Fetch recording info using a Zoom meeting detail URL."""
        parsed = urllib.parse.urlparse(detail_url)
        query = urllib.parse.parse_qs(parsed.query)
        meeting_id = query.get("meeting_id", [None])[0]
        if not meeting_id:
            raise ValueError("Invalid Zoom URL: missing meeting_id")

        # decode and re-encode meeting ID for API
        meeting_id_encoded = urllib.parse.quote(urllib.parse.unquote(meeting_id), safe="")
        url = f"{self.base_url}/meetings/{meeting_id_encoded}/recordings"
        headers = {"Authorization": f"Bearer {self.access_token}"}

        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()

    def download_recording(self, recording_info: dict, download_dir: str = "zoom_downloads") -> list:
        """
        Download MP4/M4A files from recording info.
        Returns list of downloaded file paths.
        """
        if not recording_info:
            return []

        os.makedirs(download_dir, exist_ok=True)
        downloaded_files = []

        topic = recording_info.get("topic", "NoTopic").replace(" ", "_")
        meeting_id = recording_info.get("id")
        files = recording_info.get("recording_files", [])

        for file in files:
            file_type = file.get("file_type")
            if file_type not in ["MP4", "M4A"]:
                continue

            download_url = f"{file['download_url']}?access_token={self.access_token}"
            filename = f"{topic}_{meeting_id}_{file['id']}.{file_type.lower()}"
            filepath = os.path.join(download_dir, filename)

            with requests.get(download_url, stream=True) as r:
                if r.status_code == 200:
                    with open(filepath, "wb") as f:
                        for chunk in r.iter_content(chunk_size=8192):
                            f.write(chunk)
                    downloaded_files.append(filepath)
                else:
                    print(f"❌ Failed to download {file_type}: {r.text}")

        return downloaded_files

