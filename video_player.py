import vlc

def play_video(path):
    # Create a new instance of the VLC player
    player = vlc.Instance()

    # Create a new media instance for the video file
    media = player.media_new(path)

    # Create a new media player instance and set the media instance
    media_player = player.media_player_new()
    media_player.set_media(media)

    # Start playing the video
    media_player.play()

    # Wait for the video to finish playing
    while True:
        state = media_player.get_state()
        if state == vlc.State.Ended:
            break

    # Release the media player and media instances
    media_player.release()
    media.release()

