import sys
import requests
from datetime import datetime, timedelta, timezone
from PyQt6.QtWidgets import QApplication, QMainWindow,QWidget, QLineEdit, QPushButton, QTextEdit,QVBoxLayout,QLabel,QMessageBox,QProgressBar
from PyQt6.QtGui import QIcon, QFont,QPixmap, QTextCursor, QTextBlockFormat, QPalette, QBrush, QLinearGradient, QColor
from PyQt6 import uic
from PyQt6.QtCore import Qt, QSize

api_key='a568959c7213ea219e40cc58ef9845c9'   #API Key to access weather info from openweathermap.org
waqi_key='046bfcb0bc571f1c4fb6f93fc02624362ffc1367' #API Key to access AQI info from aqicn.org

class WeatherApp(QWidget):
    def __init__(self):
        super().__init__()
        
        uic.loadUi(r"C:\Users\shand\Personal Projects\Weather\gui.ui",self)  #Loading custom Qt6 UI     
        self.setStyleSheet(""" 
            QWidget#Form {
                background:qlineargradient(spread:pad, x1:0.509, y1:0, x2:0.481, y2:0.982955, stop:0 rgba(0, 123, 221, 255), stop:1 rgba(183, 228, 255, 255));
                
            }
            QTextEdit{
            border: none;
            }
        """)  #Background colour wasn't showing up in python code so hardcoded it in my script

        self.setWindowTitle('Weather App')
        self.setWindowIcon(QIcon(r"C:\Users\shand\Personal Projects\Weather\Weather_Icon.png"))
        self.button.clicked.connect(self.provide_weather_info)
        
    def provide_weather_info(self):
        self.weather.clear() #Clearing previous search
        self.city.clear()
        
        self.input.setPlaceholderText("Enter city")
        inp=self.input.text()
   
        weather_data=requests.get(f"https://api.openweathermap.org/data/2.5/weather?q={inp}&units=metric&appid={api_key}",timeout=10) #getting Weather info
        # weather_data.raise_for_status()  # Trigger error for 4xx/5xx status codes
        
        aqi_data=requests.get(f"https://api.waqi.info/feed/{inp}/?token={waqi_key}") #getting AQI info
        # aqi_data.raise_for_status()
        
        if weather_data.status_code !=200 or aqi_data.status_code!=200: #Invalid Search
            try:
                error_message = response.json().get("message", "Unknown error")
            except Exception:
                error_message = "Unknown error"
            self.flag.clear()
            self.date.clear()
            self.icon_label.clear()
            self.geoloc.clear()
            self.add_info.clear()
            QMessageBox.critical(self, "API Error", f"Could not get weather: {error_message}")
        else:
            weather_data=weather_data.json()
            aqi_data=aqi_data.json()
            
            icon_code = weather_data['weather'][0]['icon']   # For showing weather image
            weather=weather_data['weather'][0]['main']  #Description of the weather
            temp=weather_data['main']['temp']       # Real Time Temperature
            feels_like=weather_data['main']['feels_like'] # Temperature perceived by humans
            description = weather_data['weather'][0]['description'].capitalize() 

            cursor = self.weather.textCursor()
            cursor.insertText(f"{weather} ({description})\nCurrent Temp: {temp}\xb0C \nMin: {weather_data['main']['temp_min']}\xb0C  Max:{weather_data['main']['temp_max']}\xb0C\n ")
            
            dt=datetime.fromtimestamp(weather_data['dt'])
            date=dt.strftime("%d/%m/%Y")    #Representing date in DD/MM/YYYY form
            self.date.setText(f"{date}")
            
            # Trying to fetch and show the icon
            try:        
                icon_url = f"http://openweathermap.org/img/wn/{icon_code}@2x.png"
                icon_data = requests.get(icon_url, timeout=10).content
                pixmap = QPixmap()
                if pixmap.loadFromData(icon_data):
                    pixmap.setDevicePixelRatio(self.devicePixelRatio()) # Setting proper DPI ratio
                    scaled_pixmap = pixmap.scaled(150, 150, 
                                                Qt.AspectRatioMode.KeepAspectRatio, 
                                                Qt.TransformationMode.SmoothTransformation)
                    self.icon_label.setPixmap(scaled_pixmap)
                else:
                    self.icon_label.clear()
            except Exception as e:
                print(f"Icon error: {e}")
                self.icon_label.clear()
            
            country=weather_data['sys']['country']      #Getting country code
            self.city.setAlignment(Qt.AlignmentFlag.AlignHCenter)
            self.city.setText(f"{inp.title()} ({country})")     
            
            #Displaying the flag of the country of the city
            try:
                response = requests.get(f"https://flagcdn.com/w320/{country.lower()}.png", timeout=10) 
                response.raise_for_status()

                pixmap = QPixmap()
                if pixmap.loadFromData(response.content):
                    pixmap.setDevicePixelRatio(self.devicePixelRatioF())
                    target_size = QSize(140,112)  
                    scaled_pixmap = pixmap.scaled(
                        target_size,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation
                    )
                    self.flag.setPixmap(scaled_pixmap)
                    self.flag.setFixedSize(target_size)  
                    self.flag.setAlignment(Qt.AlignmentFlag.AlignHCenter)
                else:
                    self.flag.clear()
            
            except requests.RequestException as e:
                print(f"Network error while fetching flag: {e}")
                self.flag.clear()
            except Exception as e:
                print(f"Unexpected error while setting flag: {e}")
                self.flag.clear()
            
            cursor = self.city.textCursor()
            block_format = QTextBlockFormat()
            block_format.setAlignment(Qt.AlignmentFlag.AlignHCenter)
            cursor.mergeBlockFormat(block_format)
            self.city.setTextCursor(cursor)
            
            self.pos=weather_data["coord"]
            [lon,lat]=[self.pos['lon'],self.pos['lat']]     #Latitude and Longitude of the City
            elev=requests.get(f"https://api.open-elevation.com/api/v1/lookup?locations={lat},{lon}").json()['results'][0]['elevation']  #Getting the elevation of the city
            self.geoloc.setText(f"Lon: {abs(self.pos['lon'])}\xb0{'E' if self.pos['lon']>0 else 'W'}\nLat: {abs(self.pos['lat'])}\xb0{'N' if self.pos['lat']>0 else 'S'}\nElev: {elev} m")
            
            humidity=weather_data['main']['humidity']
            pressure=weather_data['main']['pressure']
            wind_speed=weather_data['wind']['speed']

            try:
                aqi=aqi_data['data']['aqi']
            except TypeError:
                self.flag.clear()
                self.date.clear()
                self.icon_label.clear()
                self.geoloc.clear()
                self.add_info.clear()
                self.city.clear()
                self.weather.clear()
                QMessageBox.critical(self,"Invalid Response","Invalid City/ No Info available")
                return
                
            sr_raw=weather_data['sys']['sunrise']   #Time provided as UNIX Timestamp
            ss_raw=weather_data['sys']['sunset']
            tz_offset=weather_data['timezone']
            tz = timezone(timedelta(seconds=tz_offset))
            sunrise = datetime.fromtimestamp(sr_raw, tz).strftime("%I:%M %p").strip()
            sunset = datetime.fromtimestamp(ss_raw, tz).strftime("%I:%M %p").strip()
            self.add_info.setText(f"___________________________________________________________________\nHumidity: {humidity}%          Pressure: {pressure} hPa{" "*(16-len(str(pressure)))}Sunrise: {sunrise}\nAQI: {aqi}{" "*(23-len(str(aqi)))}Wind-Speed:{wind_speed}m/s{" "*(13-len(str(wind_speed)))}Sunset: {sunset}")

app=QApplication(sys.argv)
window=WeatherApp()
window.show()
app.exec()
