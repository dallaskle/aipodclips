import asyncio
from dotenv import load_dotenv
import os
import sys

# Add the deepresearch src directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), "third_party/deepresearch/src"))

# Now import the run function after the path is set up
from run import run

# Load environment variables
load_dotenv()

if __name__ == "__main__":
    # Run the main function from run.py
    asyncio.run(run())