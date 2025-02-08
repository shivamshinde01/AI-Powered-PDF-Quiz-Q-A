import streamlit as st
import PyPDF2
import google.generativeai as genai
import random
import os

# Set up Google Gemini API Key
os.environ["GOOGLE_API_KEY"] = "AIzaSyBTR3MmV7TiGPznME9B5CODfOkyVb2_sa0"
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Load the Gemini model
model = genai.GenerativeModel("gemini-pro")

# Streamlit UI
st.title("📚 AI-Powered PDF Quiz & Q&A")
st.write("Upload a PDF, generate a quiz, or ask AI about the document!")

# PDF Upload
uploaded_file = st.file_uploader("Upload a PDF file", type=["pdf"])

if uploaded_file is not None:
    try:
        # Extract text from PDF
        pdf_reader = PyPDF2.PdfReader(uploaded_file)
        text = "\n".join([page.extract_text() for page in pdf_reader.pages if page.extract_text()])
        
        if len(text) < 100:
            st.error("PDF does not contain enough text to generate questions.")
        else:
            # Ask AI a question
            user_query = st.text_input("Ask a question based on the document:")
            if st.button("Get Answer"):
                query_prompt = f"Answer this question based on the document:\n{text[:4000]}\n\nQuestion: {user_query}"
                response = model.generate_content(query_prompt)
                st.write(f"**AI Answer:** {response.text}" if response else "No answer available.")
            
            # Define function to generate well-structured multiple-choice questions
            def generate_quiz(text, num_questions=10):
                prompt = f"""
                Generate {num_questions} multiple-choice quiz questions based on this text:
                {text[:4000]}
                
                Format:
                Q1: What is the capital of France?
                A) Berlin
                B) Paris *
                C) Madrid
                
                Ensure:
                - Each question starts with 'Q' followed by a number.
                - 3 distinct answer choices labeled A, B, and C.
                - Correct answer marked with an asterisk (*).
                """
                response = model.generate_content(prompt)
                return response.text.split("\n") if response else []

            # Quiz Functionality
            if "quiz_data" not in st.session_state:
                st.session_state.quiz_data = []
                st.session_state.correct_answers = []
                st.session_state.user_answers = {}

            if st.button("Generate 10-Question Quiz"):
                raw_quiz = generate_quiz(text, 10)
                st.session_state.quiz_data = []
                st.session_state.correct_answers = []
                st.session_state.user_answers = {}

                # Process quiz data to extract questions and answers
                current_question = ""
                options = []
                for line in raw_quiz:
                    line = line.strip()
                    if line.startswith("Q"):
                        if current_question and options:  # Save the previous question
                            st.session_state.quiz_data.append((current_question, options))
                        current_question = line
                        options = []
                    elif line.startswith("A)") or line.startswith("B)") or line.startswith("C)"):
                        options.append(line.replace("*", "").strip())
                        if "*" in line:
                            st.session_state.correct_answers.append(line.replace("*", "").strip())

                if current_question and options:  # Add the last question
                    st.session_state.quiz_data.append((current_question, options))

            if st.session_state.quiz_data:
                st.subheader("📝 Quiz Time!")

                for i, (question, options) in enumerate(st.session_state.quiz_data):
                    correct_option = next((opt for opt in options if opt in st.session_state.correct_answers), None)
                    selected_answer = st.radio(f"**{question}**", options, index=None, key=f"q{i}")
                    st.session_state.user_answers[question] = (selected_answer, correct_option)

                if st.button("Submit Quiz"):
                    score = sum(1 for q, (user_ans, correct_ans) in st.session_state.user_answers.items() if user_ans == correct_ans)
                    st.write(f"### ✅ Your Score: {score} / {len(st.session_state.user_answers)}")
                    st.subheader("📌 Correct Answers:")
                    for question, (_, correct_ans) in st.session_state.user_answers.items():
                        st.write(f"**{question}** → ✅ {correct_ans}")
    
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
