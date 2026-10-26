# YouTube Subscriber Analyzer
A mobile-friendly personal web application that scans up to 100 unique **top-level** YouTube commenters (newest first) and shows only commenters with publicly accessible subscriptions in a two-column table. Subscription links load in small batches on scroll; commenters without accessible subscriptions are omitted.

## Run on Render
1. Create a **Web Service** on Render and connect this GitHub repository.
2. Choose **Docker** as the runtime. The included Dockerfile starts the FastAPI application on Render's PORT.
3. Set the following **environment variables** (never add their values to GitHub):
   - `APP_USER`: your chosen username (default `admin`)
   - `APP_PASSWORD`: a strong, unique password (**required**)
   - `YOUTUBE_API_KEY`: optional. You can also enter the API key in the web form for each analysis.
4. Deploy, then open the assigned `https://...onrender.com` address on your mobile.
5. Sign in and paste a YouTube video link.

## How it works
Uses YouTube Data API v3 `commentThreads.list` and `subscriptions.list` via your YouTube API key. Only visible subscriptions are returned. Private/restricted subscriptions cannot be retrieved, and some users may have none available. No OpenAI or ChatGPT tokens are used at runtime.

## Notes
- API quota limits, video comments disabled, and Render request timeouts may prevent some analyses.
- The app retrieves up to 100 unique commenters first. Subscription requests are then loaded per commenter, in batches of five as you scroll; a Retry button appears if a request fails. A commenter with an exceptionally large public subscription list may still take time to load.
- HTTP Basic authentication protects the UI and analysis API; use only Render's HTTPS address.
- **Security**: this repository can be public without exposed credentials, but making it private is recommended. Do not commit keys, passwords, or `.env` files.
- You still need to obtain a YouTube Data API key from a Google Cloud project; Google Cloud is not used for hosting.
