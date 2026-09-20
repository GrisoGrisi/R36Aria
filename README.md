# R36Aria
Torrenting client UI for R36S consoles, using Aria2 client as a base made by the goat Tatsuhiro Tsujikawa.

Just drag and drop .torrent files on the /torrents folder and edit /config/options.json to add them to the ui:

- "nombre": Name that will appear on the main menu of the app.

- "magnet": Magnet link in case you want to use a magnet instead of a .torrent file.

- "torrent_path": Path to the .torrent file, just add the .torrent file name, or a absolute path like /roms/torrents/example.torrent in case you want to store the .torrent files anywhere else.

- "carpeta_destino": Path where the downloaded files will be saved.


# EXAMPLE:

```
{

  "opciones":
  [
    
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

```

## Scan For Torrents feature ##

Additionally you can press START on the main menu to scan the /torrents folder in search of .torrent files that had not been added to the torrents list.
Once in there you can pick a file and the on-screen keyboard will appear, once there you can manually add the name that will appear on the torrents list, 
then, after pressing START to confirm the name, you can manually type the path where the downloads will save. Press START one more time to save the changes.

With this process you can edit options.json without having to access to it.


## .zip Files Handling ##

After a download is complete, if a .zip file is detected, you’ll be given three options:

- Keep the .zip file as is (without extracting).
- Extract the contents and delete the .zip file.
- Extract the contents and keep the .zip file.

The extracted contents will be stored in the same folder, not in a subfolder.

# CONTROLS:

**Navigation Controls**

- D-Pad: Navigate through the different options.

- A: Select an option
  
- SELECT + START: Close the app. **This works at any screen.**


**Main Menu Controls**

- START: Scan the /torrents folder in search of non-added torrents.


**On-Torrent Controls**

- SELECT: Open or close the search bar.

- A: Select files to download.
  
- B: Return to the main menu.
  
- X: Start download.


**Search bar controls:**



- A: Type the selected letter.

- Y: Delete the last character.

- X: Insert a space.

- B: Clear the search bar and close the on-screen keyboard.

- L1: Switch between Lowercase and Uppercase.

- SELECT or START: Close the search bar with the filter applied.




### Notes ###

This is all vibe coded btw, im still learning coding, this project helped me a lot to understand how OOP, python and git works, please don´t be too harsh lol.

You can use this project to do whathever you want if it helps you. 
This project was tested on dArkOSRE-R36 03082026, on a genuine R36S-V22 2024-12-18

*Feel free to add issues with suggestions.*

# Aria2 was made by Tatsuhiro Tsujikawa.
https://aria2.github.io/
