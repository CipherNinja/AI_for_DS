from agent_tools import tools, __schema__
from langchain_groq import ChatGroq
from langchain.schema.runnable import Runnable
from langchain.schema.runnable.config import RunnableConfig
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from pydantic import SecretStr
import os
import json
import random
from typing import Annotated, List
from typing_extensions import TypedDict
from langgraph.graph.message import AnyMessage, add_messages
from langgraph.graph import END, StateGraph, START
from langgraph.graph.message import MessagesState
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage, ToolMessage
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.tools import tool

print("Module Imported")


opts = {
    'api_key': SecretStr(os.getenv('GROQ_API_KEY', '')),
    "model": "llama3-groq-70b-8192-tool-use-preview"
}


llm = ChatGroq(
    **opts
)

system_prompt = SystemMessage(content=f"""You are a Database Admin that is Incharge of User's SQL Database.
Make sure that you always stay relevant to the User's Input.

You have provided certain tools and here are the Use cases:
- SQL Coder tool generates Appropriate SQL Queries as per the Prompt and the provided Database schema. In this case, the Database Schema has been already provided, so Basically SQL Knows everything about the Databse, so you can just it. Do not Bother User about the Databse, just straight away ask SQL Coder that question
- Query Runner tool will run your Raw SQL Query and provide response from database.
- Analyze Data tool analyzes the Data Provided to it. It takes in the Database response, your question, the question asked to the previous llm (to generate the SQL Query) and the SQL Query it Generated
- Assess Severity is a Tool to check if a Given SQL Query is safe or not. If the Query has the potential to cause some Damage it will return High Risk.

Do run the Generated SQL Query by SQL Coder, don't forget this Step.

""")

tools = tools.copy()
model = llm.bind_tools(tools)

class State(TypedDict):
    # Messages have the type "list". The `add_messages` function
    # in the annotation defines how this state key should be updated
    # (in this case, it appends messages to the list, rather than overwriting them)
    messages: Annotated[List[AnyMessage], add_messages]

graph_builder = StateGraph(State)

def chatbot(state: State):
    return {"messages": [model.invoke(state["messages"])]}


class BasicToolNode:
    """A node that runs the tools requested in the last AIMessage."""

    def __init__(self, tools: list) -> None:
        self.tools_by_name = {tool.name: tool for tool in tools}

    def __call__(self, inputs: dict):
        if messages := inputs.get("messages", []):
            message = messages[-1]
        else:
            raise ValueError("No message found in input")
        outputs = []
        for tool_call in message.tool_calls:
            tool_result = self.tools_by_name[tool_call["name"]].invoke(
                tool_call["args"]
            )
            outputs.append(
                ToolMessage(
                    content=json.dumps(tool_result),
                    name=tool_call["name"],
                    tool_call_id=tool_call["id"],
                )
            )
        return {"messages": outputs}

def route_tools(
    state: State,
):
    """
    Use in the conditional_edge to route to the ToolNode if the last message
    has tool calls. Otherwise, route to the end.
    """
    if isinstance(state, list):
        ai_message = state[-1]
    elif messages := state.get("messages", []):
        ai_message = messages[-1]
    else:
        raise ValueError(f"No messages found in input state to tool_edge: {state}")
    if hasattr(ai_message, "tool_calls") and len(ai_message.tool_calls) > 0:
        return "tools"
    return END

tool_node = BasicToolNode(tools=tools)

graph_builder.add_node("chatbot", chatbot)
graph_builder.add_node("tools", tool_node)

graph_builder.add_conditional_edges(
    "chatbot",
    route_tools,
    # The following dictionary lets you tell the graph to interpret the condition's outputs as a specific node
    # It defaults to the identity function, but if you
    # want to use a node named something else apart from "tools",
    # You can update the value of the dictionary to something else
    # e.g., "tools": "my_tools"
    {"tools": "tools", END: END},
)
# Any time a tool is called, we return to the chatbot to decide the next step
graph_builder.add_edge("tools", "chatbot")
graph_builder.add_edge(START, "chatbot")


config = {"configurable": {"thread_id": "1"}}

if __name__ == "__main__":
    graph = graph_builder.compile(checkpointer=memory)
    memory = MemorySaver()
    events = graph.stream(
        {"messages": [system_prompt, ("user", "Hello")]}, config, stream_mode="values"
    )

    for event in events:
        event["messages"][-1].pretty_print()

    while True:
        try:
            user_input = input("Prompt: ")

            # The config is the **second positional argument** to stream() or invoke()!
            events = graph.stream(
                {"messages": [system_prompt, ("user", user_input)]}, config, stream_mode="values"
            )

            for event in events:
                event["messages"][-1].pretty_print()
        except KeyboardInterrupt:
            break
