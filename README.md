# Chatterbot

# AI Closed-Domain Chatbot for School District

## Project Description
This project involves developing a closed-domain AI chatbot tailored for a school district. The chatbot aims to improve communication and streamline access to district-provided information such as enrollment processes, lunch menus, bus schedules, and academic calendars. By leveraging modern AI technologies, the chatbot will deliver accurate and context-aware responses, reducing administrative workload and enhancing user experience for parents, students, and staff.

---

## Developer Introduction & Setup Instructions

### Dependencies Needed
- **Languages/Frameworks:** Latest version of Java, Python, & React (Javascript) needed
- **Packages:**
    - Python: asyncio, os, json, pandas, crawl4ai, Flask, FastAPI, Django, uvicorn, python-docx, PyMuPDF, pydantic, shutil, logging, openai, elasticsearch
    - Java: elasticsearch, openai

### Usage Instructions

Application is separated into 4 parts: Frontend to display output to user and take in queries, backend to receive queries from user and answer using AI processing with elasticsearch database, elasticsearch database to store webscraped data, and the files used to actually webscrape from the given sites. To use and contribute to this application, developers must look at and understand the function of each of these 4 separate parts to contribute to them.



## Technologies Used

### Natural Language Processing (NLP)
- **GPT-based Models**: For generating human-like responses from stored webscraping data
- **ElasticSearch**: For efficiently storing webscraped data and allowing for complex queries
- **Text Embedding**: OpenAi's text embedding for vector-based semantic search across documents and user queries

### Backend Development
- **Programming Languages**: Python, Java (For ElasticSearch)
- **Frameworks**: Flask, FastAPI, Django, crawl4ai, asyncio
- **Databases**: ElasticSearch (Optimal for webscraping data & queries)
- **Libraries Used**:
    - OpenAi for embeddings and chat completions
    - Elasticsearch for querying the search engine
    - 'python-docx' for parsing uploaded Word documents
    - PyMuPDF ('fitz') for reading and extracting text from PDF files
    - 'pydantic' for request validation
    - 'uvicorn' as server for running FastAPI app
### User Interface
- **Frontend Frameworks**: React.js
- **UI Libraries**: Bootstrap, Material UI
- **Other Features**:
    - 'ReactMarkdown' for rendering formatted bot replies
    - 'webkitSpeechRecognition' for voice-to-text functionality
    - File upload handling for '.txt', '.pdf', and '.docx' using FormData

### Security and Privacy
- **Authentication**: OAuth 2.0, JWT (JSON Web Tokens)
- **Compliance**: FERPA and other privacy standards

### Cloud and Hosting
- **Cloud Platform**: OU-owned server accessed through RDS
- **Hosting Stack**: FastAPI with Elasticsearch for running locally or on cloud VMs

### Testing and Deployment
- **Testing Tools**: Postman (API testing), Pytest (unit testing)
- **Version Control**: Git, Github (pull requests and branch workflows)

---

## Goals

### Primary Goals
- Reduce administrative workload by automating routine queries
- Provide quick, accurate, and context-aware responses to students
- Improve communication between the school district and its community

### Measurable Objectives
- Achieve 90% accuracy in chatbot responses
- Reach 80% user satisfaction within the first 6 months
- Ensure uptime of at least 99% during school operating hours

### Long-Term Vision
- Expand the chatbot's scope to include voice interaction
- Enable deeper personalization by integrating advanced user authentication
- Continuously update the chatbot's knowledge base to reflect changes in district policies and events

---

## Progress Plan

### Phase 1: Planning and Requirements Gathering
- Define use cases and user stories
- Identify stakeholders and their needs
- Establish integration points with existing systems

### Phase 2: Development
- **Month 1-2**: Develop core NLP functionality and intent recognition
- **Month 3**: Build and test backend integrations with district systems
- **Month 4**: Create a responsive user interface for web and mobile platforms

### Phase 3: Testing
- Conduct internal testing with simulated queries
- Perform user testing with parents, students, and staff
- Refine the chatbot based on feedback

### Phase 4: Deployment and Feedback
- Launch the chatbot on selected platforms
- Monitor performance metrics and gather user feedback
- Implement updates and improvements based on usage data

---

## License
This project is licensed under the [MIT License](LICENSE).
