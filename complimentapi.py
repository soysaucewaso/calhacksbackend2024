import rag
import calenderclient

import base64
import pickle

from flask import Flask, request, jsonify
from flask_cors import CORS
from google import auth

import os
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import BatchHttpRequest
from google.oauth2 import credentials
import re
app = Flask(__name__)

CORS(app)

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
def getMessageIds():
    # OAuth
    creds = None
    REDIRECT_URI = 'http://localhost:58297/callback'
    TOKENPICKLEPATH = '/Users/sawyer/Documents/token.pickle'
    # get creds
    if os.path.exists(TOKENPICKLEPATH):
        with open(TOKENPICKLEPATH, 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                '/Users/sawyer/Downloads/gmail_credentials.json',scopes= SCOPES)
            creds = flow.run_local_server(port=8080)
            # Save the credentials for the next run
        with open(TOKENPICKLEPATH, 'wb') as token:
            pickle.dump(creds, token)
    service = build('gmail', 'v1', credentials=creds)

    results = service.users().messages().list(userId='me', maxResults=50).execute()
    messages = results.get('messages', [])
    return service, messages

structuredEmails = []
lines = 0
def handle_message_request(request_id, response, exception):
    if exception is not None:
        print(f"Error fetching message with id {request_id}: {exception}")
    else:
        # Process the response (email content)
        payload = response['payload']
        #print(f"Successfully Fetched")
        if 'parts' not in payload:
            return
        headers = {nvpair['name']: nvpair['value'] for nvpair in payload['headers']}
        subject = headers['Subject']
        sender = headers['From']
        date = headers['Date']
        encoded_data = payload['parts'][0]['body']['data']
        data = base64.urlsafe_b64decode(encoded_data).decode('utf-8')
        # cleaned_text = re.sub(r'<[^>]*>(\s*\n)*', '', data)
        # remove empty lines
        cleaned_text = re.sub(r'\n[\s*\n]+', '\n', data)
        # remove links
        cleaned_text = re.sub('[^\s]*://[^\s]*', '', cleaned_text)
        # lines += cleaned_text.count('\n') + 1
        structuredEmails.append(str({'Subject': subject, 'Sender': sender, 'Date': date}))

def getStructuredEmails():
    service, messages = getMessageIds()

    if not messages:
        print("No messages found.")
    else:
        print("Top 50 emails:")
        lines = 0
        i = 0
        jump = 3
        while i < len(messages):
            batch = BatchHttpRequest(callback=handle_message_request,
                                     batch_uri='https://www.googleapis.com/batch/gmail/v1')
            for j in range(i,min(i+jump,len(messages))):
                batch.add(service.users().messages().get(userId='me', id=messages[j]['id'], format='full'))
            batch.execute()
            i += jump
#
# getStructuredEmails()
# emailsstr = '['+",".join(structuredEmails)+']'
# print(emailsstr)
# calenderstr = calenderclient.get_calendar_info()
# inputstr = f"EMAILS: {emailsstr}, CALENDAR: {calenderstr}"


