<!-- PROJECT INTRO -->

OrpheusDL - Bugs!
=================

A Bugs! module for the OrpheusDL modular archival music program

[Report Bug](https://github.com/Dniel97/orpheusdl-bugsmusic/issues)
·
[Request Feature](https://github.com/Dniel97/orpheusdl-bugsmusic/issues)


## Table of content

- [About OrpheusDL - Bugs!](#about-orpheusdl---bugs)
- [Getting Started](#getting-started)
    - [Prerequisites](#prerequisites)
    - [Installation](#installation)
- [Usage](#usage)
- [Configuration](#configuration)
    - [Global](#global)
    - [Bugs](#bugs)
- [Contact](#contact)



<!-- ABOUT ORPHEUS -->
## About OrpheusDL - Bugs!

OrpheusDL - Bugs! is a module written in Python which allows archiving from **[bugs.co.kr](https://music.bugs.co.kr/)** for the modular music archival program.


<!-- GETTING STARTED -->
## Getting Started

Follow these steps to get a local copy of Orpheus up and running:

### Prerequisites

* Already have [OrpheusDL](https://github.com/yarrm80s/orpheusdl) installed

### Installation

1. Go to your `orpheusdl/` directory and run the following command:
   ```sh
   git clone https://github.com/Dniel97/orpheusdl-bugsmusic.git modules/bugs
   ```
2. Execute:
   ```sh
   python orpheus.py
   ```
3. Now the `config/settings.json` file should be updated with the Bugs! settings

<!-- USAGE EXAMPLES -->
## Usage

Just call `orpheus.py` with any link you want to archive:

```sh
python orpheus.py https://music.bugs.co.kr/track/5311931
```

<!-- CONFIGURATION -->
## Configuration

You can customize every module from Orpheus individually and also set general/global settings which are active in every
loaded module. You'll find the configuration file here: `config/settings.json`

### Global

```json5
"global": {
    "general": {
        // ...
        "download_quality": "hifi"
    },
    "covers": {
	    "main_resolution": 3000,
	    // ...
    }
}
```

`download_quality`: Choose one of the following settings:
* "hifi": same as lossless
* "lossless": FLAC with 44.1kHz/16bit
* "high": AAC 320 kbit/s
* "medium": MP3 320 kbit/s
* "low": same as minimum
* "minimum": AAC 128 kbit/s

`main_resolution`: Bugs! supports officially 75, 140, 200, 350, 500 and 1000x1000px (scaled) artworks, 
orpheusdl-bugsmusic also supports the following resolutions: 1400 and 2000x2000px. If set to 3000, the original
artwork will be downloaded.

### Bugs!
```json
{
    "username": "",
    "password": ""
}
```
`username`: Enter your Bugs! email/username address here

`password`: Enter your Bugs! password here

**Note:** Only VIP accounts are currently supported.

**Note:** Playlists are not (yet) supported.

<!-- Contact -->
## Contact

Dniel97 - [@Dniel97](https://github.com/Dniel97)

Project Link: [OrpheusDL Bugs! Public GitHub Repository](https://github.com/Dniel97/orpheusdl-bugsmusic)
