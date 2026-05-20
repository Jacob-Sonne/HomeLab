# HomeLab

# Services
This section describes all the different services available to run in the homelab project from what they do to how to run it.
___
#### Jellyfin
**Acessible at: http://jellyfin.home**
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
___
#### Kavita
**Accessible at: http://kavita.home**
**Description**
Kavita is a home entertainment media server that lets you browse written media like comics, manga and ebooks.
___
#### Youtube-music-downloader
**Acessible at: http://youtube.home**
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
___
#### ...

# TODO
- Add some kind of dashboard or homepage for navigating services without knowing specific routes (IP:PORT) or url like homelab/grafana. (Homepage / Homarr)
- Reverse Proxy? Nginx for finegrained manual control. Traefik for automatic detection but less control. Possibly a hybrid mix?
- Other media downloaders.
- Kavita for written media like comics, manga, ebooks.
- Audiobookshelf for audiobooks.
- 