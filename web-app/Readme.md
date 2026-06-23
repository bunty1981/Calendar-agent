
To set up a Python web app for testing with the Google Calendar API, you will configure a Google Cloud project, download your OAuth 2.0 credentials, and use the Google API client libraries in a local Python virtual environment to handle user authentication. [1, 2]

Enable the Google Calendar API
1. Navigate to the Google Cloud Console.
2. Create a New Project.
3. Click Enable APIs and Services and search for Google Calendar API. Enable it. [1, 2]

Configure OAuth Consent and Credentials
Because you are building a web application, you will need to authenticate test users securely. [1]
1. Go to the OAuth consent screen in the sidebar. Choose External for the User Type and fill out the required app name and support email.
2. Under Scopes, add .../auth/calendar (or calendar.readonly if you only need to view events).
3. Under Test users, add the email address of the Google account you will use for testing.
4. Go to Credentials, click Create Credentials, and select OAuth client ID.
5. Set the Application type to Web application.
6. Add http://localhost:8000 (or your chosen local port) to the Authorized redirect URIs.
7. Click Create and download the credentials.json file. Save it in your project's root folder. [1, 2, 3, 4, 5]

*** Must use http://localhost as opposed to http:/127.0.0.1 as Google explicitly blocks the //127.0 loops backs but allows //localhost based testing ***