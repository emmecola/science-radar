import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Disable CrewAI tracing to suppress the tracing preference message
os.environ.setdefault("CREWAI_TRACING_ENABLED", "false")

from crewai import Agent, Crew, LLM, Task
from crewai.project import CrewBase, agent, task
from crewai.agents.agent_builder.base_agent import BaseAgent

from science_radar.env_impact import MeliousEnvImpactInterceptor
from science_radar.tools import web_search, generate_illustration

load_dotenv()

_env_impact_interceptor = MeliousEnvImpactInterceptor()

_skills_dir = Path(__file__).resolve().parent.parent.parent / "skills"

# Validate required environment variables
_required_vars = {
    "SCOUT_MODEL": os.getenv("SCOUT_MODEL"),
    "CRITIC_MODEL": os.getenv("CRITIC_MODEL"),
    "CURATOR_MODEL": os.getenv("CURATOR_MODEL"),
    "WRITER_MODEL": os.getenv("WRITER_MODEL"),
    "ILLUSTRATION_MODEL": os.getenv("ILLUSTRATION_MODEL"),
    "MELIOUS_IMAGE_MODEL": os.getenv("MELIOUS_IMAGE_MODEL"),
    "MELIOUS_API_KEY": os.getenv("MELIOUS_API_KEY"),
    "MELIOUS_BASE_URL": os.getenv("MELIOUS_BASE_URL"),
    "NEWSAPI_KEY": os.getenv("NEWSAPI_KEY"),
    "BRAVE_API_KEY": os.getenv("BRAVE_API_KEY"),
}

_missing_vars = [k for k, v in _required_vars.items() if not v]
if _missing_vars:
    print(f"ERROR: Missing required environment variables: {', '.join(_missing_vars)}", file=sys.stderr)
    print("Please set these in your .env file (see .env.example)", file=sys.stderr)
    sys.exit(1)

_melious_base_url = _required_vars["MELIOUS_BASE_URL"]
_melious_api_key = _required_vars["MELIOUS_API_KEY"]

_scout_llm   = LLM(model=_required_vars["SCOUT_MODEL"],   base_url=_melious_base_url, api_key=_melious_api_key, max_retries=5, interceptor=_env_impact_interceptor)
_critic_llm  = LLM(model=_required_vars["CRITIC_MODEL"],  base_url=_melious_base_url, api_key=_melious_api_key, max_retries=5, max_tokens=8192, interceptor=_env_impact_interceptor)
_curator_llm = LLM(model=_required_vars["CURATOR_MODEL"], base_url=_melious_base_url, api_key=_melious_api_key, max_retries=5, interceptor=_env_impact_interceptor)
_writer_llm  = LLM(model=_required_vars["WRITER_MODEL"],  base_url=_melious_base_url, api_key=_melious_api_key, max_retries=5, interceptor=_env_impact_interceptor)
_illustration_llm = LLM(model=_required_vars["ILLUSTRATION_MODEL"], base_url=_melious_base_url, api_key=_melious_api_key, max_retries=5, interceptor=_env_impact_interceptor)


