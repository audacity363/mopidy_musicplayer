import mpd
import spotipy
import pygst
import gst
import time
import argparse


class Player:
    
    uri = ""
    player = None
    
    def __init__(self, http_url):
        self.uri = http_url

    def start_player(self):
        self.player = gst.element_factory_make("playbin", "player")
        self.player.set_property("uri", self.uri)
        self.player.set_state(gst.STATE_PLAYING)

    def restart_player(self, timeout=1):
        time.sleep(timeout)
        self.start_player()

class MyMPDClient:

    host = ""
    password = ""

    client = None
    spot_client = None

    def __init__(self, host, password):
       self.host = host
       self.password = password

       self.spot_client = spotipy.Spotify()
       self.connect()

    def connect(self):
        self.client = mpd.MPDClient()
        self.client.timeout = 10
        self.client.connect(self.host, 6600)
        self.client.password(self.password)

    def disconnect(self):
       self.client.close()
       self.client.disconnect()

    def changePlaylist(self, newPlaylist):
        self.client.pause()
        self.client.clear()
        self.client.load(newPlaylist)
        self.client.play()

    def getPlaylistsNames(self):
        returnlist = []
        for plist in self.client.listplaylists():
            returnlist.append(plist["playlist"])
        return returnlist

    def getTrackNamesFromPlaylist(self, playlistname):
        returnlist = []
        try:
            tracks = self.client.listplaylist(playlistname)
        except mpd.ConnectionError:
            self.connect()
            tracks = self.client.listplaylist(playlistname)
#check if spotify playlist
        if tracks[0][0:13] == "spotify:track":
            tracks_chunks = self.chunks(tracks, 50)
            for chunk in tracks_chunks:
                cur = self.spot_client.tracks(chunk)["tracks"]
                for song in cur:
                    returnlist.append(song["name"])
        else:
            for song in songs:
                returnlist.append(song)
        return returnlist

    def getCurrentSong(self):
        try:
            return self.client.currentsong()
        except mpd.ConnectionError:
            self.connect()
            return self.client.currentsong()

    def getCurrentState(self):
        try:
            return self.client.status()
        except mpd.ConnectionError:
            self.connect()
            return self.client.status()

    def chunks(self, l, n):
        """Yield successive n-sized chunks from l."""
        for i in range(0, len(l), n):
            yield l[i:i + n]

parser = argparse.ArgumentParser()

parser.add_argument("--host", action="store", dest="host", help="Host on which mopidy is running")
parser.add_argument("--password", action="store", dest="passwd", help="Password for the mopidy MPD server")

results = parser.parse_args()

gstPlayer = Player("http://"+results.host+":8000/mopidy")
mpdclient = MyMPDClient(results.host, results.passwd)

while True:
    input_str = raw_input("CMD: ")
    if input_str == "playlists":
        for plist in mpdclient.getPlaylistsNames():
            print plist
    elif input_str == "change":
        i=0
        plists = mpdclient.getPlaylistsNames()
        for plist in plists:
            print "[%d] %s" % (i, plist)
            i+=1
        number = raw_input("Play Playlist number: ")
        mpdclient.changePlaylist(plists[int(number)])
        gstPlayer.restart_player()
    elif input_str == "song":
        song = mpdclient.getCurrentSong()
        print "Current Song:"
        print "\tTitle:  "+song["title"]
        print "\tAlbum:  "+song["album"]
        print "\tArtist: "+song["artist"]
    elif input_str == "restart":
        gstPlayer.restart_player(0)
    elif input_str == "quit":
        break
    else:
        print "Commands:"
        print "\tplaylists"
        print "\tchange"
        print "\tquit"

mpdclient.disconnect()
