from agent import graph, config, system_prompt, RunnableConfig, HumanMessage, memory, ToolMessage
import mesop as me
import mesop.labs as mel


def on_load(e: me.LoadEvent):
  me.set_theme_mode("system")


@me.page(
  security_policy=me.SecurityPolicy(
    allowed_iframe_parents=["https://google.github.io"]
  ),
  path="/",
  title="AIDS",
  on_load=on_load,
)
def page():
  mel.chat(transform, title="AIDS : Artificial Intelligence Database Solution", bot_user="AIDS")


def transform(input: str, history: list[mel.ChatMessage]):
    global config
    events = graph.stream(
        {"messages": [system_prompt, ("user", input)]}, config, stream_mode="messages"
    )
    for event in events:
        msg = event[0]
        if not isinstance(msg, ToolMessage):
            yield msg.content
        else:
            msg.pretty_print()