@CrewBase
class ScienceRadar():
    """Science Radar topic intelligence crew"""

    agents: list[BaseAgent]
    tasks: list[Task]

    # --- Agents ---

    @agent
    def source_critic(self) -> Agent:
        return Agent(config=self.agents_config['source_critic'], llm=_scout_llm, skills=[str(_skills_dir / "topic-relevance")], verbose=True)  # type: ignore[index]

    @agent
    def curator_novelty(self) -> Agent:
        return Agent(config=self.agents_config['curator_novelty'], llm=_curator_llm, verbose=True)  # type: ignore[index]

    @agent
    def curator_science(self) -> Agent:
        return Agent(config=self.agents_config['curator_science'], llm=_curator_llm, verbose=True)  # type: ignore[index]

    @agent
    def curator_impact(self) -> Agent:
        return Agent(config=self.agents_config['curator_impact'], llm=_curator_llm, verbose=True)  # type: ignore[index]

    @agent
    def arbiter(self) -> Agent:
        return Agent(config=self.agents_config['arbiter'], llm=_critic_llm, skills=[str(_skills_dir / "editorial-arbitration")], tools=[web_search], verbose=True)  # type: ignore[index]

    @agent
    def writer(self) -> Agent:
        return Agent(config=self.agents_config['writer'], llm=_writer_llm, skills=[str(_skills_dir / "essay-writer")], tools=[web_search], verbose=True)  # type: ignore[index]

    @agent
    def editorial_critic(self) -> Agent:
        return Agent(config=self.agents_config['editorial_critic'], llm=_critic_llm, skills=[str(_skills_dir / "editorial-revision")], tools=[web_search], verbose=True)  # type: ignore[index]

    @agent
    def fact_checker(self) -> Agent:
        return Agent(config=self.agents_config['fact_checker'], llm=_critic_llm, skills=[str(_skills_dir / "fact-checker")], tools=[web_search], verbose=True)  # type: ignore[index]

    @agent
    def illustrator(self) -> Agent:
        return Agent(config=self.agents_config['illustrator'], llm=_illustration_llm, skills=[str(_skills_dir / "image-prompt-writer")], tools=[generate_illustration], verbose=True)  # type: ignore[index]

    # --- Tasks ---

    @task
    def task_source_critique(self) -> Task:
        return Task(config=self.tasks_config['task_source_critique'])  # type: ignore[index]

    @task
    def task_curate_novelty(self) -> Task:
        return Task(config=self.tasks_config['task_curate_novelty'])  # type: ignore[index]

    @task
    def task_curate_science(self) -> Task:
        return Task(config=self.tasks_config['task_curate_science'])  # type: ignore[index]

    @task
    def task_curate_impact(self) -> Task:
        return Task(config=self.tasks_config['task_curate_impact'])  # type: ignore[index]

    @task
    def task_arbitrate(self) -> Task:
        return Task(config=self.tasks_config['task_arbitrate'])  # type: ignore[index]

    @task
    def task_write(self) -> Task:
        return Task(config=self.tasks_config['task_write'])  # type: ignore[index]

    @task
    def task_editorial_critique(self) -> Task:
        return Task(config=self.tasks_config['task_editorial_critique'])  # type: ignore[index]

    @task
    def task_fact_check(self) -> Task:
        return Task(config=self.tasks_config['task_fact_check'])  # type: ignore[index]

    @task
    def task_revise(self) -> Task:
        return Task(config=self.tasks_config['task_revise'])  # type: ignore[index]

    @task
    def task_illustrate(self) -> Task:
        return Task(config=self.tasks_config['task_illustrate'])  # type: ignore[index]

    # --- Crews ---

    def critique_crew(self) -> Crew:
        return Crew(
            agents=[self.source_critic(), self.curator_novelty(), self.curator_science(), self.curator_impact(), self.arbiter()],
            tasks=[self.task_source_critique(), self.task_curate_novelty(), self.task_curate_science(), self.task_curate_impact(), self.task_arbitrate()],
            verbose=True,
        )

    def writing_crew(self) -> Crew:
        return Crew(
            agents=[self.writer()],
            tasks=[self.task_write()],
            verbose=True,
        )

    def critique_writing_crew(self) -> Crew:
        return Crew(
            agents=[self.editorial_critic()],
            tasks=[self.task_editorial_critique()],
            verbose=True,
        )

    def fact_check_crew(self) -> Crew:
        return Crew(
            agents=[self.fact_checker()],
            tasks=[self.task_fact_check()],
            verbose=True,
        )

    def revision_crew(self) -> Crew:
        return Crew(
            agents=[self.writer()],
            tasks=[self.task_revise()],
            verbose=True,
        )

    def illustrate_crew(self) -> Crew:
        return Crew(
            agents=[self.illustrator()],
            tasks=[self.task_illustrate()],
            verbose=True,
        )