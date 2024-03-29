# MicroPython Temperature Server

This is a MicroPython project that creates a local network server for temperature logging. It utilizes the TMP36 analog sensor for temperature measurement.

## Project Overview

This project offers four implementations, each focusing on implementing different methods for temperature logging. The logging function is designed to be invoked either by a timer interrupt or by utilizing the dual cores available on the Raspberry Pi Pico W.
One core is dedicated to running the server, while the other continuously serves the website. Periodic Temperature logging runs once every 5 minutes.
Also there are imlementations that store the periodic temperature measurents in a python array and others that stores only the sum of the temperatures that are measured periodically today and the number of them in order to calculate the Average Daily Temperature. 

## Website Features

The website generated by the server provides the following information:

* Current Temperatures: The site automatically refreshes every minute to display the latest temperature readings.

* Average Temperature for the Current Day

* Maximum Temperature Measured Today

* Historical Data: If the MicroPython server has been running for over a day, a diagram depicting the average temperature for the past 10 days will be displayed.

* Auxiliary Parameter: Additionally, the site displays the number of temperature measurements taken automatically on the current day.

## Website Preview

![Screenshot from 2024-03-29 12-25-00](https://github.com/ManosXen/MicroPython-Temperature-Server/assets/73884458/79f93818-0dbe-42a8-9649-ffc15e358595)

## How to run
Some short instructions in order to run the code from the repository:
* Change the ssid and password parameters to the name and password of your local network, so that the microcontroller can connect to your local network
* Microcontrollers usually dont have a battery with their RTC in order to store time when they are not connected to a power supply/battery/computer. In order to set the time correctly we use an API to get the time. Set the city that corresponds with your time zone. Also set your API Key from API Ninja. You can get an API Key from here
https://api-ninjas.com/
* The implementation that use the ```py _threads``` work only for microcontrollers that have more than 2 CPU cores. 

