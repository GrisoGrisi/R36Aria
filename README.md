# R36Aria
Torrenting client UI for R36S consoles, using Aria2 client as a base made by the goat Tatsuhiro Tsujikawa.

Just drag and drop .torrent files on the /torrents folder and edit /config/options.json to add them to the ui:

"nombre": Name that will appear on the main menu of the app.

"magnet": Magnet link in case you want to use a magnet instead of a .torrent file.

"torrent_path": Path to the .torrent file, just add the .torrent file name, or a absolute path like /roms/torrents/example.torrent in case you want to store the .torrent files anywhere else.

"carpeta_destino": Path where the downloaded files will be saved.


# EXAMPLE:

{
  "opciones": [
    {
      "nombre": "Example 1",
      "magnet": "magnet:?xt=urn:btih:REPLACE_WITH_REAL_HASH",
      "carpeta_destino": "/roms/ports/downloads"
    },
    {
      "nombre": "Example 2",
      "torrent_path": "example.torrent",
      "carpeta_destino": "/examples"
    },
    {
      "nombre": "Example 3",
      "torrent_path": "/roms/torrents/example.torrent",
      "carpeta_destino": "/roms/downloaded_file_examples"
    }
  ]
}

This is all vibe coded btw, im trying to learn coding, this project helped me a lot to understand how python and git works, please don´t be too harsh lol.
You can use this project to do whathever you want if it helps you. 

# Aria2 was made by Tatsuhiro Tsujikawa.
https://aria2.github.io/
