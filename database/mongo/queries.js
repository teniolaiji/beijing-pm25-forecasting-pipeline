// MongoDB queries for the Beijing PM2.5 data
// run them one by one in the mongosh shell inside Compass
// database: beijing_pm25, collection: readings

use("beijing_pm25");

// Query 1: average PM2.5 for each month of 2013
// $match keeps 2013 and drops the nulls, $group makes one row per month
// Result: 12 rows, highest in January(193.3), lowest in August(61.9)
db.readings.aggregate([
  { $match: {
      datetime: { $gte: ISODate("2013-01-01"), $lt: ISODate("2014-01-01") },
      pm25: { $ne: null }
  } },
  { $group: { _id: { $month: "$datetime" }, avg_pm25: { $avg: "$pm25" } } },
  { $project: { _id: 0, month: "$_id", avg_pm25: { $round: ["$avg_pm25", 1] } } },
  { $sort: { month: 1 } }
]);

// Query 2: the hour with the highest PM2.5 in winter 2013(Jan & Feb)
// Result: 886 on 2013-01-12 at 20:00
db.readings.find(
  {
    datetime: { $gte: ISODate("2013-01-01"), $lte: ISODate("2013-02-28T23:59:59Z") },
    pm25: { $ne: null }
  },
  { _id: 0, datetime: 1, pm25: 1 }
).sort({ pm25: -1 }).limit(1);

// Query 3: how many readings there are for each wind direction
// the wind direction is inside "weather" so the path is weather.wind_dir
// Result: SE 15290, NW 14150, cv 9387, NE 4997
db.readings.aggregate([
  { $group: { _id: "$weather.wind_dir", readings: { $sum: 1 } } },
  { $project: { _id: 0, wind_direction: "$_id", readings: 1 } },
  { $sort: { readings: -1 } }
]);

// Query 4: the latest record(the latest record endpoint will need this)
// Result: 2014-12-31 23:00, pm25 12, wind NW
db.readings.find({}, { _id: 0 }).sort({ datetime: -1 }).limit(1);

// Query 5: Jan. 2013 hours where PM2.5 was above 300
// run the count first then the list
// Result: 201 hours
db.readings.countDocuments({
  datetime: { $gte: ISODate("2013-01-01"), $lt: ISODate("2013-02-01") },
  pm25: { $gt: 300 }
});

// Result: the first one is 2013-01-06 20:00 with pm25 335
db.readings.find(
  {
    datetime: { $gte: ISODate("2013-01-01"), $lt: ISODate("2013-02-01") },
    pm25: { $gt: 300 }
  },
  { _id: 0, datetime: 1, pm25: 1, "weather.wind_dir": 1 }
).sort({ datetime: 1 }).limit(5);