model = rag.rag_model("""
Personal Information:
Name: Alex Johnson
Age: 20
Location: Seattle, WA
Occupation: Full-time Student at the University of Washington
Major: Computer Science
Bio: A dedicated computer science student with a passion for artificial intelligence, game development, and machine learning. Alex loves to explore the latest in technology and enjoys coding challenges, video games, and hiking in the Pacific Northwest.
Google Calendar:
Class Schedule:
CS 324 - Machine Learning: Monday, Wednesday, Friday at 10 AM (in-person)
CS 376 - Game Development: Tuesday and Thursday at 1 PM (in-person)
MATH 307 - Linear Algebra: Monday and Wednesday at 2 PM (online)
PHYS 121 - Physics I: Thursday at 3 PM (in-person lab)
Important Deadlines:
CS 324 Midterm Exam: October 30, 2024, at 9 AM
MATH 307 Assignment 4 Submission: October 22, 2024, by 11:59 PM
Game Development Project Prototype: November 5, 2024, 5 PM
Personal Events:
Weekly hiking trips every Saturday at 8 AM with friends.
Study group for Machine Learning every Wednesday at 7 PM.
Attending the Seattle Tech Meetup on November 2 at 6 PM.
Canvas (Class Scores and Assignments):
CS 324 - Machine Learning:
Current Grade: 88%
Assignments:
Completed Assignment 1: 92%
Completed Assignment 2: 85%
Midterm Review Exam: Upcoming
CS 376 - Game Development:
Current Grade: 93%
Projects:
Prototype Submission: 95%
Group Project Status: In Progress
MATH 307 - Linear Algebra:
Current Grade: 75%
Next Homework Submission: October 22
PHYS 121 - Physics I:
Current Grade: 82%
Upcoming Lab: October 26, 2024
Interests & Hobbies:
Interests:
Deeply interested in artificial intelligence and machine learning, especially computer vision.
Enjoys game development, exploring new game engines like Unity and Unreal Engine, with hopes to build an indie game.
Regularly participates in hackathons, often collaborating on AI-powered applications.
Hobbies:
Video games, especially strategy and puzzle-based games like "Portal" and "Civilization VI."
Hiking and outdoor photography, with a focus on capturing the beauty of the Pacific Northwest.
Coding side projects, such as building personal websites and experimenting with AI models like GPT and LLaMA.
Emails:
School-related Emails:
Received an email from the professor about additional review sessions for Machine Learning midterms.
Notification from the career center regarding upcoming tech internship opportunities and deadlines.
Feedback on the last Linear Algebra assignment with suggestions for improvement.
Personal Emails:
Newsletters from TechCrunch and Hacker News about the latest in AI and tech trends.
Workshop confirmation for “Introduction to Deep Learning” happening on November 10, 2024.
Additional Context:
Goals:
Alex aspires to land a summer internship in AI research or game development, with long-term plans to work at companies like OpenAI, Google DeepMind, or indie game studios.
Working towards developing a personal portfolio that includes AI-based projects and game prototypes to showcase skills.
Wants to explore opportunities to merge interests in AI and gaming, possibly developing AI-driven NPCs for games.
Aiming to improve overall GPA to 3.7 by the end of the academic year to enhance chances for internships and graduate school applications.
Current Projects:
Building a neural network for a class project, focusing on image classification using TensorFlow.
Collaborating with friends on a side game development project, where Alex handles game physics and AI behavior for enemy characters.
Favorite Activities:
Spending weekends hiking, especially around Mount Rainier and Olympic National Park.
Attending local tech meetups and hackathons in Seattle to network with professionals and fellow students in the AI and gaming fields.
Learning new programming languages, currently working through Rust to improve system-level programming skills.

Social Media Activity:
Twitter:
Actively follows AI researchers, game developers, and tech innovators. Regularly retweets content about advancements in AI, especially deep learning, and new developments in gaming engines like Unity and Unreal.
Recently posted about completing a TensorFlow tutorial on neural networks and shared insights from the latest AI conference attended virtually.
Engages in conversations with peers about the ethical implications of AI in gaming and how it can shape future virtual environments.
LinkedIn:
Connected with fellow computer science students, professors, and industry professionals from hackathons and tech events.
Updated profile with a recent project, "AI-Powered Chatbot for Game NPCs," and highlighted participation in a 48-hour game development hackathon, where the team won second place.
Regularly reads articles on career development, AI trends, and industry demands for tech roles.
GitHub:
Frequent commits to personal repositories for machine learning experiments and game development projects.
Created a repository for a class project: a neural network that uses convolutional layers for image recognition.
Recently forked a popular open-source project related to AI-based procedural content generation in games, intending to contribute in the next few weeks.
Google Search History (last month):
“How to optimize neural networks for image classification”
“Game development vs AI: which career path is more in demand?”
“Best laptops for AI programming in 2024”
“Seattle tech internship opportunities for students 2025”
“TensorFlow or PyTorch: which is better for beginners?”
“How to implement enemy AI behavior in Unity”
“Linear algebra study guides for computer science majors”
“Ethical concerns in AI and gaming”
“OpenAI internships application process”
“Top indie game studios to work for as a developer”
Google Drive:
School Projects Folder:
Contains class assignments and collaborative documents for group projects. Recently uploaded the first draft of a game design document for the final project in CS 376 - Game Development.
Uploaded a presentation on machine learning for an upcoming group presentation in CS 324 - Machine Learning.
Personal Folder:
A subfolder labeled "AI Experiments" with Python scripts that implement basic neural networks and AI models, including Alex’s attempts to build a chatbot and experiment with reinforcement learning.
Several unfinished drafts of blog posts on topics like “AI’s Role in Game Development” and “My Experience at Hackathons.”
Portfolio folder with personal projects for showcasing to potential employers, including the AI-based NPC behavior model and other game development projects.
Recent Purchases:
Amazon:
Purchased a new laptop: Dell XPS 15, optimized for programming and AI development.
Bought a couple of books: "Deep Learning with Python" by François Chollet and "Artificial Intelligence and Games" by Georgios N. Yannakakis.
Ordered a new pair of hiking boots for weekend hikes and an external monitor to help with programming setups.
Steam:
Bought the latest game in the strategy genre, "Age of Wonders 4," interested in studying its AI mechanics and gameplay systems.
Pre-ordered a game development tutorial series focused on building AI-driven characters for RPGs.
Career Goals:
Short-Term Goals:
Secure a competitive AI-focused internship for summer 2025, ideally at a company known for pushing the boundaries of AI research or game development.
Complete a personal project—a video game prototype that showcases advanced AI behaviors for non-playable characters (NPCs) and share it as part of an online portfolio.
Continue attending hackathons and tech meetups to build a network in both the AI and gaming industries, with a focus on finding potential mentors or collaborators.
Long-Term Goals:
Alex dreams of combining his passion for AI and gaming by working as an AI researcher in a leading tech company or game studio, focusing on creating intelligent virtual environments and NPCs that adapt to player behavior.
Interested in pursuing graduate studies in AI, either at the University of Washington or applying to schools like Stanford or MIT.
Aspires to eventually launch a startup that leverages AI to create immersive, player-driven worlds in video games, where each player’s experience is uniquely tailored by the game’s AI systems.
Hobbies & Future Plans:
Photography:
Recently started exploring photography as a hobby during weekend hikes. Alex enjoys capturing scenic landscapes and has started posting pictures on social media.
Considering merging photography and game development by working on a side project that simulates real-world environments using photorealistic 3D graphics.
Fitness:
Active in running and aims to complete a half-marathon in the coming year. Uses fitness apps to track progress and enjoys participating in local running events.
Joined a rock climbing group in Seattle to stay active and socialize outside of academic and tech circles.

""")



# ## Additional Context:
# - **Hobbies & Interests:**
#   - Enjoys photography, often sharing images on Instagram and participating in local photography contests.
#   - Actively participates in local community events and volunteering opportunities, focusing on environmental sustainability.
# - **Current Projects:**
#   - Leading a campaign for a new product launch at work, focusing on social media and influencer partnerships.
#   - Working on a personal project to create a travel blog, documenting adventures and experiences.
# - **Goals:**
#   - Aims to travel to at least three new countries in the next year, with plans for Japan and Italy.
#   - Working towards a personal fitness goal of completing a half marathon by the end of 2024.
# - **Favorite Activities:**
#   - Exploring new restaurants and cafes in Seattle, often sharing reviews on social media.
#   - Attending tech meetups and networking events to connect with other professionals in the industry.
# """)

chat_history = []

@app.route('/query',methods=['POST'])
def query():
    inputjson = request.json
    input = inputjson['body']
    output = model.prompt(input, chat_history)

    chat_history.append({"User:" : input, "Assistant": output})
    print(output)
    return jsonify({"Response":output})

@app.route('/affirm',methods=['GET'])
def affirm():
    output = model.get_positive()
    return jsonify({"Response":output})

app.run(debug=True)