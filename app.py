from flask import Flask, render_template, url_for, request
import googleapiclient.discovery
import googleapiclient.errors
from datetime import datetime
import os

app = Flask(__name__)

def convert_date(date_string):
    date_obj = datetime.strptime(date_string, '%Y-%m-%dT%H:%M:%SZ')
    return date_obj.strftime('%d/%m/%Y')

def get_channel_id(api_key, channel_name_or_custom_url):
    youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=api_key)

    request = youtube.search().list(
        part="snippet",
        type="channel",
        q=channel_name_or_custom_url,
        maxResults=1
    )
    response = request.execute()
   
    if response["items"]:
        return response["items"][0]["snippet"]["channelId"]
    else:
        return None

def get_channel_videos(api_key, channel_id):
    youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=api_key)

    request = youtube.channels().list(
        part="contentDetails",
        id=channel_id
    )
    response = request.execute()
    playlist_id = response["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]

    videos = []
    next_page_token = None

    while True:
        request = youtube.playlistItems().list(
            part="snippet",
            playlistId=playlist_id,
            maxResults=50,
            pageToken=next_page_token
        )
        response = request.execute()
        videos.extend(response["items"])

        next_page_token = response.get("nextPageToken")

        if next_page_token is None:
            break

    return videos

def get_video_titles(videos):
    video_titles = []

    for video in videos:
        video_titles.append(video["snippet"]["title"])

    return video_titles

def get_video_titles_and_urls(videos):
    video_data = []

    for video in videos:
        video_title = video["snippet"]["title"]
        video_url = video['snippet']['resourceId']['videoId']
        video_publishedAt = convert_date(video["snippet"]["publishedAt"])
        video_data.append({"title": video_title, "url": video_url, "publishedAt": video_publishedAt})

    return video_data

@app.route('/')
@app.route('/home')
def home():
    return render_template("index.html")

@app.route('/result', methods=['POST', 'GET'])
def result():
    output = request.form.to_dict()
    print(output)
    name = output["name"]

    api_key = os.environ.get("API_KEY")
    channel_id = get_channel_id(api_key, name)

    if channel_id:
        videos = get_channel_videos(api_key, channel_id)
        video_data = get_video_titles_and_urls(videos)
        video_data.reverse()
    else:
        video_data = None

    return render_template('index.html', name=name, video_data=video_data)

if __name__ == "__main__":
    app.run(debug=True)