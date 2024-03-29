import network
import socket
import machine
import time
import requests
from machine import Timer

# Pin where TMP36 is connected
analog_sensor = machine.ADC(26)

# Function to read temperature from TMP36 sensor
def read_temperature():
    global maximumTemp
    reading = analog_sensor.read_u16()
    analog_voltage= (3.3/65535)*reading
    temperature=(100*analog_voltage)-50
    temperature=round(temperature, 2)
    if temperature>maximumTemp:
        maximumTemp=temperature
    return temperature

#Instead of logging the temperatures to calculate the avg daily temperature we use two variables:
# 1)TempSum that is the sum of measuredTemperatures
# 2)TempNum that is the number of the measured temperatures
#The optimization comes mainly that we dont have to run through the whole array, text file etc but we only
#do a simple division. Minor improvements comes from the fact that we dont have to flush the measured
#temperatures at the start of every day and "storing" is faster.

tempCounter=0
tempSum=0
maximumTemp = -300

#Initializing a list of the average temperature for the last 10 days
#List contains pairs: (AverageTemp, Day)
lastDaysLog=list()
    
def averageDailyTemp():
    global tempCounter, tempSum
    if tempCounter == 0:
        return read_temperature()
    else:
            return round(tempSum / tempCounter, 2)

def temperature_logging(dummy):
    global tempSum, tempCounter, maximumTemp
    prevMeasurement=rtc.datetime()
    prevMeasurementDay=[prevMeasurement[2], prevMeasurement[1], prevMeasurement[0]]
    try: 
        check_date=rtc.datetime()
        #print(type(currentDay[0]), type(check_date[2]), sep=" ")
        if prevMeasurementDay[0]!=check_date[2]:
            tempCounter=1
            maximumTemp=-300
            tempSum=read_temperature()
            lastDaysLog.append((str(prevMeasurementDay[0])+ "-" + str(prevMeasurementDay[1])+ "-" + str(prevMeasurementDay[2]), averageDailyTemp()))
            if len(lastDaysLog)==11:
                lastDaysLog.pop(0)
            prevMeasurementDay=[check_date[2], check_date[1], check_date[0]]
        else:
            tempSum+=read_temperature()
            tempCounter+=1
    except Exception as e:
        print("Error in temperature_logging:", e)

periodicTimer=Timer()
periodicTimer.init(period=300000, mode=Timer.PERIODIC, callback=temperature_logging)

html = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>Pico W Temperature Server</title>
                <meta http-equiv="refresh" content="60"/>
            </head>
            <body>
                <p>Latest Page Refresh: %s</p>
                <hr>
                <h1>Raspberry Pi Pico W Web Server for Temperature Measurement</h1>
                <p>Current Temperature: <span id="temperature">%s</span> &deg;C</p>
                <p>Maximum Temperature Measured Today: <span id="temperature">%s</span> &deg;C</p>
                <p>Average Temperature Today: <span id="temperature">%s</span> &deg;C</p>
                <img src="%s">
                <p>Temperatures Taken: %s</p>
            </body>
            </html>
            """
    
ssid = 'your_ssid'
password = 'your_password'

sta_if = network.WLAN(network.STA_IF)

sta_if.active(True)
sta_if.config(pm = 0xa11140) # Disable power-saving for WiFi 
sta_if.connect(ssid, password)

max_wait = 10
while max_wait > 0:
    if sta_if.status() < 0 or sta_if.status() >= 3:
        break
    max_wait -= 1
    print('waiting for connection...')
    time.sleep(1)

if sta_if.isconnected():
    print("Connected")
else:
    print("Not Connected")

status = sta_if.ifconfig()
print('IP Address:', status[0])

api_url = "https://api.api-ninjas.com/v1/worldtime?city=Athens"
api_response = requests.get(api_url, headers={'X-Api-Key': 'your_api_key'})

api_response=api_response.json()

days_mapping = {
        'Monday': 0,
        'Tuesday': 1,
        'Wednesday': 2,
        'Thursday': 3,
        'Friday': 4,
        'Saturday': 5,
        'Sunday': 6
    }


print(api_response)
year = api_response['year']
month = api_response['month']
day = api_response['day']
hour = api_response['hour']
minutes = api_response['minute']
seconds = api_response['second']
weekDay=days_mapping[api_response['day_of_week']]

currentDay=[int(day), int(month), int(year)]

rtc = machine.RTC()
rtc.datetime((int(year), int(month), int(day), weekDay, int(hour), int(minutes), int(seconds), 0))

temperature_logging(0)

addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
s = socket.socket()
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(addr)
s.listen(1)
        
while True:
    try:
        cl, addr = s.accept()
        print('client connected from', addr)
        request = cl.recv(1024)
        
        currentDayTime =rtc.datetime()
        currentTemp = read_temperature()
        
        currentDay=[currentDayTime[2], currentDayTime[1], currentDayTime[0]]
        
        Day = str(currentDayTime[2]) + "-" + str(currentDayTime[1]) + "-" + str(currentDayTime[0]) + " " + str(currentDayTime[4]) + ":" + str(currentDayTime[5]) + ":" + str(currentDayTime[6])
        
        averageDaily = averageDailyTemp()
        
        if len(lastDaysLog)!=0:
            labels = [day[0] for day in lastDaysLog]
            data = [temp[1] for temp in lastDaysLog]
            
            chart_data = "{type:'line',data:{labels:['" + "','".join(labels) + "'],datasets:[{label:'Temperature',data:[" + ",".join(map(str, data)) + "],fill:false}]},options:{title:{display:true,text:'Average Daily Temperature for the Last 10 Days'}}}"
            
            chart_url = "https://quickchart.io/chart?c=" + chart_data
            
            response = html % (Day, str(currentTemp), str(maximumTemp), str(averageDaily), chart_url, str(tempCounter))
        
        else:
            response = html % (Day, str(currentTemp), str(maximumTemp), str(averageDaily), "", str(tempCounter))

        cl.send('HTTP/1.0 200 OK\r\nContent-type: text/html\r\n\r\n')
        cl.send(response)
        cl.close()
    
    except Exception as e:
            print("Error in main loop:", e)



