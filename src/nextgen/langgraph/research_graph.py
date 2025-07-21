from typing import TypedDict, Annotated, Dict, Any

import pandas as pd

# LangGraph core classes
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite import SqliteSaver

# Local imports
from nextgen.agents.data_scientist_agent import get_data_scientist_agent
from nextgen.agents.statistician_agent import StatisticianAgent
from nextgen.agents.analysis_agent import AnalysisAgent
from nextgen.agents.cross_reference_agent import CrossReferenceAgent

MODEL = "openai"


# -----------------------------------------------------------------------------
# Graph State definition
# -----------------------------------------------------------------------------
class PipelineState(TypedDict, total=False):
    """Shared state that flows through every node in the graph."""

    # Input
    question: str

    # Data retrieval
    sql: str
    raw_df: pd.DataFrame  # Data retrieved by Vanna

    # Statistical analysis
    stat_result: pd.DataFrame  # Output from StatisticianAgent

    # Protein extraction
    analysis_results: list[str]  # List of proteins selected by AnalysisAgent

    # Final answer – markdown string from CrossReferenceAgent
    final_answer: str


# -----------------------------------------------------------------------------
# Graph wrapper class
# -----------------------------------------------------------------------------
class ResearchGraph:
    """A reusable LangGraph pipeline that answers research questions.

    The pipeline consists of the following sequential steps:
      1. Query data via Vanna (LLM-powered SQL generator) → ``raw_df``
      2. Run statistical tests with :class:`StatisticianAgent` → ``stat_result``
      3. Extract key proteins with :class:`AnalysisAgent` → ``analysis_results``
      4. Cross-reference literature with :class:`CrossReferenceAgent` → ``final_answer``
    """

    def __init__(
        self,
        db_path: str | None = None,
        chroma_path: str | None = None,
        checkpoint_path: str | None = None,
    ) -> None:
        """Construct the graph and instantiate all agents.

        Parameters
        ----------
        db_path
            Path to the SQLite database containing omics/tables.
            Defaults to ``database/nextgen.db`` inside the workspace.
        chroma_path
            Directory used by Vanna's ChromaDB vectorstore. Defaults to
            ``database/chroma``.
        checkpoint_path
            SQLite file used by LangGraph to persist state between calls. If
            *None*, a default ``database/langgraph_checkpoints.db`` is created.
        """
        self.db_path = db_path or "database/nextgen.db"
        chroma_path = chroma_path or "database/data_scientist_chroma"
        checkpoint_path = checkpoint_path or "database/langgraph_checkpoints.db"

        # -------------------------- Initialise helper objects -----------------
        # Data retrieval agent (wraps Vanna internally)
        self.data_scientist_agent = get_data_scientist_agent(model=MODEL, chroma_path=chroma_path)

        # Other agents
        self.statistician = StatisticianAgent()
        self.analysis_agent = AnalysisAgent()
        self.cross_ref = CrossReferenceAgent(model=MODEL)

        # --------------------------- Build LangGraph --------------------------
        builder: StateGraph = StateGraph(PipelineState)

        # Each node is a function that receives the current state and returns a
        # dictionary with *updates* to that state. The updates are then merged
        # with the existing state (override semantics for identical keys).
        builder.add_node("query_data", self._query_data)
        builder.add_node("statistics", self._run_statistics)
        builder.add_node("analysis", self._run_analysis)
        builder.add_node("cross_reference", self._run_cross_reference)

        # Wire nodes sequentially
        builder.set_entry_point("query_data")
        builder.add_edge("query_data", "statistics")
        builder.add_edge("statistics", "analysis")
        builder.add_edge("analysis", "cross_reference")
        builder.set_finish_point("cross_reference")

        # Persist intermediate state so we can answer follow-up questions
        # checkpointer = SqliteSaver(checkpoint_path)
        self.graph = builder.compile()

    # ---------------------------------------------------------------------
    # Node implementations
    # ---------------------------------------------------------------------

    # def _chatbot(self, state: PipelineState) -> Dict[str, Any]:
    #     """Chatbot node that uses the OpenAI API to answer questions."""
    #     message = llm.invoke(state["messages"])
        # return {"messages": [message]}
    def _query_data(self, state: PipelineState) -> Dict[str, Any]:
        """Generate SQL with the DataScientistAgent and return the resulting DataFrame."""
        question = state["question"]
        raw_df, sql = self.data_scientist_agent.analyze(question)
        return {"sql": sql, "raw_df": raw_df}

    def _run_statistics(self, state: PipelineState) -> Dict[str, Any]:
        """Run statistical comparison between cancer types."""
        df = state["raw_df"]
        stat_question = (
            "Perform a two-sample t-test for each unique protein comparing "
            "expression levels between the two cancer types"
        )
        result = self.statistician.analyze(stat_question, df)
        return {"stat_result": result}

    def _run_analysis(self, state: PipelineState) -> Dict[str, Any]:
        """Extract list of interesting proteins from statistical result."""
        proteins = self.analysis_agent.analyze(
            state["question"], state["sql"], state["stat_result"]
        )
        return {"analysis_results": proteins}

    def _run_cross_reference(self, state: PipelineState) -> Dict[str, Any]:
        """Validate proteins against literature and craft final answer."""
        answer = self.cross_ref.analyze(state["question"], state["analysis_results"])
        return {"final_answer": answer}

    # ---------------------------------------------------------------------
    # Public API
    # ---------------------------------------------------------------------
    def run(self, question: str) -> str:
        """Execute the graph for *question* and return the final answer."""
        initial_state: PipelineState = {"question": question}
        output_state: PipelineState = self.graph.invoke(initial_state)
        return output_state["final_answer"] 

if __name__ == "__main__":

   # Create an instance of ResearchGraph
   graph = ResearchGraph()

   # Define your research question
   question = "List proteins differentially expressed in breast cancer. You should compare it with all other cancer types."

   # Run the graph with the question
   answer = graph.run(question)

   # Print the answer
   print(answer)