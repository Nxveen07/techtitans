# TruthTrace AI - Intelligence Platform

TruthTrace AI is a powerful, full-stack misinformation detection and mitigation platform designed to monitor truth in real-time. This project leverages the Groq API for high-velocity AI analysis and provides a modern, interactive dashboard for enterprise monitoring.

## 🚀 Key Features

- **AI Misinformation Detection**: High-confidence analysis using the Groq API (Llama 3.3).
- **Origin Tracking**: Visualize the spread of content across digital platforms.
- **Auto-Mitigation**: Automated flagging and DNS blacklisting of confirmed fake news.
- **Enterprise Dashboard**: A premium, real-time command center for intelligence oversight.

## 📂 Project Structure

```text
TruthTrace_Project/
├── frontend/               <-- Reorganized frontend (HTML/CSS/JS)
├── backend/                <-- FastAPI Backend (Python)
├── vercel.json             <-- Deployment Configuration
└── README.md               <-- Documentation
```

## 🛠️ Getting Started

### 1. Prerequisites
- **Python 3.10+** (for the backend)
- **Node.js** (optional, for advanced Vercel commands)
- **Groq API Key**: Obtain one at [console.groq.com](https://console.groq.com)

### 2. Setup
1. Clone this repository (or copy the files).
2. Navigate to the `backend` folder and create a `.env` based on `.env.example`.
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### 3. Running the Project
Use the included startup script at the root:
```powershell
./run_truthtrace.bat
```

## 🌐 Deployment

### Frontend (Vercel)
This project is configured for seamless deployment on Vercel. 
- **Root Directory**: `.`
- **Build Command**: `None`
- **Output Directory**: `frontend` (Handles through `vercel.json`)

### Backend
The backend can be deployed on any Python-capable host (Render, Railway, or AWS). Ensure you set your `GROQ_API_KEY` in the environment variables.

---
Created by **Tech Titans Team**.
