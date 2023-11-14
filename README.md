# Fantasy Football Data Provider

Fantasy football is not only fun to play with friends but is a great source of raw statistical data. This Python application is a backend job that aggregates player data Yahoo's fantasy football API into a document driven database; like Cloudant. 

This application consumes a custom database library, [nosql-common](https://github.com/0xCoderJoe/nosql-common), that abstracts the most common database routines we will encounter. It is also a good way to demonstrate competency in building Python packages that can be reused across different applications. 

This was meant to be a fun data transformation project and may provide future data for downstream analytical projects. 

## Prerequisites 

Before running the provider several infrastructure resource need to be configured. More instructions forthcoming. 

## Getting Started

Below are general setup instructions for running the provider as a console Python application. 

1. Clone the repository 

    `git clone git@github.com:0xCoderJoe/fantasy-football-data-provider.git`

2. Open project

    `cd fantasy-football-data-provider`

3. (Recommended) setup a virtual environment

    `python3 -m venv venv`

    `source venv/bin/activate`

4. Copy .env file and set expected environment variables

    `cp env.template .env`

    Open the .env file and populate the respective environment variables with values in the prerequistie step.

5. Run

    `python3 main.py`