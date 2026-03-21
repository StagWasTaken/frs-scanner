# Frs Scanner (For us unlicensed in anything else folk)
## Purpose
I think it's becoming less common of a gift but I think many households still keep walkie talkie toys, and this ~~intercept messages~~ alerts you when there is someone nearby to talk with.
## Limitations and Config
- FRS obviously is limited to 2W, and is a really high frequency, so you are only gonna hear neighbors ofc.
- Some FRS channels are lower power, so if you want alerts for that you need to make a separate above-floor threshold for 8-14
- This is a wideband scanner, so it scans a lot of channels at once but not all of them at once because the FRS band is too wide for the rtl
- You must set the discord webhook in main,py or it won't send alerts (guh)
- The 2 most important constants for configuration are SIGNAL_THRESHOLD and CONFIRM_CYCLES. Signal threshold filters out weak interference, (db above floor), and cycles determines how many scans activity on a channel must be to be considered a real transmission and not just an RF spike. Alert cooldown ofc prevents your webhook from being spammed.
- Nearby walkie talkies will probably notify for their actual channel AND that channel +7. But you shouldn't have your walkie talkie that close, for you can damage your sdr.
![](/demo.PNG)
