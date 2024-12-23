# AI Database Solution (AIDS)
![GitHub License](https://img.shields.io/github/license/NotoriousArnav/aids)
![GitHub commit activity](https://img.shields.io/github/commit-activity/t/NotoriousArnav/aids)
![GitHub contributors](https://img.shields.io/github/contributors/NotoriousArnav/aids)
![GitHub forks](https://img.shields.io/github/forks/NotoriousArnav/aids)
![GitHub language count](https://img.shields.io/github/languages/count/NotoriousArnav/aids)

<img src="mascot.nobg.png" alt="drawing" width="80"/>


AI Database Solution (AIDS) is an AI-driven platform designed to automate SQL database operations. The system interprets natural language inputs to generate and execute SQL queries, improving efficiency and reducing manual effort.

## Features

- **Natural Language Processing**: Allows users to interact with the database using natural language.
- **SQL Code Generation**: Automatically generates SQL queries based on user input.
- **Data Analysis**: Analyzes data returned from SQL queries for better decision-making.
- **Query Safety Assessment**: Checks SQL queries for potential risks before execution.
- **Command-Line and Web Interfaces**: Available for interaction, providing flexibility for different environments.

## Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/NotoriousArnav/aids.git
   cd aids
   ```

2. Install dependencies using Pipenv:
   ```bash
   pipenv install
   ```

3. Set up environment variables. Create a `.env` file in the root directory (copy or rename the '.env copy') and add the following:
   ```bash
   CLOUDFLARE_API_TOKEN="your_token_here"
   CLOUDFLARE_ACCOUNT_ID="your_account_id_here"
   GROQ_API_KEY="your_api_key_here"
   SQLALCHEMY_DB_URL="your_database_url_here"
   ```
   and maybe even these for Easier debugging
   ```bash
   LANGCHAIN_TRACING_V2="your_tracing_version_here"
   LANGCHAIN_ENDPOINT="your_endpoint_here"
   LANGCHAIN_API_KEY="your_api_key_here"
   LANGCHAIN_PROJECT="your_project_here"
   ```

## Running the Application

- To run the application via GUI/Web:
  ```bash
  pipenv run server
  ```

- To run the application via CLI:
  ```bash
  pipenv run cli_agent
  ```

## Project Structure

- `agent_tools/`: Contains the core logic for processing requests.
- `langchain_groq/`: Integration with the Groq AI language model.
- `langgraph/`: Handles the state and memory of the agent.
- `server.py`: The entry point for the web server.
- `cli_agent.py`: The entry point for the command-line interface.

## Requirements

- Python 3.8 or higher
- Pipenv for dependency management

## Material
[![Project Update](https://img.youtube.com/vi/l61xNQLrZ5E/0.jpg)](https://www.youtube.com/watch?v=l61xNQLrZ5E)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
