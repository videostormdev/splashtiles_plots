
import time
import pycurl
# from StringIO import StringIO
import glob
import os



# this function will push the data to Splash-tiles.com slot slt
#  pushtyp = 0 (plaintext in datafnam)
#          = 1 (image file imgfnam + any text in datafnam)
#          = 2 (HTML5 in datafnam)

#  token must be set to your Splash-tiles.com browser token

#  SSL verify is disabled must in case your device doesn't have updated SSL certs
#    you can enable if your device is up to date

def st_pushdata(pushtyp, datafnam, imgfnam, slt, token):
	fo = open(datafnam,"r")
	fdata = fo.read()
	fo.close


	# buf = StringIO()
	c = pycurl.Curl()
	c.setopt(pycurl.URL, 'https://splash-tiles.com/console/server/pushdata.php')
	if (pushtyp==2):
		#HTML5
		send = [("txt", fdata),
			("slot", slt),
			("typ","2"),
			("token", token),]
	elif (img):
		send = [("txt", fdata),
			("slot", slt),
			("token", token),
			("img", (pycurl.FORM_FILE, imgfnam)),]
	else:
		send = [("txt", fdata),
			("slot", slt),
			("token", token),]
		
	c.setopt(pycurl.HTTPPOST, send)
	c.setopt(pycurl.SSL_VERIFYPEER, 0)
	c.setopt(pycurl.SSL_VERIFYHOST, 0)
	# c.setopt(c.WRITEDATA, buf)
	c.setopt(pycurl.VERBOSE, 1)
	c.perform()

	print(c.getinfo(pycurl.RESPONSE_CODE))
	# print(buf.getvalue())
	c.close()

