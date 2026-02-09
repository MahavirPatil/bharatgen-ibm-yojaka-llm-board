# User Chat Feature Documentation

## Overview

The User Chat feature is an interactive AI tutor interface that helps students learn about specific educational topics. It uses Retrieval-Augmented Generation (RAG) to provide context-aware responses based on NCERT curriculum content.

## How to Access the Chat Feature

There are **two ways** to access the User Chat feature:

### Method 1: Direct Access (Manual Selection)

This is the traditional way where you manually select your preferences and start chatting.

**Steps:**

1. **Navigate to the Chat Page**
   - Open your browser and go to: `http://localhost:8000/user-chat`
   - You'll see a welcome screen with a sidebar on the left

2. **Select Your Subject**
   - Click on one of the four subject buttons: **MATH**, **PHYSICS**, **CHEMISTRY**, or **BIOLOGY**
   - The selected button will be highlighted

3. **Choose Language**
   - From the language dropdown, select either:
     - **English** (en)
     - **हिंदी** (hi)

4. **Select Your Class**
   - Pick your class from the dropdown:
     - Class 10
     - Class 11
     - Class 12

5. **Pick a Chapter**
   - Once you select a class, the chapter dropdown will populate automatically
   - Choose the specific chapter you want to learn about
   - Chapters are organized by topic categories for easy navigation

6. **Start Your Chat Session**
   - Click the **"START CHAT"** button
   - The system will:
     - Fetch relevant educational content from the RAG system
     - Load the context about your selected chapter
     - Display a context badge showing what's loaded
     - Enable the chat input box
   - You'll see a welcome message from the AI tutor

7. **Start Asking Questions**
   - Type your question in the chat input box
   - Press **Enter** or click the **send button** (paper plane icon)
   - The AI will respond based on the loaded educational context
   - You'll see a typing animation (three dots) while the AI is thinking

**Additional Features:**
- **View Context Details**: Click the document icon (📄) in the chat header to see:
  - Filename of the source material
  - Page numbers
  - The full retrieved context in a formatted popup
- **Settings**: Click the gear icon (⚙️) to change the AI model
- **Reset Chat**: Click the refresh icon (🔄) to start a new session
- **Theme Toggle**: Switch between light and dark mode with the moon/sun icon

---

### Method 2: Form Submission (Auto-populated)

This method is designed for seamless integration where another page can submit educational content directly to the chat interface.

**Steps:**

1. **Access the Test Form**
   - Navigate to: `http://localhost:8000/test-form`
   - You'll see a form with pre-filled example data

2. **Fill in the Form** (or use the provided examples)
   - **Subject**: Enter the subject name (e.g., Biology, Physics, Math, Chemistry)
   - **Language**: Enter `en` for English or `hi` for Hindi
   - **Class**: Enter the class level (e.g., 10, 11, 12)
   - **Chapter**: Enter the chapter name (e.g., "Life Processes")
   - **Context**: Paste or type the educational content/context you want the AI to use

3. **Submit the Form**
   - Click the **"Submit to User Chat"** button
   - The form will POST the data to the chat endpoint

4. **Automatic Setup**
   - You'll be taken to the chat page automatically
   - Everything will be **pre-configured** for you:
     - Subject button already selected and highlighted
     - Language dropdown set to your choice
     - Class dropdown set to your class
     - Chapter dropdown showing your selected chapter
     - Context already loaded and ready
     - Chat interface already open and ready to use
   - The AI tutor will greet you with a welcome message

5. **Start Chatting Immediately**
   - No need to click "START CHAT" - it's already done!
   - Just type your question and start learning

**Why Use This Method?**
- Perfect for integration from other pages (like quiz results, study sessions, etc.)
- No manual selection needed - everything is pre-populated
- Great for providing custom context that isn't in the default curriculum
- Useful for teachers who want to provide specific learning materials

---

## Chat Interface Features

### Context Badge
- Shows what content is currently loaded
- Displays: Subject, Class, and Chapter
- Shows the source filename and page numbers (for RAG-retrieved content)
- For form submissions, it shows "From Form Submission"

