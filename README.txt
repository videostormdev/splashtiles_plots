Push data example with plotting   Splash-tiles.com
------------------------------------------------

This example shows how you can push text, image and python generated plots to your Splash-tiles.com cloud account for display on your TVs or any other monitor.

This specific example is for a temp and humidity control system.  It is using a Raspberry Pi to read temp and humidity from a SDC30 sensor and uses these values to control a blower fan on GPIO.

It also is using the PI camera to take timelapse photos (latest photo always uploaded to SplashTiles.com for monitoring).  (seperate process using raspistill)

The text data is stored in a tmp file /tmp/mon_runstat

The python plot data HTML5 goes to tmp file /tmp/mon_plot



About Splash-tiles.com
------------------------------------
Splash-tiles.com is a freemium cloud service that does a great many things.  For this example, we are using the "push data" capability which is completely free (no cc needed).  We are pushing our data to the cloud, then diplaying that data on the TV using the (free) SplashTiles Android TV app.  Push data screens automatically update whenever our data changes, so this makes a great real time monitoring system.

Splash-tiles.com also offers real time 2 way control using Firebase realtime db with python support.  See our other examples for this.

