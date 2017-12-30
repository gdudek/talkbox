# talkbox
An internet-enabled artifact that plays a greeting when a button is pressed, with a different greeting every time.

This is an IoT device based on a raspberry pi (or similar microcomputer) that provides the use with a button. It is meant to be a momento/art object that provides a different simple greeting each day.

The button is meant to be pressed roughly once a day, and each time a different randomly-selected greeting is emitted.  No greeting is re-used until all recorded greetings have been played.  The greeting can also be
triggered by opening the lid (connected to a magnetic reed switch).  An additional button is present for a secondary user (who gets the secondary user greeting).

System state is saved and restored so that the file usage pattern and other state variables survive across system reboots.

The file hello.py serves as the main loop and handles GPIO processing to detect button pushes, lid openings, and vibration.
The file soundOfTheDay.py handles saving state and playing random sounds of various classes.
