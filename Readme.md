
This repo contains code based on the code here:
https://developers.google.com/workspace/calendar/api/quickstart/python

>> conda env create --f calendar-agent-env.yml

To get the test users to work, I had to do the following:

Enabling test users for a Google project is a free process typically used during the development of apps that use Google APIs. By default, new projects are in "Testing" mode, which limits access to a manually defined list of authorized testers.

Steps to Enable Test Users
Access Google Cloud Console: Navigate to the Google Cloud Console and select your specific project from the top dropdown.
Go to OAuth Consent Screen: From the left-side menu, go to APIs & Services > OAuth consent screen.
Configure User Type: If not already set, choose External (standard for testing with any Google account) and click Create.
Add Test Users:
Scroll down to the Test users section.
Click + Add Users.
Enter the email addresses (Gmail or Google Workspace) for your testers and click Save. 


Reference for adding an LLM to create calendar events from free form text
https://github.com/jonathantan12/agent-tan/tree/a0f08d3a15223a243dc1851a537cab091954d5c6/google-calendar-ai-agent
https://medium.com/@jonathantan12/how-to-build-a-python-ai-agent-for-google-calendar-using-singapores-sea-lion-llm-8224e5e016a7
https://medium.com/@swatiagrawal_26/%EF%B8%8F-building-a-simple-ai-tool-to-extract-calendar-events-using-openai-sdk-9c65be613d59