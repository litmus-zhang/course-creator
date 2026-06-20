import os
from typing import Literal

import google.auth
from google.adk.agents import LlmAgent
from google.adk.agents.context import Context
from google.adk.apps import App
from google.adk.events.event import Event
from google.adk.tools.google_search_tool import GoogleSearchTool
from google.adk.workflow import Workflow, node
from google.genai import types
from pydantic import BaseModel, Field

_, project_id = google.auth.default()
os.environ["GOOGLE_CLOUD_PROJECT"] = project_id
os.environ["GOOGLE_CLOUD_LOCATION"] = "global"
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "True"


# 1. Define Schemas
class ResearchReport(BaseModel):
    topic: str = Field(description="The topic of the course.")
    concepts: list[str] = Field(
        description="Core concepts and definitions related to the topic."
    )
    recommended_modules: list[str] = Field(
        description="Syllabus modules or structure suggested."
    )
    learning_outcomes: list[str] = Field(
        description="Key learning outcomes for the course."
    )
    detailed_summary: str = Field(
        description="Detailed research summary from web search."
    )


class CritiqueResult(BaseModel):
    verdict: Literal["APPROVED", "REJECTED"] = Field(
        description="APPROVED if the research is complete, otherwise REJECTED."
    )
    feedback: str = Field(description="Detailed critique and suggestions.")
    missing_aspects: list[str] = Field(
        description="List of specific things missing from the research report."
    )


class LessonOutline(BaseModel):
    lesson_title: str = Field(description="The title of the lesson.")
    lesson_objective: str = Field(description="The objective of the lesson.")
    summary: str = Field(
        description="Summary outline of what is taught in this lesson."
    )


class ModuleOutline(BaseModel):
    module_title: str = Field(description="The title of the module.")
    module_objective: str = Field(description="The objective of the module.")
    lessons: list[LessonOutline] = Field(
        description="List of detailed lessons (at least 3 lessons per module)."
    )


class CourseCurriculum(BaseModel):
    title: str = Field(description="The title of the course.")
    description: str = Field(description="The description of the course.")
    target_audience: str = Field(description="The target audience for the course.")
    prerequisites: str = Field(description="Prerequisites required for the course.")
    learning_objectives: list[str] = Field(description="Course learning objectives.")
    modules: list[ModuleOutline] = Field(description="Module-by-module breakdown.")


# 2. Define specialized Agents
def create_researcher() -> LlmAgent:
    return LlmAgent(
        name="researcher",
        model="gemini-2.5-flash",
        instruction=(
            "You are a Researcher Agent.\n"
            "We are creating a course on the topic: {topic}\n\n"
            "Your task is to gather comprehensive, accurate, and up-to-date information.\n"
            "If this is the first turn, research the topic thoroughly using Google Search.\n"
            "If this is a revision turn (i.e., you see a critique from the judge), "
            "use Google Search to address the judge's feedback and fill in the missing details.\n\n"
            "Generate a structured research report based on your findings."
        ),
        tools=[GoogleSearchTool(bypass_multi_tools_limit=True)],
        output_key="latest_research",
        description="Researches a course topic and returns a detailed research report.",
    )


def create_judge() -> LlmAgent:
    return LlmAgent(
        name="judge",
        model="gemini-2.5-flash",
        instruction=(
            "You are a Judge Agent.\n"
            "Your role is to critique the research report for the topic: {topic}.\n\n"
            "Evaluate the report for:\n"
            "1. Completeness: Does it cover all standard topics for this subject?\n"
            "2. Depth: Is the information detailed enough to build lessons from?\n"
            "3. Accuracy and up-to-date relevancy.\n\n"
            "Provide a clear critique. You must provide a verdict: APPROVED (if ready) "
            "or REJECTED (if there are gaps/missing details)."
        ),
        output_schema=CritiqueResult,
        description="Critiques research reports for quality and completeness.",
    )


def create_content_builder() -> LlmAgent:
    return LlmAgent(
        name="content_builder",
        model="gemini-2.5-flash",
        instruction=(
            "You are a Content Builder Agent.\n"
            "Your role is to turn the approved research report into a structured, "
            "professional, and comprehensive course curriculum.\n\n"
            "Read the approved research report from the state: {latest_research}\n\n"
            "Do not do any more research. Use ONLY the approved research report to build the course curriculum."
        ),
        output_schema=CourseCurriculum,
        description="Generates a structured course curriculum from approved research.",
    )


# 3. Define Workflow Nodes (functions)
@node
def init_state(ctx: Context, node_input: types.Content) -> Event:
    topic = node_input.parts[0].text
    return Event(output=topic, state={"topic": topic, "loop_count": 0})


@node
def get_research_text(ctx: Context, node_input: str) -> Event:
    return Event(output=node_input, state={"latest_research": node_input})


@node
def check_verdict(ctx: Context, node_input: CritiqueResult) -> Event:
    loop_count = ctx.state.get("loop_count", 0) + 1
    # Prevent infinite loop: cap at 3 attempts
    if loop_count >= 3:
        return Event(output=node_input, route="exit", state={"loop_count": loop_count})

    if node_input.verdict == "APPROVED":
        return Event(output=node_input, route="exit", state={"loop_count": loop_count})
    else:
        return Event(
            output=node_input, route="continue", state={"loop_count": loop_count}
        )


# 4. Construct the Workflow
researcher = create_researcher()
judge = create_judge()
content_builder = create_content_builder()

root_agent = Workflow(
    name="course_creator_workflow",
    description="Orchestrates Researcher, Judge, and Content Builder to create structured courses.",
    edges=[
        ("START", init_state),
        (init_state, researcher),
        (researcher, get_research_text),
        (get_research_text, judge),
        (judge, check_verdict),
        (check_verdict, {"continue": researcher, "exit": content_builder}),
    ],
)

app = App(root_agent=root_agent, name="course_creator")
