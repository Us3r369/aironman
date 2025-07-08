import os
from crewai import Agent, Task, Crew
from langchain_openai import ChatOpenAI
from utils.config import settings

# Set up the OpenAI API key
os.environ["OPENAI_API_KEY"] = settings.OPENAI_API_KEY

# Define the date extractor agent (now using gpt-3.5-turbo)
date_extractor_agent = Agent(
    role="Date Extractor",
    goal="Extract the date from a file's content. The date is in 'YYYY-MM-DD' format.",
    backstory=(
        "You are an expert in parsing JSON files and extracting date information. "
        "You can handle various formats and return a clean, standardized date string."
    ),
    verbose=True,
    allow_delegation=False,
    llm=ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0),
)

def create_date_extraction_task(file_content: str, context: str) -> Task:
    if context == "workout":
        description = (
            "Extract the date from the following workout JSON file content. "
            "Use the date from the timestamp field (e.g., '2025-06-06T14:00:00Z'). "
            "Assume no workout spans two days. Return only the date in 'YYYY-MM-DD' format.\n"
            f"File content:\n{file_content}"
        )
    else:
        description = (
            "Extract the date from the following health metric JSON file content. "
            "Return only the date in 'YYYY-MM-DD' format.\n"
            f"File content:\n{file_content}"
        )
    return Task(
        description=description,
        agent=date_extractor_agent,
        expected_output="A date string in 'YYYY-MM-DD' format.",
    )

def get_date_from_file_content(file_content: str, context: str = "health") -> str:
    """
    Uses a CrewAI agent to extract the date from file content.
    Args:
        file_content (str): The file content to parse (first 50 lines recommended).
        context (str): Either 'health' or 'workout'.
    Returns:
        str: The extracted date in 'YYYY-MM-DD' format.
    """
    task = create_date_extraction_task(file_content, context)
    crew = Crew(
        agents=[date_extractor_agent],
        tasks=[task],
        verbose=True,
    )
    result = crew.kickoff()
    # CrewAI's .kickoff() may return a CrewOutput object; extract the string
    if hasattr(result, 'result'):
        return result.result
    return str(result) 