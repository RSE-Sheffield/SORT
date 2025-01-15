import os
import sys
import anthropic

client = anthropic.Anthropic(
    api_key=os.environ.get("ANTHROPIC_API_KEY"),
)

message = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=8192,
    temperature=0,
    system="Create a diff patch containing suggested code changes that can be applied to the files using the patch"
           "tool. The files will be the Python code used to create a Django web application. Each contents of each"
           "file in the input will be preceded by the filename of that file, such as SORT/settings.py\n\nPlease"
           "generate all suggested changes, primarily focussed on code quality, performance, security, and project"
           "organisation.",
    messages=[
        dict(
            role="user",
            content=[
                dict(
                    type="text",
                    # Get input from the command line
                    text=str(sys.stdin),
                )
            ]
        )
    ]
)

print(message.content)
