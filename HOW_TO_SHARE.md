# 🌐 How to Share TruthTrace with Anyone

Since your backend is running on your local computer, you can use **Ngrok** to create a public tunnel. This will let anyone in the world use your Vercel website to communicate with your local machine.

---

### Step 1: Install & Set Up Ngrok
1.  **Download Ngrok**: [https://ngrok.com/download](https://ngrok.com/download).
2.  **Sign Up & Get Token**: Create a free account and copy your "Auth Token".
3.  **Configure it**: Open your terminal and run:
    ```bash
    ngrok config add-authtoken YOUR_AUTH_TOKEN_HERE
    ```

---

### Step 2: Start the Tunnel (Live Link)
Whenever you want others to access your backend, run this command:
```bash
ngrok http 8001
```

Look for the **"Forwarding"** URL in your terminal. It will look something like this:
👉 `https://a1b2-c3d4-e5f6.ngrok-free.app`

---

### Step 3: Share the Magical Link
To share your project with anyone, just add **`?api=`** followed by your Ngrok link to your Vercel URL:

👉 **`https://fake-news-detection.vercel.app/?api=https://a1b2-c3d4-e5f6.ngrok-free.app`**

---

### 💡 Why this is great:
- **Zero Configuration**: Your friends don't have to change anything. Just click the link and the app will "Auto-Detect" the backend.
- **Persistent**: TruthTrace will "remember" the last working link. Even if they refresh the page, they'll stay connected!
- **Safe**: You can stop the tunnel anytime by pressing `Ctrl + C` in your terminal.
