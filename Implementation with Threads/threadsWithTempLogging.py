import network
import socket
import machine
import time
import _thread
import requests

# Pin where TMP36 is connected
analog_sensor = machine.ADC(26)

sensor_lock=_thread.allocate_lock()

# Function to read temperature from TMP36 sensor
def read_temperature():
    sensor_lock.acquire()
    global maximumTemp
    reading = analog_sensor.read_u16()
    analog_voltage= (3.3/65535)*reading
    temperature=(100*analog_voltage)-50
    temperature=round(temperature, 2)
    if temperature>maximumTemp:
        maximumTemp=temperature
    sensor_lock.release()
    return temperature

#Initializing an array to save the temperatures for the current day.
#We measure temperature every 5min so we need 12*24=288 cells
currentDayLog=[-300]*289
daily_log_counter=0
maximumTemp = -300
#Initializing a list of the average temperature for the last 10 days
#List contains pairs: (AverageTemp, Day)
lastDaysLog=list()
    
currentDay_lock = _thread.allocate_lock()

def averageDailyTemp():
    global currentDayLog, daily_log_counter
    if daily_log_counter == 0:
        return read_temperature()
    sum_temp = 0
    with currentDay_lock:
        for temp in currentDayLog:
            if temp == -300:
                break
            sum_temp += temp
    return round(sum_temp / daily_log_counter, 2)


def temperature_logging():
    global currentDayLog, daily_log_counter, lastDaysLog, maximumTemp
    prevMeasurement=rtc.datetime()
    prevMeasurementDay=[prevMeasurement[2], prevMeasurement[1], prevMeasurement[0]]
    while True:
        try: 
            #Checking if the day has changed. If the date has changed then we flush the array with temperatures stored from previous day
            #Also if we have data for more than 10 days then we pop the oldest data
            check_date=rtc.datetime()
            if prevMeasurementDay[0]!=check_date[2]:
                with currentDay_lock:
                    currentDayLog=[-300]*289
                    currentDayLog[0]=read_temperature()
                    daily_log_counter=1
                    maximumTemp=-300
                lastDaysLog.append((str(prevMeasurementDay[0])+ "-" + str(prevMeasurementDay[1])+ "-" + str(prevMeasurementDay[2]), averageDailyTemp()))
                if len(lastDaysLog)==11:
                    lastDaysLog.pop(0)
                prevMeasurementDay=[check_date[2], check_date[1], check_date[0]]
            else:
                with currentDay_lock:
                    currentDayLog[daily_log_counter]=read_temperature()
                daily_log_counter+=1
            time.sleep(300)
        except Exception as e:
            print("Error in temperature_logging:", e)

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

addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
s = socket.socket()
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(addr)
s.listen(1)

_thread.start_new_thread(temperature_logging, ())
        
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
            
            response = html % (Day, str(currentTemp), str(maximumTemp), str(averageDaily), chart_url, str(daily_log_counter))
        
        else:
            response = html % (Day, str(currentTemp), str(maximumTemp), str(averageDaily), "", str(daily_log_counter))

        cl.send('HTTP/1.0 200 OK\r\nContent-type: text/html\r\n\r\n')
        cl.send(response)
        cl.close()
    
    except Exception as e:
            print("Error in main loop:", e)




