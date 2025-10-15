# Video Call Platform - Complete Project

This repository contains both the frontend and backend for the video call platform.

## 📁 Project Structure

```
├── video_call_platform/     # Frontend (React + Vite)
│   ├── src/
│   │   ├── components/      # React components
│   │   └── ...
│   └── package.json
├── project-onevoice/        # Backend (FastAPI + Python)
│   ├── app/
│   │   ├── routers/         # API endpoints
│   │   ├── models.py        # Database models
│   │   └── ...
│   └── requirements.txt
├── mediasoup-server/        # Media Server (Node.js)
│   └── server.js
└── README.md
```

## 🚀 Quick Start

### Backend Setup
```bash
cd project-onevoice
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

### Frontend Setup
```bash
cd video_call_platform
npm install
npm run dev
```

### Media Server Setup
```bash
cd mediasoup-server
npm install
npm start
```

## 🔧 Development

- **Backend API**: http://localhost:8000
- **Frontend**: http://localhost:5173
- **Media Server**: http://localhost:8083

## 📝 Features

- ✅ User Authentication (Signup/Login)
- ✅ Instant Meeting Creation
- ✅ Real-time Video Calls
- ✅ Screen Sharing
- ✅ Chat System
- ✅ Recording
- ✅ Multi-user Support

## 🤝 For Frontend Developers

The frontend is located in `video_call_platform/` and is ready to use with the backend API.
