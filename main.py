import os
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
import webbrowser
import time

# Scopes required for managing playlists
scopes = ["https://www.googleapis.com/auth/youtube.force-ssl"]


# YouTube API initialization
def youtube_authenticate():
    api_service_name = "youtube"
    api_version = "v3"
    client_secrets_file = "client_secret.json"  # Your OAuth 2.0 credentials file

    # Get credentials and create an API client
    flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(client_secrets_file, scopes)

    # Use run_local_server() for OAuth authentication
    credentials = flow.run_local_server(port=0)

    youtube = googleapiclient.discovery.build(api_service_name, api_version, credentials=credentials)
    return youtube


# Search for a song on YouTube
def search_song(youtube, song_name):
    request = youtube.search().list(
        q=song_name,
        part="snippet",
        maxResults=1
    )
    response = request.execute()

    # Return the video ID of the top result
    if 'items' in response and len(response['items']) > 0:
        video_id = response['items'][0]['id']['videoId']
        return video_id
    return None


# Add a video to a playlist with retry mechanism
def add_to_playlist(youtube, playlist_id, video_id):
    for attempt in range(3):  # Retry up to 3 times
        try:
            request = youtube.playlistItems().insert(
                part="snippet",
                body={
                    "snippet": {
                        "playlistId": playlist_id,
                        "resourceId": {
                            "kind": "youtube#video",
                            "videoId": video_id
                        }
                    }
                }
            )
            response = request.execute()
            return response
        except googleapiclient.errors.HttpError as e:
            if e.resp.status == 409:  # Conflict error
                print(f"Conflict error: {e}")
                return None  # Skip adding this video
            print(f"An error occurred: {e}. Retrying...")
            time.sleep(2)  # Wait before retrying
    print("Failed to add video after retries.")
    return None


# Main function to add all songs from folder to playlist
def add_songs_to_playlist(playlist_id):
    # Authenticate YouTube API
    youtube = youtube_authenticate()

    # Read the list of song names from file (or directory) with specified encoding
    with open('songslist.txt', 'r', encoding='utf-8') as file:
        songs = file.readlines()

    # Process each song
    for song in songs:
        song = song.strip()
        print(f"Searching for: {song}")
        video_id = search_song(youtube, song)
        if video_id:
            print(f"Adding to playlist: {song}")
            add_to_playlist(youtube, playlist_id, video_id)
        else:
            print(f"No results found for: {song}")
        time.sleep(2)  # Avoid hitting rate limits


if __name__ == "__main__":
    # Playlist ID of the target playlist (you can find this in the playlist URL)
    PLAYLIST_ID = "PLh4yzueUYkCJg22PVbSnSETe9BMEj1_8E"
    add_songs_to_playlist(PLAYLIST_ID)
