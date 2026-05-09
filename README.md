# HomeLab

# Services
#### Jellyfin
**Description**
Jellyfin is a home entertainment media server that lets you browse and play different kinds of media such as Movies, TV-shows and Music.
**Setup**
Running Jellyfin service:
```
cd docker/jellyfin
docker compose up -d
```
Stopping Jellfin service:
```
cd docker/jellyfin
docker compose down
```
#### Youtube-music-downloader
**Description**
Youtube-music-downloader is a custom built app that lets you download videos from youtube using yt-dlp and it will automatically download into the jellyfin music folder.
**Setup**
Running Youtube-music-downloader service:
```
cd docker/youtube-music-downloader
docker compose up -d --build
```
Stopping Youtube-music-downloader service:
```
cd docker/youtube-music-downloader
docker compose down
```
#### ...
