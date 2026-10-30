USE beijing_pm25;
 
-- Query 1: average PM2.5 for each month of 2013
-- (join the two tables, group by month, ignore the NULL values)
-- Result: 12 rows highest in January(193.3), lowest in August(61.9)
SELECT MONTH(w.reading_time) AS month,
       ROUND(AVG(p.pm25), 1) AS avg_pm25
FROM weather_readings w
JOIN pm25_readings p ON p.weather_id = w.weather_id
WHERE YEAR(w.reading_time) = 2013
GROUP BY MONTH(w.reading_time)
ORDER BY month;
 
-- Query 2: the hour with the highest PM2.5 in winter 2013(Jan & Feb)
-- Result: 886 on 2013-01-12 at 20:00
SELECT w.reading_time, p.pm25
FROM weather_readings w
JOIN pm25_readings p ON p.weather_id = w.weather_id
WHERE w.reading_time BETWEEN '2013-01-01 00:00:00' AND '2013-02-28 23:59:59'
ORDER BY p.pm25 DESC
LIMIT 1;
 
-- Query 3: how many readings there are for each wind direction
-- Result: SE 15290, NW 14150, cv 9387, NE 4997 (total 43,824)
SELECT d.code AS wind_direction,
       COUNT(*) AS readings
FROM weather_readings w
JOIN wind_directions d ON d.wind_dir_id = w.wind_dir_id
GROUP BY d.code
ORDER BY readings DESC;
 
-- Query 4: the latest record(the latest record endpoint will need this)
-- all three tables are joined to get the full row
-- Result: 2014-12-31 23:00, pm25 12, wind NW
SELECT w.reading_time, p.pm25, w.temperature, w.pressure,
       d.code AS wind_direction, w.wind_speed
FROM weather_readings w
JOIN pm25_readings p ON p.weather_id = w.weather_id
LEFT JOIN wind_directions d ON d.wind_dir_id = w.wind_dir_id
ORDER BY w.reading_time DESC
LIMIT 1;
 
-- Query 5: Jan 2013 hours where PM2.5 was above 300 
-- first the count
-- Result: 201 hours
SELECT COUNT(*) AS hazardous_hours
FROM weather_readings w
JOIN pm25_readings p ON p.weather_id = w.weather_id
WHERE w.reading_time >= '2013-01-01' AND w.reading_time < '2013-02-01'
  AND p.pm25 > 300;
 
-- then the first 5 of those hours
-- Result: the first one is 2013-01-06 20:00 with pm25 335
SELECT w.reading_time, p.pm25, d.code AS wind_direction
FROM weather_readings w
JOIN pm25_readings p ON p.weather_id = w.weather_id
LEFT JOIN wind_directions d ON d.wind_dir_id = w.wind_dir_id
WHERE w.reading_time >= '2013-01-01' AND w.reading_time < '2013-02-01'
  AND p.pm25 > 300
ORDER BY w.reading_time
LIMIT 5;