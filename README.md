# ESP Restart
There's a weird bug in the esp32 devices I have... So this script is to watch the mqtt queue and see all the devices that publish... If a device doesn't post in over X minutes, it'll try and restart the device. Also every 6 hours the device will be restarted anyways... The data isn't important... not enough to require super granular metrics. 

## Usage
`./restart-cron.py HOST USER PW`