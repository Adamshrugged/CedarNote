This project endeavors to be similar to Obsidian with an easy to use interface for saving notes
organized by folders and tags.

The project is currently setup with minimal security meant more for self hosting on a local network or single computer rather than more broadly.



Installation:
- git clone https://github.com/Adamshrugged/MarkdownProject.git
- cd MarkdownProject/
- python3 -m venv venv
- source venv/bin/activate
- pip install --upgrade pip
- pip install -r requirements.txt


**Running:**
- Just localhost:
   - uvicorn main:app --reload
- Any domain:
   - uvicorn main:app --reload --host 0.0.0.0 --port 8080

You may need to update your firewall rules such as:
- sudo firewall-cmd --add-port=8080/tcp --permanent
- sudo firewall-cmd --reload