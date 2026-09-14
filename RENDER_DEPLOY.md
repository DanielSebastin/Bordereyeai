# 🚀 Hosting BorderEye Surveillance Suite on Render

This guide provides instructions to deploy both the **FastAPI AI Backend** and the **Next.js Government UI Frontend** on **[Render.com](https://render.com/)**.

---

## ⚡ Method 1: Automatic Blueprint Deployment (Recommended)

Because the repository includes ender.yaml, Render can deploy both services together with zero manual configuration:

1. Log in to your account on **[dashboard.render.com](https://dashboard.render.com/)**.
2. Click the **\"New +\"** button in the top navigation bar and select **\"Blueprint\"**.
3. Connect your GitHub repository: https://github.com/praveen21-tech/sih_border_survelliance.git.
4. Render will automatically detect ender.yaml and configure:
   - **ordereye-backend** (Python 3.11 / FastAPI)
   - **ordereye-frontend** (Node.js 20 / Next.js)
5. Under environment variables, enter your optional API keys:
   - GROQ_API_KEY: Your Groq Cloud API key (for NL Query Engine).
   - OPENAI_API_KEY: (Optional) If using OpenAI fallback.
6. Click **\"Apply\"** to start the build and deployment.

---

## 🛠️ Method 2: Manual Service Deployment

If you prefer to configure the services individually in the Render dashboard:

### 1. Deploy the Backend Web Service
1. In Render Dashboard, click **New +** → **Web Service**.
2. Select your repository praveen21-tech/sih_border_survelliance.
3. Fill in the following details:
   - **Name:** ordereye-backend
   - **Region:** Any (e.g., *Singapore* or *Oregon*)
   - **Branch:** main
   - **Root Directory:** *(leave blank / repository root)*
   - **Runtime:** Python 3
   - **Build Command:** pip install --upgrade pip && pip install -r requirements.txt
   - **Start Command:** python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 
   - **Plan:** Free
4. Under **Environment Variables**, add:
   - PYTHON_VERSION = 3.11.9
   - GROQ_API_KEY = your_groq_api_key_here
5. Click **Create Web Service**.
6. Copy your generated backend URL (e.g., https://bordereye-backend.onrender.com).

---

### 2. Deploy the Frontend Web Service
1. In Render Dashboard, click **New +** → **Web Service**.
2. Select the same repository praveen21-tech/sih_border_survelliance.
3. Fill in the following details:
   - **Name:** ordereye-frontend
   - **Region:** Same as backend
   - **Branch:** main
   - **Root Directory:** rontend
   - **Runtime:** Node
   - **Build Command:** 
pm install && npm run build
   - **Start Command:** 
pm run start -- -p 
   - **Plan:** Free
4. Under **Environment Variables**, add:
   - NODE_VERSION = 20.18.0
   - NEXT_PUBLIC_API_URL = https://bordereye-backend.onrender.com *(Replace with your actual backend URL from Step 1)*
5. Click **Create Web Service**.

---

## 🔍 Verification & Health Check

Once both services show **\"Live\"**:
- **Backend Health Check:** Visit https://your-backend.onrender.com/health (should return {\"status\": \"healthy\"}).
- **Interactive API Docs:** Visit https://your-backend.onrender.com/docs (Swagger UI).
- **Surveillance UI:** Visit https://your-frontend.onrender.com to access the full Government-themed C4I surveillance platform.
