#imports for thermometer reading
import os
import glob
import time
#imports for gmail reading
import imaplib
import email

# wiringpi numbers  
import wiringpi2 as wiringpi
wiringpi.wiringPiSetup()
wiringpi.pinMode(0, 1) # sets WP pin 0 to output 

#Find temperature from thermometer
os.system('modprobe w1-gpio')
os.system('modprobe w1-therm')

base_dir = '/sys/bus/w1/devices/'
device_folder = glob.glob(base_dir + '28*')[0]
device_file = device_folder + '/w1_slave'

def read_temp_raw():
    f = open(device_file, 'r')
    lines = f.readlines()
    f.close()
    return lines

def read_temp():
    lines = read_temp_raw()
    while lines[0].strip()[-3:] != 'YES':
        time.sleep(0.2)
        lines = read_temp_raw()
    equals_pos = lines[1].find('t=')
    if equals_pos != -1:
        temp_string = lines[1][equals_pos+2:]
        temp_c = float(temp_string) / 1000.0
        temp_f = temp_c * 9.0 / 5.0 + 32.0
        return temp_c #, temp_f

#connect to gmail
def read_gmail():
    global varSubject
    mail = imaplib.IMAP4_SSL('imap.gmail.com')
    mail.login('raspberrypinest@gmail.com','remoteheating')
    mail.select('inbox')
    mail.list()

    typ, data = mail.search(None, 'ALL')
    for num in data[0].split():
        typ, data = mail.fetch(num, '(RFC822)')
    typ, data = mail.search(None, 'ALL')
    ids = data[0]
    id_list = ids.split()

    
# Any Emails? 
# get most recent email id
    if id_list:
        latest_email_id = int( id_list[-1] )
        for i in range( latest_email_id, latest_email_id-1, -1):
            typ, data = mail.fetch( i, '(RFC822)')
        for response_part in data:
            if isinstance(response_part, tuple):
                msg = email.message_from_string(response_part[1])
        varSubject = msg['subject']
        varFrom = msg['from']
        varFrom = varFrom.replace('<','')
        varFrom = varFrom.replace('>','')

    #Remove used emails from mailbox
        typ, data = mail.search(None, 'ALL')
    for num in data[0].split():
        mail.store(num, '+FLAGS', '\\Deleted')
        mail.expunge()
        mail.close()
        mail.logout()

    return int(varSubject)

while True:
        print "Current temp"
        print read_temp()
        print "Target temp"
        print read_gmail()
        if (read_gmail() > read_temp()):#Compare varSubject to temp
            wiringpi.digitalWrite(0, 1) # sets port 0 to 1 (3.3V, on)
            print "HEATING ON\n"
        else:
            wiringpi.digitalWrite(0, 0) # sets port 0 to 0 (3.3V, off)
            print "HEATING OFF\n"
        time.sleep(5)
