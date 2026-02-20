"""
Cover Letter Generator Tab
──────────────────────────
• Left panel  : Resume paste, specific instructions, company FAQs
• Right panel : AI-generated cover letter output + copy button
• Bottom drawer: Q&A sidebar — ask anything; answers are grounded in the
                 resume + instructions you provided (no hallucination).
"""

import asyncio
import flet as ft
from dotenv import dotenv_values


# ── helpers ──────────────────────────────────────────────────────────────────

def _section_label(text: str) -> ft.Text:
    return ft.Text(text, size=12, weight=ft.FontWeight.W_600, color=ft.Colors.BLUE_300)


def _card(content: ft.Control, padding: int = 16) -> ft.Container:
    return ft.Container(
        content=content,
        padding=ft.padding.all(padding),
        border_radius=12,
        bgcolor=ft.Colors.GREY_900,
        border=ft.border.all(1, ft.Colors.GREY_800),
    )


# ── main component ────────────────────────────────────────────────────────────

class CoverLetterComponent(ft.Column):
    """Full-page Cover Letter generator with an inline Q&A sidebar."""

    def __init__(self):
        super().__init__()
        self.expand = True
        self.spacing = 0
        self._mounted = False

        # ── Resume text area ──────────────────────────────────────────────
        self.resume_field = ft.TextField(
            label="Paste your résumé here",
            multiline=True,
            min_lines=8,
            max_lines=12,
            border_radius=8,
            filled=True,
            hint_text="Copy-paste the full text of your résumé…",
            expand=True,
        )

        # ── Specific instructions ─────────────────────────────────────────
        self.instructions_field = ft.TextField(
            label="Specific instructions / tone / focus",
            multiline=True,
            min_lines=3,
            max_lines=5,
            border_radius=8,
            filled=True,
            hint_text='e.g. "Emphasise my Python skills, keep it under 300 words, formal tone"',
            expand=True,
        )

        # ── Company FAQ ───────────────────────────────────────────────────
        self.faq_field = ft.TextField(
            label="Company FAQs / screening questions (one per line)",
            multiline=True,
            min_lines=4,
            max_lines=8,
            border_radius=8,
            filled=True,
            hint_text=(
                "Why do you want to work here?\n"
                "What is your greatest strength?\n"
                "Describe a challenge you overcame…"
            ),
            expand=True,
        )

        # ── Job description (optional) ────────────────────────────────────
        self.job_desc_field = ft.TextField(
            label="Job description (optional — improves relevance)",
            multiline=True,
            min_lines=3,
            max_lines=6,
            border_radius=8,
            filled=True,
            hint_text="Paste the full job posting text here…",
            expand=True,
        )

        # ── Generate button ───────────────────────────────────────────────
        self.generate_btn = ft.ElevatedButton(
            content=ft.Row(
                [
                    ft.Icon(ft.Icons.AUTO_AWESOME, size=18),
                    ft.Text("Generate Cover Letter", size=14, weight=ft.FontWeight.W_600),
                ],
                tight=True,
                spacing=8,
            ),
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.BLUE_700,
                color=ft.Colors.WHITE,
                shape=ft.RoundedRectangleBorder(radius=8),
                padding=ft.padding.symmetric(horizontal=24, vertical=14),
            ),
            on_click=self._on_generate,
        )

        # ── Output area ───────────────────────────────────────────────────
        self.output_text = ft.Text(
            "Your generated cover letter will appear here…",
            size=13,
            color=ft.Colors.GREY_500,
            selectable=True,
            italic=True,
        )
        self.copy_btn = ft.IconButton(
            icon=ft.Icons.COPY_OUTLINED,
            tooltip="Copy to clipboard",
            icon_color=ft.Colors.BLUE_300,
            on_click=self._copy_output,
            visible=False,
        )
        self.output_spinner = ft.ProgressRing(width=20, height=20, stroke_width=2, visible=False)

        # ── FAQ answers area ──────────────────────────────────────────────
        self.faq_output_text = ft.Text(
            "",
            size=13,
            color=ft.Colors.GREY_300,
            selectable=True,
        )
        self.faq_spinner = ft.ProgressRing(width=20, height=20, stroke_width=2, visible=False)
        self.faq_output_container = ft.Container(
            content=ft.Column(
                [
                    ft.Row([
                        _section_label("📋 FAQ Answers"),
                        ft.Container(expand=True),
                        self.faq_spinner,
                    ]),
                    self.faq_output_text,
                ],
                spacing=8,
            ),
            padding=ft.padding.all(14),
            border_radius=10,
            bgcolor=ft.Colors.with_opacity(0.5, ft.Colors.BLUE_900),
            border=ft.border.all(1, ft.Colors.BLUE_800),
            visible=False,
        )

        # ── Q&A sidebar ───────────────────────────────────────────────────
        self.qa_input = ft.TextField(
            label="Ask a question about yourself…",
            hint_text='e.g. "What is my strongest technical skill?"',
            border_radius=8,
            filled=True,
            expand=True,
            on_submit=self._on_ask,
        )
        self.qa_send_btn = ft.IconButton(
            icon=ft.Icons.SEND_ROUNDED,
            icon_color=ft.Colors.BLUE_400,
            tooltip="Ask",
            on_click=self._on_ask,
        )
        self.qa_spinner = ft.ProgressRing(width=18, height=18, stroke_width=2, visible=False)
        self.qa_messages = ft.ListView(
            expand=True,
            spacing=8,
            auto_scroll=True,
        )

        # ── Build layout ──────────────────────────────────────────────────
        self._build_ui()

    # ── lifecycle ─────────────────────────────────────────────────────────

    def did_mount(self):
        self._mounted = True

    def will_unmount(self):
        self._mounted = False

    # ── UI construction ───────────────────────────────────────────────────

    def _build_ui(self):
        # Left column: inputs
        left_panel = ft.Column(
            [
                _section_label("📄 Your Résumé"),
                self.resume_field,
                ft.Container(height=4),
                _section_label("🎯 Instructions & Tone"),
                self.instructions_field,
                ft.Container(height=4),
                _section_label("❓ Company FAQs / Screening Questions"),
                self.faq_field,
                ft.Container(height=4),
                _section_label("💼 Job Description (optional)"),
                self.job_desc_field,
                ft.Container(height=12),
                ft.Row([self.generate_btn], alignment=ft.MainAxisAlignment.END),
            ],
            spacing=6,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

        # Right column: output + FAQ answers
        right_panel = ft.Column(
            [
                ft.Row([
                    _section_label("✉️ Generated Cover Letter"),
                    ft.Container(expand=True),
                    self.output_spinner,
                    self.copy_btn,
                ]),
                _card(
                    ft.Column(
                        [self.output_text],
                        scroll=ft.ScrollMode.AUTO,
                        expand=True,
                    ),
                    padding=14,
                ),
                ft.Container(height=8),
                self.faq_output_container,
            ],
            spacing=8,
            expand=True,
            scroll=ft.ScrollMode.AUTO,
        )

        # Q&A sidebar
        qa_panel = ft.Container(
            content=ft.Column(
                [
                    ft.Row([
                        ft.Icon(ft.Icons.PSYCHOLOGY_OUTLINED, color=ft.Colors.PURPLE_300, size=18),
                        ft.Text(
                            "Ask About Yourself",
                            size=13,
                            weight=ft.FontWeight.W_600,
                            color=ft.Colors.PURPLE_300,
                        ),
                        ft.Container(expand=True),
                        self.qa_spinner,
                    ]),
                    ft.Text(
                        "Questions are answered strictly from your résumé & instructions — no guessing.",
                        size=11,
                        color=ft.Colors.GREY_500,
                        italic=True,
                    ),
                    ft.Divider(height=1, color=ft.Colors.GREY_800),
                    ft.Container(
                        content=self.qa_messages,
                        expand=True,
                        border=ft.border.all(1, ft.Colors.GREY_800),
                        border_radius=8,
                        padding=8,
                    ),
                    ft.Row(
                        [self.qa_input, self.qa_send_btn],
                        spacing=4,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                ],
                spacing=8,
                expand=True,
            ),
            width=300,
            padding=ft.padding.all(14),
            border_radius=12,
            bgcolor=ft.Colors.with_opacity(0.4, ft.Colors.GREY_900),
            border=ft.border.all(1, ft.Colors.with_opacity(0.6, ft.Colors.PURPLE_900)),
        )

        # Main body: left + right panels
        main_body = ft.Row(
            [
                ft.Container(content=left_panel, expand=True),
                ft.VerticalDivider(width=1, color=ft.Colors.GREY_800),
                ft.Container(content=right_panel, expand=True),
            ],
            expand=True,
            spacing=16,
        )

        # Full layout
        self.controls = [
            # Header
            ft.Row([
                ft.Icon(ft.Icons.DESCRIPTION_OUTLINED, color=ft.Colors.WHITE, size=24),
                ft.Text("Cover Letter Generator", size=22, weight=ft.FontWeight.BOLD),
            ], spacing=10),
            ft.Divider(height=1, color=ft.Colors.OUTLINE),
            # Body + sidebar
            ft.Row(
                [
                    ft.Container(content=main_body, expand=True),
                    ft.VerticalDivider(width=1, color=ft.Colors.GREY_800),
                    qa_panel,
                ],
                expand=True,
                spacing=12,
                vertical_alignment=ft.CrossAxisAlignment.START,
            ),
        ]

    # ── AI helpers ────────────────────────────────────────────────────────

    def _get_api_key(self) -> str:
        env = dotenv_values(".env")
        return env.get("OPENAI_API_KEY", ".....")

    def _build_context(self) -> str:
        """Combine resume + instructions into a grounding context string."""
        resume = self.resume_field.value or ""
        instructions = self.instructions_field.value or ""
        job_desc = self.job_desc_field.value or ""
        parts = []
        if resume.strip():
            parts.append(f"=== RÉSUMÉ ===\n{resume.strip()}")
        if instructions.strip():
            parts.append(f"=== INSTRUCTIONS / TONE ===\n{instructions.strip()}")
        if job_desc.strip():
            parts.append(f"=== JOB DESCRIPTION ===\n{job_desc.strip()}")
        return "\n\n".join(parts)

    async def _call_openai(self, system_prompt: str, user_prompt: str) -> str:
        """Async wrapper around the OpenAI chat completion API."""
        api_key = self._get_api_key()
        if not api_key or api_key.startswith("sk-...") or not api_key.startswith("sk-"):
            return (
                "⚠️  No valid OpenAI API key found.\n"
                "Please add your key in the Settings tab under 'OpenAI API Key'."
            )
        try:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=api_key)
            response = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user",   "content": user_prompt},
                ],
                temperature=0.7,
                max_tokens=1500,
            )
            return response.choices[0].message.content.strip()
        except Exception as exc:
            return f"❌ Error calling OpenAI: {exc}"

    # ── Generate cover letter ─────────────────────────────────────────────

    def _on_generate(self, e):
        self.page.run_task(self._generate_task)

    async def _generate_task(self):
        # Validate
        if not (self.resume_field.value or "").strip():
            self._show_snack("Please paste your résumé first.", error=True)
            return

        # Show spinner, disable button
        self.generate_btn.disabled = True
        self.output_spinner.visible = True
        self.copy_btn.visible = False
        self.output_text.value = "Generating…"
        self.output_text.color = ft.Colors.GREY_500
        self.output_text.italic = True
        self.faq_output_container.visible = False
        self._safe_update()

        context = self._build_context()
        faq_raw = (self.faq_field.value or "").strip()

        system_prompt = (
            "You are an expert career coach and professional writer. "
            "You write compelling, authentic cover letters and answer screening questions "
            "STRICTLY based on the candidate's résumé and instructions provided. "
            "Do NOT invent experience, skills, or facts that are not present in the résumé. "
            "If something is not in the résumé, say so honestly or omit it."
        )

        # Build user prompt
        user_prompt_parts = [
            "Using ONLY the information below, write a professional cover letter.",
            "",
            context,
        ]
        if faq_raw:
            user_prompt_parts += [
                "",
                "=== COMPANY FAQs / SCREENING QUESTIONS ===",
                faq_raw,
                "",
                "After the cover letter, add a section titled '--- FAQ Answers ---' "
                "and answer each question concisely, grounded only in the résumé above.",
            ]

        user_prompt = "\n".join(user_prompt_parts)

        result = await self._call_openai(system_prompt, user_prompt)

        # Split cover letter from FAQ answers if present
        cover_letter_text = result
        faq_answer_text = ""
        if "--- FAQ Answers ---" in result:
            parts = result.split("--- FAQ Answers ---", 1)
            cover_letter_text = parts[0].strip()
            faq_answer_text = parts[1].strip()

        # Update output
        self.output_text.value = cover_letter_text
        self.output_text.color = ft.Colors.WHITE
        self.output_text.italic = False
        self.output_spinner.visible = False
        self.copy_btn.visible = True
        self.generate_btn.disabled = False

        if faq_answer_text:
            self.faq_output_text.value = faq_answer_text
            self.faq_output_container.visible = True

        self._safe_update()

    # ── Copy to clipboard ─────────────────────────────────────────────────

    def _copy_output(self, e):
        text = self.output_text.value or ""
        if text and self.page:
            self.page.set_clipboard(text)
            self._show_snack("✅ Cover letter copied to clipboard!")

    # ── Q&A sidebar ───────────────────────────────────────────────────────

    def _on_ask(self, e):
        question = (self.qa_input.value or "").strip()
        if not question:
            return
        self.page.run_task(self._ask_task, question)

    async def _ask_task(self, question: str):
        # Clear input, show spinner
        self.qa_input.value = ""
        self.qa_spinner.visible = True
        self._safe_update()

        # Add user bubble
        self._add_qa_bubble(question, is_user=True)

        context = self._build_context()
        if not context.strip():
            answer = (
                "⚠️  Please paste your résumé (and optionally instructions) first "
                "so I can answer based on your actual background."
            )
        else:
            system_prompt = (
                "You are a helpful assistant that answers questions about a job candidate "
                "STRICTLY based on the résumé and context provided. "
                "If the answer is not in the provided context, say: "
                "'I cannot find that information in your résumé.' "
                "Do NOT hallucinate or invent any information. "
                "Keep answers concise (2–4 sentences max)."
            )
            user_prompt = (
                f"{context}\n\n"
                f"=== QUESTION ===\n{question}"
            )
            answer = await self._call_openai(system_prompt, user_prompt)

        self.qa_spinner.visible = False
        self._add_qa_bubble(answer, is_user=False)
        self._safe_update()

    def _add_qa_bubble(self, text: str, is_user: bool):
        """Append a chat bubble to the Q&A list."""
        bubble = ft.Container(
            content=ft.Text(
                text,
                size=12,
                color=ft.Colors.WHITE if is_user else ft.Colors.GREY_200,
                selectable=True,
            ),
            padding=ft.padding.symmetric(horizontal=12, vertical=8),
            border_radius=ft.border_radius.only(
                top_left=10,
                top_right=10,
                bottom_left=0 if is_user else 10,
                bottom_right=10 if is_user else 0,
            ),
            bgcolor=ft.Colors.BLUE_800 if is_user else ft.Colors.GREY_800,
            margin=ft.margin.only(
                left=40 if is_user else 0,
                right=0 if is_user else 40,
            ),
        )
        label = ft.Text(
            "You" if is_user else "Assistant",
            size=10,
            color=ft.Colors.GREY_500,
            italic=True,
        )
        row = ft.Column(
            [
                ft.Row(
                    [label],
                    alignment=ft.MainAxisAlignment.END if is_user else ft.MainAxisAlignment.START,
                ),
                bubble,
            ],
            spacing=2,
        )
        self.qa_messages.controls.append(row)
        if self._mounted:
            try:
                self.qa_messages.update()
            except Exception:
                pass

    # ── Utilities ─────────────────────────────────────────────────────────

    def _safe_update(self):
        if self._mounted:
            try:
                self.update()
            except Exception:
                pass

    def _show_snack(self, message: str, error: bool = False):
        if self.page:
            snack = ft.SnackBar(
                content=ft.Text(message),
                bgcolor=ft.Colors.RED_700 if error else ft.Colors.GREEN_700,
                open=True,
            )
            self.page.overlay.append(snack)
            self.page.update()
