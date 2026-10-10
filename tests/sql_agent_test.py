from dotenv import load_dotenv

load_dotenv(".env.local", override=True)

from agents.sql_agent import run_sql
print(run_sql("How many active paying customers are there in each subscription plan?"))