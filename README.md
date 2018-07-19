# modesto.io

Hi there!
This is the github repo for my personal website (modesto.io).
It runs on python and is configured so it'll run cleanly if you run it on Heroku with a web dyno command: >> "python run.py -p 5000 runserver"

This is an ongoing project and it is far from finished but if its useful for you, great :)

Requirements are listed in the requirements file so heroku should solve itself.

While the website was initially configured for Heroku, having it run remotely forced me to use PostgreSQL as SQLite doesnt work under the dynamic vm model Heroku uses. This made me rever the project and have it be hosted locally so I could enjoy SQLite.
However, my ISP doesn't really appreciate me having a server running from home. After threats of cutting service I moved it back to Heroku, this repo should reflect the most recent version available there.

You can copy any resources for your own use, but if you do let me know so I can feel proud of my work.