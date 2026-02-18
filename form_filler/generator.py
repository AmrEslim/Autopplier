import google.generativeai as genai
from models.profile import UserProfile
from models.form_data import FormField
from config.settings import settings

class Generator:
    def __init__(self, profile: UserProfile):
        self.profile = profile
        if settings.GEMINI_API_KEY:
            genai.configure(api_key=settings.GEMINI_API_KEY)
            self.model = genai.GenerativeModel('gemini-3-pro-preview')
        else:
            self.model = None

    def generate_answer(self, field: FormField) -> str:
        if not self.model:
            return "Error: Gemini API Key not configured."
            
        prompt = self._create_prompt(field)
        
        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            print(f"Error generating answer for {field.name}: {e}")
            return ""

    def _create_prompt(self, field: FormField) -> str:
        base_prompt = f"""
        User Profile:
        {self.profile.model_dump_json(indent=2)}
        
        Task:
        Please provide the value for the following form field for a job application.
        
        Field Label: {field.label}
        Field Name: {field.name}
        Field Type: {field.field_type}
        Field Description: {field.description or "N/A"}
        Required: {field.required}
        Options: {field.options}
        
        Instructions:
        - Provide ONLY the value to be filled in the field.
        - Do not include any explanations or extra text.
        - If the field is a selection (radio/select), strictly match one of the provided options.
        - If the information is not explicitly in the profile, infer a reasonable answer or leave it blank if optional.
        """
        return base_prompt
