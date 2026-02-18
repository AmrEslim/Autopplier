from playwright.sync_api import Page
from models.form_data import ApplicationForm, FormField, FieldType
from typing import List

class Analyzer:
    def __init__(self, page: Page):
        self.page = page

    def analyze_form(self) -> ApplicationForm:
        fields = []
        
        # Helper to simplify field extraction
        def add_field(element, type_enum):
            try:
                # Get basic attributes
                elem_id = element.get_attribute("id")
                name = element.get_attribute("name")
                
                # Try to find a label
                label_text = None
                if elem_id:
                    # Check for <label for="id">
                    label_elem = self.page.query_selector(f'label[for="{elem_id}"]')
                    if label_elem:
                        label_text = label_elem.inner_text()
                
                if not label_text:
                     # Check for aria-label or placeholder as fallback
                    label_text = element.get_attribute("aria-label") or element.get_attribute("placeholder") or name
                
                # Determine generic selector
                # Prefer ID, then name, then generating a comprehensive selector if needed
                if elem_id:
                    selector = f"#{elem_id}"
                elif name:
                    selector = f'[name="{name}"]'
                else:
                    # Fallback to a less robust selector if necessary
                    # For now, skipping elements without ID or Name to avoid flakiness, 
                    # or could use path strategies.
                    return 

                required = element.get_attribute("required") is not None
                
                # Check options for select/radio
                options = []
                if type_enum == FieldType.SELECT:
                    option_elems = element.query_selector_all("option")
                    options = [opt.inner_text() for opt in option_elems]

                fields.append(FormField(
                    id=elem_id,
                    name=name,
                    label=label_text.strip() if label_text else None,
                    field_type=type_enum,
                    selector=selector,
                    required=required,
                    options=options
                ))
            except Exception as e:
                print(f"Error processing element: {e}")

        # 1. Text Inputs (and other input types)
        inputs = self.page.query_selector_all("input")
        for inp in inputs:
            input_type = inp.get_attribute("type") or "text"
            if input_type in ["hidden", "submit", "button", "image"]:
                continue
            
            f_type = FieldType.TEXT
            if input_type == "radio":
                f_type = FieldType.RADIO
            elif input_type == "checkbox":
                f_type = FieldType.CHECKBOX
            elif input_type == "file":
                f_type = FieldType.FILE
            elif input_type == "date":
                f_type = FieldType.DATE
            
            add_field(inp, f_type)

        # 2. Textareas
        textareas = self.page.query_selector_all("textarea")
        for ta in textareas:
            add_field(ta, FieldType.TEXTAREA)

        # 3. Selects
        selects = self.page.query_selector_all("select")
        for sel in selects:
            add_field(sel, FieldType.SELECT)

        # 4. Try to find submit button
        submit_selector = None
        submit_btn = self.page.query_selector('button[type="submit"], input[type="submit"]')
        if submit_btn:
            # Generate a selector for the submit button
            # This is a naive approach; might need improvement
            if submit_btn.get_attribute("id"):
                submit_selector = f"#{submit_btn.get_attribute('id')}"
            else:
                 submit_selector = 'button[type="submit"]' # Generic fallback

        return ApplicationForm(url=self.page.url, fields=fields, submit_selector=submit_selector)
