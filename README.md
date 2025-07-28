# AIronman Coaching App 🏊‍♂️🚴‍♂️🏃‍♂️

> **Your AI-powered triathlon training companion**

## 🎯 Functional Overview - What Can You Do?

### 🚀 **Core Features**

**📊 Health & Recovery Analysis**
- **Sleep Quality Tracking**: Monitor your sleep scores over time with trend analysis
- **Heart Rate Variability (HRV)**: Track your weekly HRV averages for recovery insights
- **Resting Heart Rate (RHR)**: Monitor your RHR trends as a recovery indicator
- **Week Navigation**: Navigate through different weeks to analyze historical trends
- **Visual Analytics**: Beautiful line charts with date labels and value indicators
- **Recovery Assessment**: Get recovery status and readiness recommendations

**💪 Workout Management**
- **Workout History**: View all your Garmin workouts with detailed information
- **Week Navigation**: Browse workouts by week with intuitive navigation
- **Workout Details**: Drill down into individual workout data and metrics
- **Training Stress Score (TSS)**: Track your training load and intensity

**👤 Athlete Profile Management**
- **Zone Configuration**: Set up training zones for all disciplines (swim, bike, run)
- **Heart Rate Zones**: Configure your heart rate training zones
- **Power Zones**: Set up bike and run power zones (FTP, LTP, Critical Power)
- **Pace Zones**: Configure run pace zones for structured training
- **Test Date Tracking**: Record when you performed your fitness tests

**🔄 Data Synchronization**
- **Garmin Connect Integration**: Automatic sync of workouts and health data
- **42-Day Historical Data**: Pull comprehensive historical data for analysis
- **Real-time Updates**: Keep your data current with background sync

### 🌟 **Why It's Cool**

**🎯 Training Intelligence**
- **Data-Driven Insights**: Make informed training decisions based on your actual data
- **Recovery Monitoring**: Track your readiness to train with HRV and sleep analysis
- **Zone-Based Training**: Ensure you're training at the right intensities
- **Historical Analysis**: See your progress over time with week-by-week navigation

**🔄 Seamless Integration**
- **Garmin Ecosystem**: Works with your existing Garmin devices and data
- **No Manual Entry**: Automatic data sync eliminates manual tracking
- **Comprehensive Coverage**: Tracks all aspects of triathlon training

**📱 Modern Interface**
- **Responsive Design**: Works on desktop and mobile devices
- **Intuitive Navigation**: Easy-to-use interface with clear data visualization
- **Real-time Updates**: See your data update as you train

### 🔮 **What's Next on the Horizon**

**📈 Performance Management Chart (PMC)**
- Chronic Training Load (CTL) calculation and visualization
- Acute Training Load (ATL) tracking
- Training Stress Balance (TSB) for readiness assessment
- Performance trend analysis over time

**🤖 AI-Powered Insights**
- Training recommendations based on your data
- Recovery optimization suggestions
- Race preparation guidance
- Training load balancing

**📋 Training Planning**
- Next week training suggestions
- Macro cycle planning tools
- Workout recommendations
- Training plan templates

**👥 Multi-Athlete Support**
- Coach-athlete relationship management
- Team training insights
- Comparative performance analysis

---

## 🔧 Technical Overview - How It Works

### 🏗️ **Architecture**

**Frontend (React)**
- Modern React application with hooks and functional components
- Responsive design with CSS Grid and Flexbox
- Real-time data visualization with SVG charts
- State management with React hooks

**Backend (FastAPI)**
- Python FastAPI for high-performance API development
- Pydantic models for data validation and serialization
- PostgreSQL database for data persistence
- Docker containerization for easy deployment

**Database (PostgreSQL)**
- Relational database with JSONB support for Garmin data
- Optimized schema for health and workout data
- Efficient querying for time-series data

**Data Pipeline**
- Garmin Connect API integration for data sync
- Background task processing for data updates
- Error handling and retry mechanisms

### 🛠️ **Tech Stack**

