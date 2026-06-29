import os
import time
import json
import google.generativeai as genai

class GeminiSummarizer:
    def __init__(self, api_key: str, model_name: str = "gemini-1.5-flash"):
        """
        Initialize the GeminiSummarizer with the provided API key and model name.
        """
        self.model_name = model_name
        genai.configure(api_key=api_key)

    def summarize_pdf(self, pdf_path: str) -> dict:
        """
        Uploads a PDF file to Google's servers, summarizes it using Gemini,
        and returns the structured summary as a dictionary.
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"File not found: {pdf_path}")

        uploaded_file = genai.upload_file(path=pdf_path)
        try:
            file_state = uploaded_file.state.name
            max_attempts = 150  # 150 attempts * 2s = 300s (5 minutes)
            attempts = 0
            while file_state == "PROCESSING":
                if attempts >= max_attempts:
                    raise TimeoutError(f"File processing timed out on Gemini servers for: {pdf_path}")
                time.sleep(2)
                retrieved = genai.get_file(uploaded_file.name)
                file_state = retrieved.state.name
                attempts += 1

            if file_state == "FAILED":
                raise ValueError(f"File processing failed on Gemini servers for: {pdf_path}")

            # Initialize the model with native JSON output enforcement
            model = genai.GenerativeModel(
                self.model_name,
                generation_config={"response_mime_type": "application/json"}
            )
            
            prompt = (
                "You are an insurance company credit risk auditor. Your task is to analyze "
                "the provided financial report/PDF and generate a structured risk assessment report. "
                "You must output ONLY a valid JSON object matching the following structure:\n"
                "{\n"
                "  \"title\": \"Title of the report in Korean\",\n"
                "  \"summary\": [\n"
                "    \"Key risk/point 1 in Korean\",\n"
                "    \"Key risk/point 2 in Korean\",\n"
                "    \"Key risk/point 3 in Korean\"\n"
                "  ],\n"
                "  \"implication\": {\n"
                "    \"upside_risk\": \"Potential positive development / opportunity in Korean\",\n"
                "    \"downside_risk\": \"Potential negative development / risk in Korean\"\n"
                "  },\n"
                "  \"keywords\": [\"keyword1\", \"keyword2\", \"keyword3\"]\n"
                "}\n"
                "Do not include any introductory or concluding text, only the raw JSON."
            )
            
            response = model.generate_content([uploaded_file, prompt])
            
            # Robust JSON parsing
            try:
                return json.loads(response.text)
            except json.JSONDecodeError as e:
                raise ValueError(f"Failed to parse Gemini response as JSON: {e}") from e
            
        finally:
            try:
                genai.delete_file(uploaded_file.name)
            except Exception:
                pass
