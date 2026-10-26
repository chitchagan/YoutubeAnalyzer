# YouTube Subscriber Analyzer
A mobile-friendly personal web application that scans up to 100 unique **top-level** YouTube commenters (newest first) and shows only commenters with publicly accessible subscriptions in a two-column table. Subscription links load in small batches on scroll; commenters without accessible subscriptions are omitted.

## Run locally on Windows
Install Python 3.10 or newer, then double-click **Start YouTube Analyzer.bat**.
The launcher creates a virtual environment and installs dependencies on first use,
opens http://127.0.0.1:8000 without a login. Enter your YouTube API key in
the web form. Keep the launcher window open while using the app; press Ctrl+C to stop.
If the browser opens before the server is ready, refresh the page after a moment.

## Run on Render
1. Create a **Web Service** on Render and connect this GitHub repository.
2. Choose **Docker** as the runtime. The included Dockerfile starts the FastAPI application on Render's PORT.
3. Set the following **environment variables** (never add their values to GitHub):
   - `YOUTUBE_API_KEY`: optional. You can also enter the API key in the web form for each analysis.
4. Deploy, then open the assigned `https://...onrender.com` address on your mobile.
5. Paste a YouTube video link.

## How it works
Uses YouTube Data API v3 `commentThreads.list` and `subscriptions.list` via your YouTube API key. Only visible subscriptions are returned. Private/restricted subscriptions cannot be retrieved, and some users may have none available. No OpenAI or ChatGPT tokens are used at runtime.

## Notes
- API quota limits, video comments disabled, and Render request timeouts may prevent some analyses.
- The app retrieves up to 100 unique commenters first. Subscription requests are then loaded per commenter, in batches of five as you scroll; a Retry button appears if a request fails. A commenter with an exceptionally large public subscription list may still take time to load.
- The UI and analysis API open without a login.
- **Security**: this repository can be public without exposed credentials, but making it private is recommended. Do not commit keys, passwords, or `.env` files.
- You still need to obtain a YouTube Data API key from a Google Cloud project; Google Cloud is not used for hosting.
