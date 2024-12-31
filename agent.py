from agent_tools import tools, __schema__, run_query_tool
from chat_llm import llm
from langchain.schema.runnable import Runnable
from langchain.schema.runnable.config import RunnableConfig
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from pydantic import SecretStr, BaseModel
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

system_prompt = SystemMessage(content=f"""You are a Database Admin that is Incharge of User's SQL Database.
Make sure that you always stay relevant to the User's Input.

You have provided certain tools and here are the Use cases:
- SQL Coder tool generates Appropriate SQL Queries as per the Prompt and the provided Database schema. In this case, the Database Schema has been already provided, so Basically SQL Knows everything about the Databse, so you can just it. Do not Bother User about the Databse, just straight away ask SQL Coder that question
- Query Runner tool will run your Raw SQL Query and provide response from database.
- Analyze Data tool analyzes the Data Provided to it. It takes in the Database response, your question, the question asked to the previous llm (to generate the SQL Query) and the SQL Query it Generated
- Assess Severity is a Tool to check if a Given SQL Query is safe or not. If the Query has the potential to cause some Damage it will return High Risk.
- FormatMarkdownTable is a Tool to show data in proper Markdown Tables

Note:
- Do run the Generated SQL Query by SQL Coder, don't forget this Step.
- Remember to Show the Data in a Proper Markdown Table for user to look at.
- You have the authority to run any command without the Consent of user, so be responsible and Check the Command before you run.
""")

tools = tools.copy()
tools.append(run_query_tool)
model = llm.bind_tools(tools)

class State(TypedDict):
    # Messages have the type "list". The `add_messages` function
    # in the annotation defines how this state key should be updated
    # (in this case, it appends messages to the list, rather than overwriting them)
    messages: Annotated[List[AnyMessage], add_messages]

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

graph_builder = StateGraph(State)
graph_builder.add_node("chatbot", chatbot)
graph_builder.add_node("tools", tool_node)

graph_builder.add_conditional_edges(
    "chatbot",
    route_tools,
    {"tools": "tools", END: END},
)
graph_builder.add_edge("tools", "chatbot")
graph_builder.add_edge(START, "chatbot")

class Configurable(BaseModel):
    thread_id: str
    session_id: str = ''

class Config(BaseModel):
    configurable: Configurable

config = Config(
            configurable=Configurable(thread_id="1", session_id="abc1")
        ).model_dump()




if __name__ == "__main__":
    memory = MemorySaver()
    graph = graph_builder.compile(checkpointer=memory)
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
