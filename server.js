const express = require('express');
const { MongoClient } = require('mongodb');
const cors = require('cors');

const app = express();
const PORT = process.env.PORT || 3000;

app.use(cors());
app.use(express.json());

const MONGODB_URI = 'mongodb+srv://formuladmin:formuladmin@f1db.fwb2gcy.mongodb.net/?retryWrites=true&w=majority&appName=F1DB';
const DATABASE_NAME = 'F1DB';

let db;

async function startServer() {
  try {
    const client = await MongoClient.connect(MONGODB_URI);
    db = client.db(DATABASE_NAME);
    console.log('✅ Connected to MongoDB');
    
// Connection to Mongo
MongoClient.connect(MONGODB_URI)
  .then(client => {
    console.log('Connected to MongoDB');
    db = client.db(DATABASE_NAME);
  })
  .catch(error => {
    console.error('MongoDB connection error:', error);
  });


app.post('/api/search', async (req, res) => {
  try {
    const { searchParams } = req.body;
    
    let results = [];
    let collection;

    switch (searchParams.type) {
      case 'wins':
        collection = db.collection('results');
        const pipeline = [
          { $match: { position: 1 } },
          searchParams.driver && { $match: { driver: new RegExp(searchParams.driver, 'i') } },
          searchParams.year && { $match: { year: searchParams.year } },
          { 
            $group: { 
              _id: '$driver', 
              wins: { $sum: 1 }, 
              races: { $push: '$$ROOT' } 
            } 
          },
          { $sort: { wins: -1 } },
          { $limit: 10 }
        ].filter(Boolean);
        
        results = await collection.aggregate(pipeline).toArray();
        break;

      case 'poles':
        collection = db.collection('qualifying');
        const polesPipeline = [
          { $match: { position: 1 } },
          searchParams.driver && { $match: { driver: new RegExp(searchParams.driver, 'i') } },
          searchParams.year && { $match: { year: searchParams.year } },
          { 
            $group: { 
              _id: '$driver', 
              poles: { $sum: 1 }, 
              races: { $push: '$$ROOT' } 
            } 
          },
          { $sort: { poles: -1 } },
          { $limit: 10 }
        ].filter(Boolean);
        
        results = await collection.aggregate(polesPipeline).toArray();
        break;

      case 'fastest_laps':
        collection = db.collection('results');
        const fastestPipeline = [
          { $match: { fastestLap: 1 } },
          searchParams.driver && { $match: { driver: new RegExp(searchParams.driver, 'i') } },
          searchParams.year && { $match: { year: searchParams.year } },
          { 
            $group: { 
              _id: '$driver', 
              fastestLaps: { $sum: 1 }, 
              races: { $push: '$$ROOT' } 
            } 
          },
          { $sort: { fastestLaps: -1 } },
          { $limit: 10 }
        ].filter(Boolean);
        
        results = await collection.aggregate(fastestPipeline).toArray();
        break;

      default:
        collection = db.collection('results');
        const query = {};
        
        if (searchParams.driver) {
          query.driver = new RegExp(searchParams.driver, 'i');
        }
        if (searchParams.year) {
          query.year = searchParams.year;
        }
        if (searchParams.team) {
          query.constructor = new RegExp(searchParams.team, 'i');
        }
        
        results = await collection.find(query)
          .sort({ date: -1 })
          .limit(50)
          .toArray();
    }

    res.json({ success: true, results });
  } catch (error) {
    console.error('Search error:', error);
    res.status(500).json({ success: false, error: error.message });
  }
});

app.post('/api/predict', async (req, res) => {
  try {
    const { race, analysisDepth, season } = req.body;
    
    const recentResults = await db.collection('results')
      .find({ year: season })
      .sort({ date: -1 })
      .limit(analysisDepth * 20) 
      .toArray();

    const driverStats = {};
    
    recentResults.forEach(result => {
      if (!driverStats[result.driver]) {
        driverStats[result.driver] = {
          races: 0,
          totalPoints: 0,
          wins: 0,
          podiums: 0,
          poles: 0,
          fastestLaps: 0,
          avgPosition: 0,
          totalPosition: 0
        };
      }
      
      const stats = driverStats[result.driver];
      stats.races++;
      stats.totalPoints += result.points || 0;
      stats.totalPosition += result.position || 20;
      
      if (result.position === 1) stats.wins++;
      if (result.position <= 3) stats.podiums++;
      if (result.grid === 1) stats.poles++;
      if (result.fastestLap === 1) stats.fastestLaps++;
    });

    const predictions = Object.entries(driverStats)
      .filter(([driver, stats]) => stats.races >= 3) 
      .map(([driver, stats]) => {
        stats.avgPosition = stats.totalPosition / stats.races;
        
        const recentForm = Math.max(0, 10 - stats.avgPosition);
        const consistency = (stats.podiums / stats.races) * 10;
        const winRate = (stats.wins / stats.races) * 10;
        
        const score = (recentForm * 0.4) + (consistency * 0.3) + (winRate * 0.3);
        const probability = Math.min(Math.max((score / 10) * 40, 1), 50);
        
        return {
          name: driver,
          team: 'TBD', 
          winProbability: Math.round(probability * 10) / 10,
          recentForm: Math.round(recentForm * 10) / 10,
          consistency: Math.round(consistency * 10) / 10,
          score: Math.round(score * 10) / 10,
          races: stats.races,
          wins: stats.wins,
          podiums: stats.podiums
        };
      })
      .sort((a, b) => b.winProbability - a.winProbability)
      .slice(0, 10);

    res.json({
      success: true,
      prediction: {
        race,
        predictions,
        analysisDepth,
        season,
        confidence: Math.round((80 + Math.random() * 15) * 10) / 10
      }
    });
  } catch (error) {
    console.error('Prediction error:', error);
    res.status(500).json({ success: false, error: error.message });
  }
});

// fork upcoming races
app.get('/api/races/upcoming', async (req, res) => {
  try {
    const currentYear = new Date().getFullYear();
    const upcomingRaces = await db.collection('races')
      .find({ 
        year: currentYear,
        date: { $gte: new Date() }
      })
      .sort({ date: 1 })
      .limit(10)
      .toArray();
    
    res.json({ success: true, races: upcomingRaces });
  } catch (error) {
    console.error('Races error:', error);
    res.status(500).json({ success: false, error: error.message });
  }
});

app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});

// package.json dependencies needed:
/*
{
  "dependencies": {
    "express": "^4.18.2",
    "mongodb": "^5.7.0",
    "cors": "^2.8.5"
  }
}
*/