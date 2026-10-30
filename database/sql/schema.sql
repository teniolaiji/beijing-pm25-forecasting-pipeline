CREATE DATABASE IF NOT EXISTS beijing_pm25;
USE beijing_pm25;

CREATE TABLE wind_directions (
    wind_dir_id INT AUTO_INCREMENT PRIMARY KEY,
    code        VARCHAR(4) NOT NULL UNIQUE
);

CREATE TABLE weather_readings (
    weather_id   INT AUTO_INCREMENT PRIMARY KEY,
    reading_time DATETIME NOT NULL UNIQUE,
    dew_point    FLOAT,
    temperature  FLOAT,
    pressure     FLOAT,
    wind_dir_id  INT,
    wind_speed   FLOAT,
    hours_snow   INT,
    hours_rain   INT,
    FOREIGN KEY (wind_dir_id) REFERENCES wind_directions(wind_dir_id)
);

CREATE TABLE pm25_readings (
    pm25_id    INT AUTO_INCREMENT PRIMARY KEY,
    weather_id INT NOT NULL UNIQUE,
    pm25       INT NULL,
    FOREIGN KEY (weather_id) REFERENCES weather_readings(weather_id)
);