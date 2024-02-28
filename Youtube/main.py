import os
from typing import List
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
import googleapiclient.http
from openai import OpenAI
from dotenv import load_dotenv
from typing import Optional
import pandas as pd

def read_first_sheet(file_path):
    """
    Reads the first sheet of an Excel file and returns all its columns.

    :param file_path: Path to the Excel file.
    :return: A DataFrame containing all columns from the first sheet.
    """
    # Read the first sheet of the Excel file
    df = pd.read_excel(file_path, engine='openpyxl', sheet_name=0)
    
    return df

def find_specific_video_file(video_file_name: str, folder_path: str = "D:\Test_videos") -> Optional[str]:
    """
    Finds a specific video file by name in the specified folder.

    :param video_file_name: The name of the video file to find.
    :param folder_path: Path to the folder where video files are located. Defaults to "D://Videos/".
    :return: Path to the video file if found, None otherwise.
    """
    try:
        # Ensure the video file name includes the extension, e.g., '.mp4'
        video_files = [f for f in os.listdir(folder_path) if f == video_file_name]

        if len(video_files) == 1:
            # Return the full path to the found video file
            return os.path.join(folder_path, video_files[0])
        elif len(video_files) > 1:
            print(f"Multiple files with the name {video_file_name} found. Returning the first one.")
            return os.path.join(folder_path, video_files[0])
        else:
            print("Video file not found.")
            return None
    except Exception as e:
        print(f"Error finding video file: {e}")
        return None
    
def load_and_verify_env_vars(required_vars):
    """
    Load environment variables from a .env file and verify if the required ones are set.

    :param required_vars: A dictionary where keys are the names of the required environment
                          variables and values are the human-readable names or descriptions.
    """
    load_dotenv()  # Load the environment variables from .env file

    missing_vars = []
    for var, name in required_vars.items():
        if os.environ.get(var) is None:
            missing_vars.append(f"{name} ({var})")

    if missing_vars:
        missing = ', '.join(missing_vars)
        raise ValueError(f"Missing required environment variables: {missing}")
    
def create_hashtag(video_description, number_of_hash_tags):
    client = OpenAI()
    prompt = f"Context: {video_description}\nWhat are the most popular hashtags related to the description?\nAnswer:"

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are helping someone create relative hashtags to get their videos seen more"},
            {"role": "user", "content": prompt}
        ]
    )
    
    # Assuming the API response is a single string of hashtags separated by spaces and prefixed with '#'
    hashtags = response.choices[0].message.content.strip().split(' ')
    
    # Filtering out empty strings in case of extra spaces and ensuring we only get the desired number of hashtags
    hashtags = [tag for tag in hashtags if tag][0:number_of_hash_tags]
    
    # Joining the hashtags into the desired format: '#hashtag1,#hashtag2,...,#hashtagn'
    formatted_hashtags = ','.join(hashtags)
    
    return formatted_hashtags

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
    folder_path_video = "D:\\Test_videos"  # Use double backslashes for Windows paths
    folder_path_excel = "D:\\Automated Youtube Upload\\Automated_youtube_upload_sheet.xlsx"
    num_hashtags = 8
    #Getting API Keys From Local Environment 
    required_env_vars = {
        "OPENAI_API_KEY": "OpenAI API Key",
    }
    try:
        load_and_verify_env_vars(required_env_vars)
        # Your main logic here
        print("All required environment variables are set. Proceeding with main logic.")
    except ValueError as e:
        print(f"Error: {e}")
        return  # Exit the main function if environment variables are missing
    
    # Initialize YouTube 
    youtube = initialize_youtube_client()
    if youtube is None:
        return
    # Creating a DataFrame to pull the remaining info for the videos
    my_df = read_first_sheet(folder_path_excel)
    
    for index, row in my_df.iterrows():
        video_file_name = row['Video File Name']
        video_file_path = find_specific_video_file(video_file_name, folder_path_video)
        if not video_file_path:  # If video file is not found, skip to the next iteration
            print(f"Video file {video_file_name} not found in {folder_path_video}.")
            continue
        title = row['Video Title']
        description = row['Description']
        category = str(row['Video Category Number'])  # Ensure the category is a string
        tags = create_hashtag(description, num_hashtags)
        privacy_status = row['Privacy Status']
        
        # Upload video
        upload_video(youtube, video_file_path, title, description, category, tags, privacy_status)
        print("Video Uploaded:", video_file_name)

if __name__ == "__main__":
    main()
