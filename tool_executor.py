from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_community.utilities.tavily_search import TavilySearchAPIWrapper
from langchain_core.tools import StructuredTool
from langgraph.prebuilt import ToolNode

from typing import List

from pydantic import BaseModel, Field


class Reflection(BaseModel):
    missing: str = Field(description="Critique of what is missing.")
    superfluous: str = Field(description="Critique of what is superfluous")


class AnswerQuestion(BaseModel):
    """Answer the question."""

    answer: str = Field(description="~250 word detailed answer to the question.")
    reflection: Reflection = Field(description="Your reflection on the initial answer.")
    search_queries: List[str] = Field(
        description="1-3 search queries for researching improvements to address the critique of your current answer."
    )


# Forcing citation in the model encourages grounded responses
class ReviseAnswer(AnswerQuestion):
    """Revise your original answer to your question."""

    references: List[str] = Field(
        description="Citations motivating your updated answer."
    )

search = TavilySearchAPIWrapper()
tavily_tool = TavilySearchResults(api_wrapper=search, max_results=5)


def run_queries(search_queries: list[str], **kwargs):
    """Run the generated queries."""
    return tavily_tool.batch([{"query": query} for query in search_queries])


tool_node = ToolNode(
    [
        StructuredTool.from_function(run_queries, name=AnswerQuestion.__name__),
        StructuredTool.from_function(run_queries, name=ReviseAnswer.__name__),
    ]
)

######
# Update
# ToolInvocation, ToolExecutor have been deprecated after 3.0, it is recommended to replace them with ToolNode
# https://github.com/langchain-ai/langgraph/releases
# https://github.com/langchain-ai/langgraph/issues/3637#issuecomment-2690150631
######

# from collections import defaultdict
# from typing import List
#
# from dotenv import load_dotenv
# from langchain_community.tools import TavilySearchResults
# from langchain_community.utilities.tavily_search import TavilySearchAPIWrapper
# from langchain_core.messages import ToolMessage, BaseMessage, HumanMessage, AIMessage
# from langgraph.prebuilt import ToolInvocation, ToolExecutor
# from chains import parser
# from schemas import AnswerQuestion, Reflection
# import json
# import random
# from chains import parser
#
# load_dotenv()
#
# search = TavilySearchAPIWrapper()
# tavily_tool = TavilySearchResults(api_wrapper=search, max_results=5)
# # we have many invocations of tavily API, we want to run them in parallel, so ToolExecutor.batch() executes all the tool_invocations with a thread pool, it's faster
# tool_executor = ToolExecutor([tavily_tool])
#
# # receive the state (a list of messages), extract tools that needs to be executed from these messages, execute them and return a list of tool messages
# # Tavily Search, search queries we generated in previous step
# def execute_tools(state: List[BaseMessage]) -> List[ToolMessage]:
#     # assume always in the last place before we get to execute tools node
#     tool_invocation: AIMessage = state[-1]
#     # parser is JsonOutputToolParser object in chains.py, taking output from LLM and turn to json
#     parsed_tool_calls = parser.invoke(tool_invocation)
#
#     ids = []
#     # objects of info which tool to use, which function to call
#     tool_invocations = []
#     for parsed_call in parsed_tool_calls:
#         for query in parsed_call["args"]["search_queries"]:
#             tool_invocations.append(ToolInvocation(
#                 tool="tavily_search_results_json",
#                 tool_input=query,
#             ))
#             # to correlate this tool invocation where it came from
#             ids.append(parsed_call["id"])
#     outputs = tool_executor.batch(tool_invocations)
#     # take outputs to transform to a list of tool messages, with one tool message containing 3 searches done for each query, where each search has 5 results
#
#     # map each output to its corresponding ID and tool input
#     outputs_map = defaultdict(dict)
#     for id_, output, invocation in zip(ids, outputs, tool_invocations):
#         outputs_map[id_][invocation.tool_input] = output
#
#     # convert mapped outputs to ToolMessage objects
#     tool_messages = []
#     for id_, mapped_output in outputs_map.items():
#         tool_messages.append(ToolMessage(content=json.dumps(mapped_output), tool_id=id_))
#     return tool_messages
#
#
# if __name__ == "__main__":
#     print("Tool Executor Enter")
#     # dummy state to understand internal
#     human_message = HumanMessage(
#         content="Write about DeepSeek MoE and GRPO, list its impact and applications to future AI research."
#     )
#     answer = AnswerQuestion(
#         answer = "",
#         reflection = Reflection(missing="", superfluous=""),
#         search_queries=[
#             "DeepSeek MoE and GRPO technologies",
#             "AI LLM research advancements",
#             "future AI applications and impacts"
#         ],
#         # auto-generated by LLM vendor, to correlate between 2 execution result with original function calling request
#         id="call_KpYHichFFEmLitHFvFhKy1Ra"
#     )
#
#     raw_res = execute_tools(
#         state = [
#             human_message,
#             AIMessage(
#                 content = "",
#                 tool_calls = [
#                     {
#                         "name": AnswerQuestion.__name__,
#                         "args": answer.dict(),
#                         "id": "call_KpYHichFFEmLitHFvFhKy1Ra",
#                     }
#                 ]
#             )
#         ]
#     )
#     print(raw_res)