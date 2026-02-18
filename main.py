import sys
import os

# Ensure the current directory is in the path
sys.path.append(os.getcwd())

from models.profile import UserProfile, ContactInfo, Experience, Education
from form_filler.navigator import Navigator
from form_filler.analyzer import Analyzer
from form_filler.generator import Generator

def main():
    # 1. Create a dummy profile
    profile = UserProfile(
        contact_info=ContactInfo(
            first_name="Jane",
            last_name="Doe",
            email="jane.doe@example.com",
            phone="123-456-7890",
            location="Remote"
        ),
        summary="Experienced software engineer with a focus on automation.",
        experience=[
            Experience(
                title="Senior Engineer",
                company="Tech Corp",
                start_date="2020-01",
                description="Built automated testing frameworks.",
                skills_used=["Python", "Playwright", "AWS"]
            )
        ],
        education=[
            Education(
                institution="State University",
                degree="BS Computer Science",
                field_of_study="Computer Science",
                start_date="2016-09",
                end_date="2020-05"
            )
        ],
        skills=["Python", "Selenium", "Playwright", "Docker"],
        preferred_salary=120000,
        remote_only=True
    )

    print("Profile loaded.")

    # 2. Init components
    navigator = Navigator()
    analyzer = Analyzer(navigator.page) # Analyzer needs the page
    generator = Generator(profile)
    
    try:
        # 3. Navigate to a test form
        # Using a public practice form or similar. For now, let's use a dummy local file or a controlled URL if possible.
        # Since I can't easily spin up a local server without more setup, I'll use a simple Google Form or similar if I had one, 
        # but for this script I'll just check if we can start browser and maybe go to example.com to verify wiring.
        print("Starting browser...")
        navigator.start()
        
        url = "https://www.w3schools.com/html/html_forms.asp" # Simple test page
        print(f"Navigating to {url}...")
        navigator.go_to(url)
        
        # 4. Analyze
        print("Analyzing form...")
        # Note: Analyzer initialization in main needs to assign the page properly after navigator starts if not done in init
        # In my current code: Analyzer takes page in init.
        # But navigator.page is None until start() is called.
        # So I need to update analyzer's page or re-init it.
        analyzer.page = navigator.current_page
        
        form_data = analyzer.analyze_form()
        print(f"Found {len(form_data.fields)} fields.")
        
        # 5. Generate and Fill (Simulation)
        for field in form_data.fields:
            print(f"Processing field: {field.name} ({field.field_type})")
            answer = generator.generate_answer(field)
            print(f"  Generated Answer: {answer}")
            
            # TODO: Add filling logic in Navigator or here
            # For now just printing
            
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        print("Closing browser...")
        navigator.close()

if __name__ == "__main__":
    main()
