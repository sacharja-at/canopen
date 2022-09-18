# canopen

canopen is a Python-script written for use under graphical desktop environments under Linux, that uses plaintext-configuration files to let you decide which (type of) file to open with which command.

I wrote it, because I found the mechanisms provided by the respective desktop environments (like xdg-open) not powerful/flexible enough and simply, not to be to my liking.

Also, with canopen, I have a much easier time to keep my configurations up to date on different machines by just updating canopen's configuration files between them, which is very easy to do.

**Disclaimer**: canopen is my very first “real” project, I am a computer technician by trade, and a mere self-taught and pretty much unprofessional programmer. Except a lot of mistakes typically made by bloody amateurs, and a lot of mistakes in general.

**Table Of Contents:**

* [License](#license)
* [Requirements](#requirements)
* [Installation](#installation)
* [Options](#options)
* [Configuration](#configuration)
  * [paths of configuration files](#paths-of-configuration-files)
  * [format of configuration files](#format-of-configuration-files)
    * [keyword mime](#keyword-mime)
    * [keyword pattern](#keyword-pattern)
    * [keyword alias](#keyword-alias)
    * [keyword setting](#keyword-setting)
      * [key fallback](#key-fallback)
      * [key messenger](#key-messenger)
      * [key loadconfig](#key-loadconfig)
* [Bugs](#bugs)


## License
Copyright © 2022 Zacharias Korsalka <sacharja@sacharja.at>

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright  notice, this list of conditions and the following disclaimer in the  documentation and/or other materials provided with the distribution.

This software is provided by the copyright holders and contributors “as is” and any express or implied warranties, including, but not limited to, the implied warranties of merchantability and fitness for a particular purpose are disclaimed. In no event shall the copyright owner or contributors be liable for any direct, indirect, incidental, special, exemplary, or consequential damages (including, but not limited to, procurement of substitute goods or services; loss of use, data, or profits; or business interruption) however caused and on any theory of liability, whether in contract, strict liability, or tort (including negligence or otherwise) arising in any way out of the use of this software, even if advised of the possibility of such damage.

## Requirements

canopen is a script for graphical desktop environments for Linux-systems. It requires a Python-interpreter (Python 3) and to be run under a Unix-like system.

## Installation

Since canopen is basically just a plain script. I suggest to

* download `canopen.py`, rename it to `canopen`, put it into `/usr/local/bin` and make it executable,
* create a directory `.config/canopen` in your home-directory,
* download the sample configuration, copy it to `.config/canopen/canopen` and modify it to your needs.
* Once you have a proper configuration, tell your graphical desktop environment to open every file with canopen from now on.

## Options

canopen accepts several command-line options:

| option | description |
| --- | --- |
| `--help` | put out help-text on standard-output and exit |
| `--show-mimes` | shows mime-types of every `FILE`, does not do anything else |
| `--simulate` | canopen will only put out what it would do on standard-output, without actually doing anything |
| `--verbose` | puts out additional information |
| `--environment NAME` | makes canopen behave as if environment `CANOPEN` was set to `NAME`, overruling any actual environment-variables |
| `--no-overwrites` | canopen will abort, if keys in configurations are overwritten by later entries |

## Configuration

Once you have installed canopen, you of course want to configure it to tell it which files to open with what. canopen reads its configuration from plain text files from `.config/canopen` in your home-directory.

### paths of configuration files

When canopen starts, it will look with which name it has been called, will take this name (minus any suffix like “.py”), and will load its configuration from a file of that name in  directory `.config/canopen` in your home directory, so if you just leave the script as it is, the configuration it will look for will of course be `~/.config/canopen/canopen`

If an environment-variable `CANOPEN` is set, canopen will use the value of this variable instead. The command-line option `--environment NAME` will make canopen use the `NAME` given instead, overruling any environment variable.

### format of configuration files

Configuration files are … something a python-script can read? … like plain-text in ASCII or UTF-8 encoding.

canopen reads its configuration line by line.

Everything that comes after the first hash-sign (“#”) will be ignored, as will lines which are empty (or consist only of empty space).

All other lines consist of a **keyword** followed by one or more spaces (or tabs), a **key**, again followed by one or more spaces (or tabs), and everything that comes after that is the **value** of that key.

Possible keywords are `alias`, `setting`, `mime` and `pattern`.

If a certain alias, mime or pattern is configured repeatedly, canopen will always use the last one specified unless the command-line-option `--no-overwrites` has been set.

#### keyword mime

It may be determined which file to open with which command via the *mime-type* of a file, canopen uses Linux' command `file` to determine the mime-type of files.

If you want to see which mime-type canopen thinks a file has, just use the command-line option `--show-mimes`:

```
canopen --show-mimes FILE...
```

Please mind that the list will only put out a list of the form *mediatype/subtype,* canopen does not care about encodings.

You may now specify which command is to be used to open files of a certain media-type in general, or more specifically of a certain media-type and sub-type. They keyword of the (line of) configuration will of course be “mime”, the key will be the media-type or the media-type followed by a slash and a sub-type, a configuration with a media-type *and* a sub-type always overrules a configuration, where only a media-type is specified.


```
mime  text/html  firefox
mime  text       geany
```

In this example, all files of media-type text are opened with geany, except that for HTML-files, which are to be opened with firefox.

#### keyword pattern
I found it insufficient to only identify files via their mime-types, so canopen is able to match the base name of a file (this is, everything without any leading directories) to patterns as are used on command-line-interfaces on Unix and Unix-like systems. The key of the configuration is the pattern, the value is the command with which to open the file matched. Patterns in canopen are, however, not case-sensitive.

Pattern-matches overrule mime-matches.

```
mime     text/html  firefox
mime     text       geany
pattern  DEADJOE    true
```

This example solves the (self-inflicted, btw) problem that my favorite terminal-texteditor `joe` leaves files called “DEADJOE” behind him when I close files uncleanly. Since a “DEADJOE” is a plain text, canopen would open it with `geany`, but since pattern-rules overrule mime-rules, and pattern `DEADJOE` of course matches those files, canopen opens those files with `true` – which simply doesn't do anything with its command-line arguments, so canopen will simply not bother me with these files anymore when I just open all files in a directory.

#### keyword alias

An “alias” allows you to define an alias for a specific command (or even other alias), which makes maintenance of configurations *much* easier. The key is the name of the alias, the value is the command the alias stands for.

In this context, it is important to remember that canopen no longer cares about spaces in a line of a configuration file once the part for the value is reached, so a value may as well contain spaces.

```
mime     application/ogg  AUDIO
mime     audio            AUDIO
mime     audio/midi       MIDI
pattern  *.wav            UNCOMPR-AUDIO
alias    UNCOMPR-AUDIO    AUDIO
alias    AUDIO            xterm -e mplayer -ao pulse
alias    MIDI             qmmp
```

In this example, the alias `AUDIO` is used to open all “normal” audio-files, alias `UNCOMPR-AUDIO` refers to `AUDIO`, while `AUDIO` itself calls xterm with some arguments to have the file played in a terminal-window.

canopen will exit if it detects loops within aliases.

Also, I use capital letters for aliases for convenience, it is not a requirement.

#### keyword setting

Keys following the keyword `setting` influence canopen's behaviour. Valid keys for settings are:

* fallback
* messenger
* loadconfig

##### key fallback

Normally, canopen will abort with an error if it gets files to open for which it does not find a command for. If a `fallback` is defined, canopen will use this command to open all those files. Example:

```
setting   fallback   gxmessage -title canopen failed to open:
```

##### key messenger

By default, canopen will put out any error-messages on standard-output. If “messenger” is set, the respective text will be given to an external command. Example:

```
setting   messenger   gxmessage -title canopen
```

##### key loadconfig

It is possible to connect configuration files, this is, to load a configuration file out of another.

So, let's say there is a configuration file `types` in which you basically define, which type of file is what:

```
mime     application/ogg  AUDIO
mime     audio            AUDIO
mime     audio/midi       MIDI
pattern  *.wav            UNCOMPR-AUDIO
```

In your default configuration, you may simply load these types and define, which actual programmes are to be used:

```
setting   loadconfig      types
alias     UNCOMPR-AUDIO   AUDIO
alias     AUDIO           xterm -e mplayer -ao pulse
alias     MIDI            qmmp
```

With that method, you might define e.g. an alternative configuration file `altcon`, in which you include the same file as in the default configuration, but define other aliases:

```
setting   loadconfig      types
alias     UNCOMPR-AUDIO   audacity
alias     AUDIO           audacious
alias     MIDI            qmmp
```

So, yes, “loadconfig” is basically canopen's equivalent to include- and import-commands in programming languages.

canopen, however, will allow you to load any single configuration file only once. This is first and foremost to prevent looping calls, but also to stop me from getting too weird in my configurations.

## Bugs
I started this project (at least in this form, which is a completely new script) literally two days ago before I uploaded it today. But I take it that the mechanism about displaying messenges is really not clean, as are many other things. See the disclaimer at the top of this file.