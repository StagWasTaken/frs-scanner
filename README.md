# Frs Scanner (For us unlicensed in anything else folk)
## Purpose
I think it's becoming less common of a gift but I think many households still keep walkie talkie toys, and this ~~intercept messages~~ alerts you when there is someone nearby to talk with.
## Limitations and Config
- FRS obviously is limited to 2W, and is a really high frequency, so you are only gonna hear neighbors ofc.
- Some FRS channels are lower power, so if you want alerts for that you need to make a separate above-floor threshold for 8-14
- You must set the discord webhook in main,py or it won't send alerts (guh)
- The 2 most important constants for configuration are SIGNAL_THRESHOLD and CONFIRM_CYCLES. Signal threshold filters out weak interference, (db above floor), and cycles determines how many scans activity on a channel must be to be considered a real transmission and not just an RF spike. Alert cooldown ofc prevents your webhook from being spammed.
![](/demo.PNG)
