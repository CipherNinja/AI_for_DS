from agent import (
    BasicToolNode,
    State,
    route_tools,
    Config,
    Configurable,
    ToolMessage,
    HumanMessage,
    system_prompt,
    RunnableConfig,
    START, END,
    StateGraph,
    llm
)
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.tools import tool
from agent_tools import (
    analyze_data_tool,
    assess_sql_severity_tool,
    SQLCoder,
    makeMDTable,
    __database_url__
)
from dbops import queryRunner
import chainlit as cl
import asyncio

memory = MemorySaver()
consent: bool = False

@tool("Query Runner")
def run_query_tool(query:str):
    """Run any SQL Query on the Attached Database

    Args:
        query: The SQL Query
    """
    global __database_url__
    global consent
    return queryRunner(
        __database_url__,
        query,
        ask_function=(lambda query: consent)
    )

tools = [
    SQLCoder,
    analyze_data_tool,
    assess_sql_severity_tool,
    makeMDTable,
    run_query_tool
]
model = llm.bind_tools(tools)

def chatbot(state: State):
    return {
        "messages": [
            model.invoke(state["messages"])
        ]
    }

msg = (
    "system",
    f'**IMPORTANT Message: You {"do" if consent else "do not"} have Consent of the User to use Query Runner tool.**'
)

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

graph = graph_builder.compile(checkpointer=memory)

@cl.on_chat_start
async def on_chat_start():
    global msg
    res = await cl.AskActionMessage(
        content="Do you consent AIDS to run SQL Query for this session?",
        actions=[
            cl.Action(name="continue", value="t", label="✅ Continue"),
            cl.Action(name="cancel", value="f", label="❌ Cancel"),
        ],
    ).send()
    if res and res.get("value") == "t":
        global consent
        consent = True
    else:
        pass
    config = Config(
            configurable=Configurable(
                thread_id=cl.context.session.id
            )
        ).model_dump()
    cb = cl.LangchainCallbackHandler()
    final_answer = cl.Message(content="")

    for msg, metadata in graph.stream(
                {
                    "messages": [
                        system_prompt,
                        msg,
                        HumanMessage(content="Hello!")
                    ]
                },
            stream_mode="messages",
            config=RunnableConfig(callbacks=[cb], **config)
        ):
            msg.pretty_print()
            if (
                msg.content
                and not isinstance(msg, HumanMessage)
                and not isinstance(msg, ToolMessage)
            ):
                await final_answer.stream_token(msg.content)

    await final_answer.send()

@cl.on_message
async def on_message(umsg: cl.Message):
    global msg
    config = Config(
        configurable=Configurable(
            thread_id=cl.context.session.id
        )
    ).model_dump()
    cb = cl.LangchainCallbackHandler()
    final_answer = cl.Message(content="")

    if umsg.elements:
        await final_answer.stream_token("The Model currently Does not support File Input")
        await final_answer.send()
        return

    """
    if umsg.content == "Test--++--":
        res = await cl.AskActionMessage(
                content="Pick an action!",
                actions=[
                    cl.Action(name="continue", value=True, label="✅ Continue"),
                    cl.Action(name="cancel", value=False, label="❌ Cancel"),
                ],
            ).send()
        return
    """
    for msg, metadata in graph.stream(
            {
                "messages": [
                    system_prompt,
                    msg,
                    HumanMessage(content=umsg.content)
                ]
            },
        stream_mode="messages",
        config=RunnableConfig(callbacks=[cb], **config)
    ):
        if isinstance(msg, ToolMessage):
            msg.pretty_print()
        if (
            msg.content
            and not isinstance(msg, HumanMessage)
            and not isinstance(msg, ToolMessage)
        ):
            await final_answer.stream_token(msg.content)

    await final_answer.send()
