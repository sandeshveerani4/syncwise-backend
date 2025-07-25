﻿# SyncWise Ai Backend

At the moment, this project uses LangChain and LangGraph to centralize these tools/workflows:
GitHub, Slack, Jira and Google Calendar.

## Running the Project

1. Clone the repository.
2. Install Python (Python 3.12+ is recommended).
3. Install necessary libraries. This project uses FastAPI, uvicorn, LangChain, among others. You can install them with pip: `pip install -r requirements.txt`.
4. Add your API keys to the `.env` file. Here's the format:

```
GROQ_API_KEY=[GROQ_API_KEY]
DATABASE_URI=[DATABASE_URI]
GOOGLE_CLIENT_ID=[GOOGLE_CLIENT_ID]
GOOGLE_CLIENT_SECRET=[GOOGLE_CLIENT_SECRET]
GITHUB_APP_ID=[GITHUB_APP_ID]
GITHUB_APP_PRIVATE_KEY="[GITHUB_APP_PRIVATE_KEY]"
PINECONE_API_KEY=[PINECONE_KEY]
PINECONE_VECTOR_NAME=[PINECONE_VECTOR_NAME]
OPENAI_API_KEY=[OPEN_API_KEY]
ATTENDEE_WEBHOOK_KEY=[ATTENDEE_WEBHOOK_KEY]
ATTENDEE_APIKEY=[ATTENDEE_APIKEY]
```

5. Start the FastAPI server by running `uvicorn main:app` in the terminal.
6. Access the application by opening your web browser and navigating to `localhost:8000`.

Note: Ensure the appropriate CORS settings if you're not serving the frontend and the API from the same origin.