### Context Details Popup
- Click the document icon to open detailed context view
- Shows:
  - **Document Information**: Filename, page numbers, chunk ID, type
  - **Retrieved Context**: Full formatted content with markdown support
- Tables, headings, lists, and code blocks are properly rendered
- Cleaned up to remove repetitive headers

### Chat Messages
- **User messages**: Appear on the right in blue
- **AI responses**: Appear on the left with proper formatting
- Markdown support includes:
  - Headers and bold/italic text
  - Tables (rendered as proper HTML tables)
  - Code blocks with syntax highlighting
  - Bullet points and numbered lists
  - Mathematical expressions

### Model Selection
- Click the settings icon (⚙️) to choose your AI model:
  - **IBM Granite 3.3 8B Instruct** (default)
  - **Meta Llama 3.2 3B**
  - **Qwen 2.5 7B Instruct**

---

## Technical Details

### How It Works (Behind the Scenes)

**Direct Access Flow:**
1. User selects preferences manually
2. Clicks "START CHAT"
3. Frontend calls `/api/reference` endpoint
4. Backend fetches relevant content from RAG system
5. Context is loaded and displayed
6. User can start chatting

**Form Submission Flow:**
1. Form POSTs data to `/user-chat` endpoint
2. Backend receives: subject, language, class, chapter, and context
3. Backend injects the data into the HTML page as `window.FORM_DATA`
4. Frontend detects the injected data on page load
5. Automatically populates all fields and loads context
6. Chat interface opens immediately - ready to use

**Chat Completion Flow:**
1. User sends a message
2. Frontend prepends the educational context as a system message
3. Calls `/api/chat-completions` endpoint with message history
4. Backend forwards to vLLM-compatible API
5. Response is rendered with markdown formatting

### API Endpoints Used

- **GET `/user-chat`**: Serves the chat interface (direct access)
- **POST `/user-chat`**: Receives form data and serves pre-populated chat interface
- **GET `/test-form`**: Serves the test form for demonstration
- **POST `/api/reference`**: Fetches educational content from RAG system
- **POST `/api/chat-completions`**: Sends messages to AI model and gets responses

---

## Use Cases

### For Students
- **Quick Learning**: Select a chapter and start asking questions immediately
- **Homework Help**: Get explanations on specific topics
- **Exam Prep**: Review concepts interactively

### For Teachers
- **Custom Content**: Use the form submission to provide specific learning materials
- **Guided Sessions**: Pre-configure chat sessions for students
- **Integration**: Link from other educational tools or platforms

### For Developers
- **Seamless Integration**: POST form data from any page to create instant chat sessions
- **Flexible Context**: Provide custom educational content programmatically
- **API Access**: Use the underlying APIs for custom applications

---

## Tips for Best Experience

1. **Be Specific**: Ask clear, focused questions about the chapter topic
2. **Use Context**: The AI has been loaded with specific educational content - ask questions related to that material
3. **Explore Features**: Check out the context details to see what information the AI is working with
4. **Try Different Models**: Different AI models may explain concepts differently - experiment in settings
5. **Reset When Needed**: Start fresh with a new chapter by clicking the reset button

---

## Troubleshooting

**Chapters not loading?**
- Make sure you've selected both a subject AND a class
- Try refreshing the page if dropdowns seem stuck

**Chat not starting?**
- Verify all fields are filled: subject, language, class, and chapter
- Check browser console for error messages

**Context not loading?**
- The reference API might be temporarily unavailable
- Check your internet connection
- Verify the backend services are running

**Form submission not working?**
- Make sure all form fields are filled
- Context field cannot be empty
- Check that the subject/class/chapter match available options

---

## Future Enhancements

- Save chat history for later review
- Export conversations as PDF
- Multi-language support beyond English and Hindi
- Voice input/output capabilities
- Collaborative chat sessions
- Integration with school learning management systems

---

**Need Help?** Contact your system administrator or check the application logs for detailed error messages.