**Frontend**
- React 18+ with functional components
- CSS3 with modern layout techniques
- SVG for data visualization
- Fetch API for backend communication

**Backend**
- FastAPI (Python web framework)
- Pydantic (data validation)
- SQLAlchemy (ORM)
- psycopg2 (PostgreSQL adapter)

**Infrastructure**
- Docker & Docker Compose
- PostgreSQL database
- Nginx (frontend serving)
- Gunicorn (backend serving)

**Data Sources**
- Garmin Connect API
- Garmin Connect SDK
- Custom data processing scripts

### 📁 **Project Structure**

```
aironman-1/
├── api/                    # FastAPI backend
│   └── main.py            # Main API endpoints
├── frontend/              # React frontend
│   ├── src/
│   │   ├── App.js         # Main React component
│   │   └── App.css        # Styles
│   └── public/
├── services/              # Business logic
│   ├── sync.py           # Garmin data sync
│   ├── preprocess.py     # Data processing
│   └── garmin_auth.py    # Authentication
├── utils/                 # Shared utilities
│   ├── database.py       # Database utilities
│   ├── config.py         # Configuration
│   └── models.py         # Data models
├── database/             # Database setup
│   └── init/            # Schema initialization
├── scripts/              # Utility scripts
│   └── sync_42_days_container.py  # Data sync script
└── docker-compose.yml    # Container orchestration
```

### 🚀 **Local Development Setup**

**Prerequisites**
- Docker and Docker Compose
- Git

**Quick Start**
```bash
# Clone the repository
git clone <repository-url>
cd aironman-1

# Set up environment
cp .env.example .env
# Edit .env with your Garmin credentials

# Start the application
docker compose up -d

# Access the application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
```

**Environment Configuration**
```bash
# Required environment variables in .env
GARMIN_EMAIL=your_email@example.com
GARMIN_PASSWORD=your_password
```

**Data Population**
```bash
# Sync 42 days of historical data
./sync_42_days.sh
```

### 🔄 **Development Workflow**

**Frontend Development**
```bash
# Rebuild frontend after changes
docker compose build frontend
docker compose up -d frontend
```

**Backend Development**
```bash
# Restart backend after changes
docker compose restart backend
```

**Database Access**
```bash
# Connect to database
docker exec -it aironman-1-db-1 psql -U postgres -d aironman
```

### 📊 **API Endpoints**

**Health & Recovery**
- `GET /api/health/trends` - Get health trends data
- `GET /api/health/analysis` - Comprehensive health analysis
- `GET /api/health/recovery-status` - Recovery status assessment
- `GET /api/health/readiness` - Training readiness recommendation

**Workouts**
- `GET /api/workouts` - List workouts with date filtering
- `GET /api/workouts/{id}` - Get detailed workout information

**Profile Management**
- `GET /api/profile` - Get athlete profile and zones
- `PUT /api/profile` - Update athlete profile

**Data Sync**
- `POST /sync` - Trigger data synchronization

### 🧪 **Testing**

**API Testing**
```bash
# Test health analysis endpoint
curl "http://localhost:8000/api/health/analysis?athlete_id=Jan&days=30"
```

**Frontend Testing**
- Open http://localhost:3000
- Navigate to "Health & Recovery" section
- Test week navigation and data visualization

### 📈 **Performance & Scalability**

**Current Performance**
- API response times: < 200ms for typical queries
- Frontend load time: < 2 seconds
- Database queries: Optimized with proper indexing

**Scalability Considerations**
- Containerized architecture for easy scaling
- Database connection pooling
- Background task processing for data sync
- Caching strategies for frequently accessed data

### 🔒 **Security**

**Data Protection**
- Environment variable configuration
- Database connection security
- API authentication (planned)
- HTTPS support (production)

**Privacy**
- Local data storage only
- No external data sharing
- User-controlled data sync

---

## 🤝 **Contributing**

This is a personal project focused on triathlon training optimization. The codebase is designed to be modular and extensible for future enhancements.

## 📄 **License**

Personal project - not licensed for commercial use.