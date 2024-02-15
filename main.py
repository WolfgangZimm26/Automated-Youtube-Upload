import os
from typing import List
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
import googleapiclient.http



def find_video_files(folder_path: str, file_extension: str = ".mp4") -> List[str]:
    """
    Finds video files in the specified folder with the given file extension.

    :param folder_path: Path to the folder where video files are located.
    :param file_extension: The extension of the video files to find.
    :return: List of video file paths.
    """
    try:
        video_files = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if f.endswith(file_extension)]
        assert len(video_files) > 0, "No video files found in the folder."
        return video_files
    except Exception as e:
        print(f"Error finding video files: {e}")
        return []

def initialize_youtube_client():
    try:
        os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"  # For local testing only!
        client_secrets_file = "client_secrets.json"
        scopes = ["https://www.googleapis.com/auth/youtube.upload"]
        flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
            client_secrets_file, scopes=scopes)
        credentials = flow.run_local_server()
        return googleapiclient.discovery.build("youtube", "v3", credentials=credentials)
    except Exception as e:
        print(f"Error initializing YouTube client: {e}")
        return None

def upload_video(youtube, file_path, title, description, category, tags, privacy_status):
    try:
        request_body = {
            "snippet": {
                "categoryId": category,
                "title": title,
                "description": description,
                "tags": tags
            },
            "status": {
                "privacyStatus": privacy_status
            }
        }

        media_file = googleapiclient.http.MediaFileUpload(file_path)

        request = youtube.videos().insert(
            part="snippet,status",
            body=request_body,
            media_body=media_file
        )

        response = request.execute()
        print(f"Upload successful for {file_path}. Response:", response)
    except googleapiclient.errors.HttpError as e:
        print(f"An HTTP error occurred: {e.resp.status} {e.content}")
    except Exception as e:
        print(f"An error occurred during video upload: {e}")



def main():
    folder_path = "D:\\Test_videos"  # Use double backslashes for Windows paths
    video_files = find_video_files(folder_path)

    youtube = initialize_youtube_client()
    if youtube is None:
        return

    for video_file in video_files:
        title = input(f"Enter the title for the video '{os.path.basename(video_file)}': ")
        description = input("Enter the description for the video: ")
        category = input("Enter the category ID for the video: ")
        tags = input("Enter the tags for the video (comma-separated): ").split(',')
        privacy_status = input("Enter the privacy status (public, private, or unlisted): ")

        upload_video(youtube, video_file, title, description, category, tags, privacy_status)
        print("Video Uploaded:", video_file)

if __name__ == "__main__":
    main()