import asyncio
from dotenv import load_dotenv
import os
import sys

# Add the deepresearch src directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), "third_party/deepresearch/src"))

# Now import the deep_research modules after the path is set up
from deep_research import deep_research, write_final_report
from feedback import generate_feedback

# Load environment variables
load_dotenv()

async def run_research(query, prompt):
    """
    Run deep research with the given query and prompt.
    """
    print("Starting deep research...")
    result = await deep_research(
        query=query,
        breadth=4,
        depth=2
    )
    
    print("Generating final report...")
    report = await write_final_report(
        prompt=prompt,
        learnings=result["learnings"],
        visited_urls=result["visited_urls"]
    )
    
    return report

if __name__ == "__main__":
    # Example usage
    research_query = input("Enter your research query: ")
    report_prompt = input("Enter your report prompt: ")
    
    # Run the async function
    report = asyncio.run(run_research(research_query, report_prompt))
    
    print("\nResearch complete!")
    print("Final Report:", report)